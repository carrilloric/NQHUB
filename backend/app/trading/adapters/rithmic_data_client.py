"""
Rithmic Data Client (AUT-345)

Custom NautilusTrader DataClient using async_rithmic for streaming NQ ticks.
Replaces Databento live feed with direct Rithmic/Apex connection via R|Protocol.

Features:
- Real-time NQ tick streaming from Rithmic
- Converts Rithmic ticks to NautilusTrader TradeTick format
- NO automatic reconnection (manual restart required)
- Uses async_rithmic library

References:
- Linear Issue: AUT-345
- Spike: SPIKE-001 GO (2026-03-15)
"""
import os
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from async_rithmic import RithmicClient, SysInfraType
except ImportError:
    # Mock for testing without async_rithmic installed
    RithmicClient = None
    SysInfraType = None

# NautilusTrader imports (will be available when AUT-344 is done)
try:
    from nautilus_trader.live.data_client import LiveDataClient
    from nautilus_trader.config import LiveDataClientConfig
    from nautilus_trader.model.data import TradeTick
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
    from nautilus_trader.model.instruments import Instrument
    from nautilus_trader.model.enums import AggressorSide
    from nautilus_trader.core.datetime import nanos_to_millis, millis_to_nanos
    from nautilus_trader.model.objects import Price, Quantity
except ImportError:
    # Temporary mocks for development
    LiveDataClient = object
    LiveDataClientConfig = object
    TradeTick = None
    InstrumentId = None
    Symbol = None
    Venue = None
    AggressorSide = None
    Price = None
    Quantity = None


logger = logging.getLogger(__name__)


# ============= Configuration =============

@dataclass
class RithmicDataClientConfig:
    """
    Configuration for Rithmic Data Client.

    Attributes:
        rithmic_user: Rithmic username
        rithmic_password: Rithmic password
        rithmic_system: System name (e.g. "Rithmic Test" or "Rithmic 01")
        gateway: Gateway URI (use discover_gateways.py to find)
    """
    rithmic_user: str
    rithmic_password: str
    rithmic_system: str
    gateway: str = "wss://rituz00100.rithmic.com:443"

    @classmethod
    def from_env(cls) -> "RithmicDataClientConfig":
        """Load configuration from environment variables"""
        return cls(
            rithmic_user=os.getenv("RITHMIC_USER", ""),
            rithmic_password=os.getenv("RITHMIC_PASSWORD", ""),
            rithmic_system=os.getenv("RITHMIC_SYSTEM", "Rithmic Test"),
            gateway=os.getenv("RITHMIC_GATEWAY", "wss://rituz00100.rithmic.com:443"),
        )


# ============= NQ Instrument Constants =============

NQ_INSTRUMENT_CONFIG = {
    "tick_size": Decimal("0.25"),
    "tick_value": Decimal("5.00"),  # $5 per tick
    "point_value": Decimal("20.00"),  # $20 per point (4 ticks)
    "symbol": "NQ",
    "exchange": "CME",
    "currency": "USD",
}


# ============= Rithmic Data Client =============

class RithmicDataClient(LiveDataClient):
    """
    NautilusTrader DataClient for Rithmic real-time tick streaming.

    Connects to Rithmic via async_rithmic and converts R|Protocol ticks
    to NautilusTrader TradeTick format for the DataEngine.

    WARNING: NO automatic reconnection. If connection drops, bot must
    be manually restarted.
    """

    def __init__(self, config: RithmicDataClientConfig):
        """
        Initialize Rithmic Data Client.

        Args:
            config: Configuration with Rithmic credentials
        """
        self._config = config
        self._client: Optional[RithmicClient] = None
        self._is_connected = False

        logger.info(
            f"RithmicDataClient initialized for system: {config.rithmic_system}"
        )

    # ============= Connection Management =============

    async def _connect(self):
        """
        Connect to Rithmic via async_rithmic.

        Raises:
            ConnectionError: If connection fails (NO auto-reconnect)
        """
        if RithmicClient is None:
            raise ImportError(
                "async_rithmic is not installed. Install with: pip install async-rithmic"
            )

        try:
            logger.info("Connecting to Rithmic...")

            self._client = RithmicClient(
                user=self._config.rithmic_user,
                password=self._config.rithmic_password,
                system_name=self._config.rithmic_system,
                app_name="NQHUB",
                app_version="2.0",
            )

            # Connect to TICKER_PLANT for market data
            await self._client.connect(SysInfraType.TICKER_PLANT)
            self._is_connected = True

            logger.info("✅ Connected to Rithmic successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Rithmic: {e}")
            raise ConnectionError(f"Rithmic connection failed: {e}")

    async def _disconnect(self):
        """
        Disconnect from Rithmic.

        Note: After disconnect, manual restart is required.
        NO automatic reconnection.
        """
        if self._client is not None:
            try:
                await self._client.disconnect()
                self._is_connected = False
                logger.info("Disconnected from Rithmic")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
        else:
            logger.warning("Disconnect called but client is None")

    # ============= Market Data Subscription =============

    async def _subscribe_trade_ticks(self, instrument_id: str):
        """
        Subscribe to trade ticks for an instrument (e.g. "NQ").

        Streams ticks from Rithmic and converts to NautilusTrader TradeTick.
        Publishes to DataEngine via _handle_trade_tick.

        Args:
            instrument_id: Instrument symbol (e.g. "NQ")

        Raises:
            ConnectionError: If stream is interrupted (NO auto-reconnect)
        """
        if not self._is_connected or self._client is None:
            raise ConnectionError("Not connected to Rithmic. Call _connect first.")

        logger.info(f"Subscribing to {instrument_id} trade ticks...")

        try:
            async for tick in self._client.get_market_data_stream(instrument_id):
                # Convert Rithmic tick to Nautilus TradeTick
                nautilus_tick = self._convert_to_nautilus_tick(tick)

                # Publish to DataEngine
                self._handle_trade_tick(nautilus_tick)

        except Exception as e:
            logger.error(f"Stream interrupted for {instrument_id}: {e}")
            raise ConnectionError(f"Market data stream failed: {e}")

    # ============= Tick Conversion =============

    def _convert_to_nautilus_tick(self, raw_tick: Dict[str, Any]) -> TradeTick:
        """
        Convert raw Rithmic tick to NautilusTrader TradeTick.

        Args:
            raw_tick: Raw tick data from Rithmic with fields:
                - symbol: str (e.g. "NQ")
                - price: float
                - size: int
                - timestamp: int (milliseconds)
                - trade_id: str
                - side: str ("BUY" or "SELL")

        Returns:
            TradeTick: NautilusTrader format tick

        Example raw_tick:
            {
                "symbol": "NQ",
                "price": 16850.25,
                "size": 5,
                "timestamp": 1711825200000,
                "trade_id": "12345",
                "side": "BUY"
            }
        """
        if TradeTick is None:
            raise ImportError("NautilusTrader not installed")

        # Extract fields
        symbol = raw_tick.get("symbol", "NQ")
        price = raw_tick["price"]
        size = raw_tick["size"]
        timestamp_ms = raw_tick["timestamp"]
        trade_id = raw_tick.get("trade_id", "")
        side = raw_tick.get("side", "BUY")

        # Create InstrumentId
        instrument_id = InstrumentId(
            symbol=Symbol(symbol),
            venue=Venue("RITHMIC")
        )

        # Determine aggressor side
        aggressor_side = (
            AggressorSide.BUYER if side == "BUY"
            else AggressorSide.SELLER
        )

        # Convert timestamp to nanoseconds
        ts_init = millis_to_nanos(timestamp_ms)

        # Create TradeTick
        tick = TradeTick(
            instrument_id=instrument_id,
            price=Price.from_str(str(price)),
            size=Quantity.from_int(size),
            aggressor_side=aggressor_side,
            trade_id=trade_id,
            ts_event=ts_init,
            ts_init=ts_init,
        )

        return tick

    # ============= Instrument Configuration =============

    def _get_instrument_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get instrument configuration for a symbol.

        Args:
            symbol: Instrument symbol (e.g. "NQ")

        Returns:
            dict: Instrument configuration with tick_size, tick_value, etc.
        """
        if symbol == "NQ":
            return NQ_INSTRUMENT_CONFIG
        else:
            raise ValueError(f"Unknown instrument: {symbol}")

    # ============= Mock Handler (to be replaced by NautilusTrader) =============

    def _handle_trade_tick(self, tick: TradeTick):
        """
        Handle incoming trade tick.

        This is called for each tick received from Rithmic.
        In production, this publishes to NautilusTrader DataEngine.

        For testing, this is mocked.

        Args:
            tick: NautilusTrader TradeTick
        """
        # In production, this would publish to DataEngine:
        # self._msgbus.publish(DataType.TRADE_TICK, tick)

        # For now, just log
        logger.debug(f"Received tick: {tick.instrument_id} @ {tick.price}")
