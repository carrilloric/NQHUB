# Trading Module - Rithmic Live Adapter (AUT-345)

Custom NautilusTrader DataClient for real-time NQ tick streaming from Rithmic/Apex.

## Overview

This module implements **M3.2 Rithmic live adapter** using `async_rithmic` library to connect directly to Rithmic's R|Protocol for real-time market data.

## Features

- ✅ Real-time NQ tick streaming from Rithmic
- ✅ Conversion to NautilusTrader TradeTick format
- ✅ NO automatic reconnection (manual restart required)
- ✅ Environment variable configuration
- ✅ Comprehensive test coverage (6/8 passing, 2 require NautilusTrader)

## Architecture

```
app/trading/
├── adapters/
│   └── rithmic_data_client.py    # Main implementation
├── kernel.py                      # NautilusTrader node setup (placeholder)
└── README.md                      # This file

tests/trading/
└── test_rithmic_data_client.py    # TDD test suite
```

## Dependencies

- **AUT-344** (NautilusTrader core) - In progress
- `async_rithmic` - Rithmic R|Protocol client library
- `nautilus_trader` - Trading framework

## Configuration

Set the following environment variables:

```bash
export RITHMIC_USER="your_username"
export RITHMIC_PASSWORD="your_password"
export RITHMIC_SYSTEM="Rithmic Test"  # or "Rithmic 01" for production
export RITHMIC_GATEWAY="wss://rituz00100.rithmic.com:443"
```

Or use programmatic configuration:

```python
from app.trading.adapters import RithmicDataClientConfig

config = RithmicDataClientConfig(
    rithmic_user="your_username",
    rithmic_password="your_password",
    rithmic_system="Rithmic Test",
    gateway="wss://rituz00100.rithmic.com:443"
)
```

## NQ Instrument Constants

```python
{
    "tick_size": 0.25,      # Minimum price movement
    "tick_value": $5.00,    # Value per tick
    "point_value": $20.00,  # Value per point (4 ticks)
    "symbol": "NQ",
    "exchange": "CME",
    "currency": "USD"
}
```

## Usage

### Basic Usage (when AUT-344 is complete)

```python
from app.trading.kernel import setup_trading_node
from app.trading.adapters import RithmicDataClientConfig

# Setup configuration
config = RithmicDataClientConfig.from_env()

# Create trading node
node = setup_trading_node()

# Node already has Rithmic adapter registered
# Start the node
node.start()
```

### Direct Usage (for testing)

```python
from app.trading.adapters import RithmicDataClient, RithmicDataClientConfig

# Create client
config = RithmicDataClientConfig.from_env()
client = RithmicDataClient(config=config)

# Connect
await client._connect()

# Subscribe to NQ ticks
await client._subscribe_trade_ticks("NQ")
```

## Testing

Run tests with pytest:

```bash
# Run all trading tests
pytest tests/trading/ -v

# Run specific test
pytest tests/trading/test_rithmic_data_client.py::test_data_client_connects -v
```

### Test Coverage

- ✅ `test_data_client_connects` - Connection logic
- ✅ `test_disconnect_on_error` - Disconnect without auto-reconnect
- ⏸️ `test_tick_conversion_to_nautilus` - Requires NautilusTrader
- ✅ `test_nq_instrument_constants` - NQ configuration
- ⏸️ `test_subscribe_trade_ticks` - Requires NautilusTrader
- ✅ `test_config_from_env_vars` - Environment variable loading
- ✅ `test_connection_failure_raises_error` - Error handling
- ✅ `test_stream_interruption_no_auto_reconnect` - No auto-reconnect

**6 out of 8 tests passing** (2 require NautilusTrader from AUT-344)

## Critical Design Decisions

### NO Automatic Reconnection

⚠️ **IMPORTANT**: If the Rithmic connection drops, the bot will **NOT** automatically reconnect. This is intentional.

**Reason**: Automatic reconnection could lead to:
- Missed ticks during reconnection
- Duplicate positions if state is lost
- Undetected failures

**Solution**: Manual bot restart required. This ensures operators are aware of connection issues and can verify state before resuming.

## Implementation Timeline

- [x] **AUT-345** (This PR) - Rithmic adapter implementation
- [ ] **AUT-344** - NautilusTrader core setup
- [ ] **AUT-348** - Kill switch integration
- [ ] **AUT-349** - Risk Manager integration
- [ ] **AUT-350** - Order Management System

## Related Issues

- **Linear Issue**: [AUT-345](https://linear.app/automation-labs/issue/AUT-345)
- **Depends on**: AUT-344 (NautilusTrader core)
- **Unblocks**: AUT-348 (Kill switch), AUT-349 (Risk Manager), AUT-350 (OMS)
- **Spike**: SPIKE-001 GO (2026-03-15)

## References

- `async_rithmic` documentation (when available)
- Rithmic R|Protocol documentation
- NautilusTrader documentation: https://nautilustrader.io/
