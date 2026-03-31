"""
Execution client for order management.

Interfaces with broker API for order submission, cancellation, and position management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionClient:
    """
    Execution client for broker interactions.

    Handles order submission, cancellation, and position flattening.
    """

    def __init__(self, broker_config: Optional[Dict[str, Any]] = None):
        """
        Initialize execution client.

        Args:
            broker_config: Broker configuration (API keys, endpoints, etc.)
        """
        self.config = broker_config or {}
        self._orders = {}  # Mock order storage
        self._positions = {}  # Mock position storage

    async def submit_order(self, order: Dict[str, Any]) -> str:
        """
        Submit an order to the broker.

        Args:
            order: Order details

        Returns:
            Order ID
        """
        order_id = f"ORD_{datetime.utcnow().timestamp()}"
        self._orders[order_id] = order
        logger.info(f"Order submitted: {order_id}")
        return order_id

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.

        Args:
            order_id: Order identifier

        Returns:
            True if cancelled successfully
        """
        if order_id in self._orders:
            self._orders[order_id]["status"] = "CANCELLED"
            logger.info(f"Order cancelled: {order_id}")
            return True
        return False

    async def flatten_position(
        self,
        symbol: str,
        quantity: float,
        order_type: str = "MARKET",
        time_in_force: str = "IOC"
    ) -> str:
        """
        Flatten a position with a market order.

        Uses IOC (Immediate or Cancel) to prevent hanging orders.

        Args:
            symbol: Trading symbol
            quantity: Position size to flatten
            order_type: Order type (default MARKET)
            time_in_force: Time in force (default IOC)

        Returns:
            Order ID
        """
        flatten_order = {
            "symbol": symbol,
            "quantity": quantity,
            "order_type": order_type,
            "time_in_force": time_in_force,
            "side": "SELL" if quantity > 0 else "BUY",
            "purpose": "FLATTEN",
            "timestamp": datetime.utcnow()
        }

        order_id = await self.submit_order(flatten_order)
        logger.warning(f"Position flatten order submitted: {order_id} for {symbol}")
        return order_id

    async def get_positions(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get open positions for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            List of positions
        """
        # Mock implementation
        return self._positions.get(bot_id, [])

    async def get_pending_orders(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get pending orders for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            List of pending orders
        """
        # Mock implementation
        return [
            order for order_id, order in self._orders.items()
            if order.get("bot_id") == bot_id and order.get("status") == "PENDING"
        ]

    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information from broker.

        Returns:
            Account info including balance, buying power, etc.
        """
        return {
            "account_balance": 25000.0,
            "buying_power": 100000.0,  # With margin
            "currency": "USD",
            "broker": "Rithmic"
        }


# Global execution client instance
_execution_client: Optional[ExecutionClient] = None


def get_execution_client() -> ExecutionClient:
    """Get global execution client instance."""
    global _execution_client
    if _execution_client is None:
        _execution_client = ExecutionClient()
    return _execution_client