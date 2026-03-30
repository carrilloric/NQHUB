# PYRITHMIC vs ASYNC_RITHMIC — Full Comparative Analysis

## 1. Directory Structure Comparison

| pyrithmic | async_rithmic |
|---|---|
| `src/rithmic/` (nested src layout) | `async_rithmic/` (flat package) |
| `interfaces/ticker/ticker_api.py` | `plants/ticker.py` |
| `interfaces/order/order_api.py` | `plants/order.py` |
| `interfaces/history/history_api.py` | `plants/history.py` |
| *(not implemented)* | `plants/pnl.py` |
| `interfaces/base.py` | `plants/base.py` |
| `callbacks/callbacks.py` | Events on `RithmicClient` via `pattern_kit` |
| `config/credentials.py` + `.ini` files | Constructor args directly |
| `tools/pyrithmic_exceptions.py` | `exceptions.py` |
| `tools/meta.py`, `tools/general.py` | `enums.py`, `objects.py` |
| *(none)* | `helpers/connectivity.py` (reconnection) |
| *(none)* | `helpers/concurrency.py` (lock mgmt) |
| *(none)* | `helpers/request_manager.py` (req/resp correlation) |
| `tests/unit/` + `tests/integration/` | `tests/` (4 files) |
| ~40 protobuf files | ~80 protobuf files (more coverage) |

**Key difference:** async_rithmic has dedicated helper modules for reconnection, concurrency, and request tracking — infrastructure pyrithmic lacks entirely.

---

## 2. Architecture Overview

| Aspect | pyrithmic | async_rithmic |
|---|---|---|
| **Concurrency model** | `asyncio` loop on background daemon thread; sync public API via `run_coroutine_threadsafe` | Pure `asyncio`; all public methods are `async` |
| **Entry point** | 3 separate classes: `RithmicTickerApi`, `RithmicOrderApi`, `RithmicHistoryApi` | Single `RithmicClient` with `DelegateMixin` delegating to plant classes |
| **Class hierarchy** | `RithmicBaseApi` (ABC) → 3 subclasses | `BasePlant` → 4 subclasses, orchestrated by `RithmicClient` |
| **Message loop** | Single async loop per API class, inline recv + process | 3 background tasks per plant: recv_loop → Queue → process_loop + heartbeat_loop |
| **Callback system** | `CallbackManager` with `CallbackId` enum registration | `pattern_kit.Event` instances on client (`on_tick`, `on_order_book`, etc.) |
| **Loop sharing** | Explicit `loop=api.loop` parameter | Single event loop; all plants share it by default |
| **Version** | 0.01 | 1.5.9 |
| **Maintenance** | Last commit: 2023-12-21 (stale, 6 open issues) | Last commit: 2026-02-20 (active, 2 open issues, 146 commits) |

### Repository Metadata

| Field | pyrithmic | async_rithmic |
|---|---|---|
| **Author** | Jack Woodhead | Mickael Burguet (rundef) |
| **License** | MIT | MIT |
| **Stars** | ~99 | ~77 |
| **Forks** | ~21 | ~19 |
| **Total Commits** | 19 | 146 |
| **Open Issues** | 6 | 2 |
| **PyPI** | `pyrithmic` | `async_rithmic` |
| **Documentation** | README only | README + Sphinx on ReadTheDocs + CHANGELOG |
| **Python** | >=3.6 (claims) | >=3.10 (tested 3.10–3.13) |

---

## 3. WebSocket Connection Management — Deep Comparison

### 3a. Connection Lifecycle

| Phase | pyrithmic | async_rithmic |
|---|---|---|
| **Open** | `websockets.connect(uri, ssl=ctx, ping_interval=3)` | `websockets.connect(url, ssl=ctx, ping_interval=60, ping_timeout=50)` |
| **Authenticate** | `rithmic_login()` sends `RequestLogin` protobuf, parses response | `_login()` sends `RequestLogin`, stores `heartbeat_interval`, `accounts`, `fcm_id`, `ib_id` |
| **Stream** | Single `_consume_subscription()` coroutine per plant, inline recv+process | `_recv_loop` → `asyncio.Queue` → `_process_loop` (decoupled) |
| **Disconnect** | `rithmic_logout()` + `ws.close()` | `disconnect(timeout=5.0)` — cancels background tasks, sends logout, closes WS |
| **System validation** | None | Ticker connects first, fetches system info, validates `system_name` matches available gateways, then reconnects |

### 3b. Heartbeat / Keepalive

| Aspect | pyrithmic | async_rithmic |
|---|---|---|
| **WS-level ping** | `ping_interval=3` (every 3s) | `ping_interval=60`, `ping_timeout=50` |
| **App-level heartbeat** | Sends `RequestHeartbeat` (template 18) after 5s of recv silence | Dedicated `_heartbeat_loop` task sends at server-negotiated interval (~30s default) |
| **Missed heartbeat** | recv timeout triggers another heartbeat; if `ws.open == False`, raises `WebsocketClosedException` | recv_loop catches `ConnectionClosed*` and triggers reconnection |
| **Heartbeat response** | Consumed and discarded (`continue`) | Consumed and discarded (base.py:513) |

pyrithmic's 3-second WS-level ping is aggressive and potentially wasteful. async_rithmic's 60s interval with 50s timeout is more standard and the dedicated heartbeat loop is cleaner than piggy-backing on recv timeouts.

**pyrithmic heartbeat implementation** (`ticker_api.py:205-236`):
```python
async def _consume_subscription(self):
    await self.send_heartbeat()  # Initial heartbeat on connect
    while connected:
        try:
            msg_buf = await asyncio.wait_for(self.recv_buffer(), timeout=5)
        except asyncio.TimeoutError:
            if self.ws.open:
                await self.send_heartbeat()  # Send heartbeat if no message in 5 seconds
            else:
                raise WebsocketClosedException('Websocket has closed')
```

**async_rithmic heartbeat implementation** (`background_task_mixin.py:96-109`):
```python
async def _heartbeat_loop(self):
    while True:
        await asyncio.sleep(self.heartbeat_interval - 1)
        await self._send_heartbeat()
```

### 3c. Reconnection Strategy

| Aspect | pyrithmic | async_rithmic |
|---|---|---|
| **Auto-reconnect on drop** | **❌ No** — connection death is permanent | **✅ Yes** — `DisconnectionHandler` catches `ConnectionClosed*` |
| **Backoff strategy** | None | Configurable: `constant`, `linear` (default), `exponential` |
| **Default delay** | N/A | 10s base, linear increase, capped at 120s |
| **Jitter** | N/A | Default `(0.5, 2.5)` seconds random jitter |
| **Max retries** | N/A | Default `None` (infinite). Configurable |
| **Re-subscribe after reconnect** | **❌ No** | **✅ Yes** — all plants auto-re-subscribe from `_subscriptions` dict |
| **In-flight order safety** | Lost silently | New orders have `retries=1` (intentional — prevents duplicate fills). Other requests retry up to 3x |
| **Reconnection timeout** | N/A | 5s per connect + 5s per login attempt |
| **Concurrent reconnection prevention** | N/A | `_reconnect_lock` + `_reconnect_event` per plant |

**async_rithmic reconnection core** (`helpers/connectivity.py:38-71`):
```python
async def _try_to_reconnect(plant, attempt):
    settings = plant.client.reconnection_settings
    while True:
        if settings.max_retries is not None and attempt > settings.max_retries:
            return False
        try:
            await asyncio.wait_for(plant._connect(), timeout=5)
            await asyncio.wait_for(plant._login(), timeout=5)
            return True
        except (asyncio.TimeoutError, Exception):
            ...
        attempt += 1
        wait_time = plant.client.reconnection_settings.get_delay(attempt)
        await asyncio.sleep(wait_time)
```

**async_rithmic backoff calculation** (`objects.py:21-42`):
```python
@dataclass
class ReconnectionSettings:
    max_retries: int | None = None          # None = infinite
    backoff_type: Literal["constant", "linear", "exponential"] = "linear"
    interval: float = 10
    max_delay: float = None
    jitter_range: tuple = None
    def get_delay(self, attempt: int) -> float:
        # constant: interval
        # linear: interval * attempt
        # exponential: interval * 2^(attempt-1)
        # + random jitter + max_delay cap
```

### 3d. Error Propagation

| Aspect | pyrithmic | async_rithmic |
|---|---|---|
| **WS disconnection** | Ticker: `WebsocketClosedException` (silently dies on background thread). Order: `except Exception as e: print(e)` — **swallowed**. History: generic `Exception` | Caught by `DisconnectionHandler` → triggers reconnect. If max retries exceeded: `RuntimeError("Unable to reconnect")` |
| **Rithmic protocol errors** | Not systematically checked | `RithmicErrorResponse` raised with full error dict. `rp_code == '7'` treated as "no data" (returns `[]`) |
| **Forced logout (template 77)** | Not handled | Logged as warning; reconnection triggers automatically |
| **Lock timeout** | N/A | Full stack trace logged for deadlock diagnosis |
| **Visibility to caller** | Exceptions silently lost on background thread | Exceptions propagate to `await` caller. Events fire for connection state |

> **⚠️ CRITICAL:** pyrithmic's Order API literally does `print(e)` and continues — a catastrophic silent failure mode for a trading system. Orders can be lost with zero indication to the caller.

### 3e. Multi-Plant Connection Management

| Aspect | pyrithmic | async_rithmic |
|---|---|---|
| **Architecture** | Each plant is an independent class instance with its own WS | Each plant is a child object of `RithmicClient`, own WS |
| **Loop sharing** | Explicit `loop=api.loop` parameter | Automatic — all plants share the client's event loop |
| **Independent failure** | Yes — each plant's WS is independent | Yes — each plant reconnects independently |
| **Coordinated connect** | Manual — user instantiates each API separately | `client.connect()` connects all plants sequentially (0.1s gap) |
| **Coordinated disconnect** | Manual — user calls `disconnect_and_logout()` on each | `client.disconnect(timeout=5.0)` handles all plants |
| **Selective plants** | User chooses which classes to instantiate | `client.connect(plants=[SysInfraType.TICKER_PLANT, ...])` |
| **Connection events** | None | `client.on_connected` / `client.on_disconnected` events |

### 3f. Production Readiness Assessment

For a 24/5 system (NQHUB) on Apex futures with potential Chicago gateway blips:

| Criterion | pyrithmic | async_rithmic |
|---|---|---|
| **Gateway blip survival** | **Fatal.** No reconnection. Requires full process restart or manual reconnection code | **Survives.** Auto-reconnect with backoff, re-subscribe, resume streaming |
| **Custom resilience needed** | Extensive: reconnection wrapper, subscription tracking, backoff, lock management, error propagation | Minimal: configure `ReconnectionSettings`, register event handlers |
| **Silent failure risk** | **High** — order plant swallows exceptions via `print(e)` | **Low** — errors propagate as exceptions or fire events |
| **24/5 stability** | Not viable without significant wrapper code | Production-ready with default settings |

---

## 4. Feature Matrix

| Feature | pyrithmic | async_rithmic |
|---|---|---|
| TICKER_PLANT (live tick streaming) | ✅ | ✅ |
| HISTORY_PLANT (historical data) | ✅ | ✅ |
| ORDER_PLANT (order placement) | ✅ | ✅ |
| PNL_PLANT (P&L monitoring) | ❌ | ✅ |
| L2 / Order Book streaming | ❌ (protobuf exists, not wired) | ✅ |
| Market Depth (Depth by Order) | ❌ | ✅ |
| BBO (Best Bid/Offer) streaming | ❌ (protobuf exists, not wired) | ✅ |
| Multi-account support | ⚠️ (uses `primary_account_id` only) | ✅ (`account_id` param on orders) |
| Automatic reconnection | ❌ | ✅ |
| Heartbeat / keepalive | ✅ (recv-timeout based) | ✅ (dedicated loop, server-negotiated interval) |
| Re-subscription after reconnect | ❌ | ✅ |
| Configurable backoff/retry | ❌ | ✅ (constant/linear/exponential + jitter) |
| Callback system | ✅ (`CallbackManager`) | ✅ (`pattern_kit.Event`) |
| Python 3.11+ compatibility | ⚠️ (claims 3.6+, untested on modern) | ✅ (tested 3.10–3.13) |
| Async-native architecture | ❌ (sync API, threading) | ✅ (pure asyncio) |
| System name validation on login | ❌ | ✅ |
| Connection state tracking | ⚠️ (`ws.open` only) | ⚠️ (`ws.state == OPEN` only, no state machine) |
| Error handling quality | ❌ (swallowed, silent) | ✅ (propagated, typed exceptions) |
| Request/response correlation | ❌ | ✅ (`RequestManager`) |
| Symbol search | ❌ | ✅ |
| Time bar streaming (live) | ❌ | ✅ |
| Bracket order support | ✅ | ✅ |
| Order modification | ✅ | ✅ |
| Exit position helper | ❌ | ✅ |
| Account RMS info | ❌ | ✅ |
| StatusManager (order state persistence) | ✅ (pickle serializable) | ❌ (no equivalent) |

---

## 5. API Design Comparison

### Connecting and Authenticating

**pyrithmic:**
```python
from rithmic import RithmicTickerApi, RithmicOrderApi, RithmicEnvironment

ticker_api = RithmicTickerApi(env=RithmicEnvironment.RITHMIC_PAPER_TRADING)
# auto_connect=True by default — connects on construction
order_api = RithmicOrderApi(
    env=RithmicEnvironment.RITHMIC_PAPER_TRADING,
    loop=ticker_api.loop
)
# Requires RITHMIC_CREDENTIALS_PATH env var pointing to .ini files
```

**async_rithmic:**
```python
from async_rithmic import RithmicClient

client = RithmicClient(
    user="myuser", password="mypass",
    system_name="Rithmic Test", app_name="myapp",
    app_version="1.0", url="wss://rituz00100.rithmic.com:443"
)
await client.connect()
```

### Streaming Live Ticks with a Callback

**pyrithmic:**
```python
stream = ticker_api.stream_market_data("NQH4", "CME")
# Polling:
df = stream.tick_dataframe
# Or callback:
cb = CallbackManager()
cb.register_callback(CallbackId.TICKER_LAST_TRADE, my_handler)
ticker_api.add_callback_manager(cb)
```

**async_rithmic:**
```python
client.on_tick += my_handler  # async def my_handler(data): ...
await client.subscribe_to_market_data("NQH4", "CME", DataType.LAST_TRADE)
```

### Placing a Market Order with account_id

**pyrithmic:**
```python
order = order_api.submit_market_order(
    order_id="my_order_1", security_code="NQH4",
    exchange_code="CME", quantity=1, is_buy=True
)
# ⚠️ No account_id parameter — uses primary_account_id only
```

**async_rithmic:**
```python
await client.submit_order(
    order_id="my_order_1", symbol="NQH4", exchange="CME",
    qty=1, transaction_type=TransactionType.BUY,
    order_type=OrderType.MARKET, account_id="APEX-12345-01"
)
```

### Downloading Historical Data

**pyrithmic:**
```python
download = history_api.download_historical_tick_data(
    "NQH4", "CME", start_time=dt1, end_time=dt2
)
while not download.is_complete:
    time.sleep(1)
df = download.dataframe
```

**async_rithmic:**
```python
ticks = await client.get_historical_tick_data(
    "NQH4", "CME", start_time=dt1, end_time=dt2, wait=True
)
# Returns list of dicts directly; or use wait=False + on_historical_tick event
```

### Handling a Disconnection Event

**pyrithmic:**
```python
# No built-in mechanism. Must wrap in try/except at application level.
# Order plant silently swallows errors. No event fired.
```

**async_rithmic:**
```python
client.on_disconnected += my_disconnect_handler
# Automatic reconnection with configurable ReconnectionSettings
# All subscriptions restored automatically
```

---

## 6. Dependencies

| pyrithmic | async_rithmic |
|---|---|
| `numpy` | *(not used)* |
| `pandas` | *(not used)* |
| `websockets` (any version) | `websockets` >=11.0, <15.0 |
| `protobuf==3.20.3` (pinned, old) | `protobuf` >=4.25.4, <5 |
| `pytz` (used but **not declared**) | `pytz` >=2022.5 |
| *(not used)* | `tzlocal` >=5.2 |
| *(not used)* | `pattern_kit` >=2.0.0 |

**async_rithmic** has fewer heavy deps (no numpy/pandas) and uses modern protobuf v4. pyrithmic pins to protobuf 3.20.3, which is outdated and may conflict with other libraries. async_rithmic adds `pattern_kit` (lightweight event system) and `tzlocal` as trade-offs.

---

## 7. Code Quality

| Aspect | pyrithmic | async_rithmic |
|---|---|---|
| **Test coverage** | 5 unit + 3 integration test files | 4 test files with `pytest-asyncio` |
| **Test quality** | Basic; integration tests need live connection | Mocked WebSocket tests for reconnection, backoff, deadlock |
| **Documentation** | README with examples | README + Sphinx docs on ReadTheDocs + CHANGELOG |
| **Type hints** | Partial (method signatures) | More extensive, uses `\|` union syntax (3.10+) |
| **Maintenance** | Stale (Dec 2023, 6 open issues, 19 commits) | Active (Feb 2026, 2 open issues, 146 commits) |
| **Code organization** | Reasonable but monolithic API files | Clean separation: helpers, plants, objects |
| **Logging** | Custom logger, minimal | Structured logging with context |

---

## 8. Explicit Improvements in async_rithmic over pyrithmic

1. **Automatic reconnection** with configurable backoff (constant/linear/exponential + jitter + max retries)
2. **Automatic re-subscription** of all data streams after reconnect
3. **PNL plant** implemented (missing in pyrithmic)
4. **BBO streaming** implemented (protobuf existed in pyrithmic but not wired)
5. **Order Book / Market Depth** streaming
6. **Multi-account support** — `account_id` parameter on order submission
7. **Pure async API** — no threading, no `run_coroutine_threadsafe` hacks
8. **Request/response correlation** via `RequestManager` — handles interleaved concurrent requests
9. **Lock-based concurrency protection** with deadlock detection and timeout logging
10. **Concurrent reconnection prevention** — `_reconnect_lock` ensures only one reconnection per plant
11. **Decoupled recv/process pipeline** — `asyncio.Queue` between recv_loop and process_loop
12. **System name validation** on login — prevents connecting to wrong gateway
13. **Proper error propagation** — typed exceptions, no silent swallowing
14. **No heavy dependencies** — no numpy/pandas requirement
15. **Modern protobuf** (v4 vs pinned v3.20.3)
16. **Configurable retry** per request type (orders intentionally limited to prevent duplicate fills)
17. **`exit_position()` helper** — close all positions with one call
18. **Symbol search** functionality
19. **Time bar streaming** (live bar updates)
20. **Selective plant connection** — connect only the plants you need
21. **Connection/disconnection events** — `on_connected`, `on_disconnected`

---

## 9. Limitations of Each

### pyrithmic

- **No reconnection** — fatal for any production use
- **No PNL plant**
- **No BBO/L2/depth** despite having the protobufs
- **Silent error swallowing** in order plant (`print(e)`)
- **Single-account only** — no `account_id` parameter
- **Stale/unmaintained** — last commit Dec 2023
- **Missing `pytz` dependency** declaration
- **Pinned to protobuf 3.20.3** — conflicts with modern stacks
- **Threading model** — `asyncio` on daemon thread with sync facade; not truly async
- **No request/response correlation** — fire-and-forget protobuf sends
- **Unbounded message accumulation** — `sent_messages`/`recv_messages` lists grow forever (memory leak)

### async_rithmic

- **No order state persistence** — pyrithmic's `StatusManager` pickle serialization has no equivalent
- **No DataFrame integration** — returns dicts, not pandas DataFrames (trade-off: lighter deps)
- **No connection state machine** — only `is_connected` bool, no connecting/disconnecting states
- **Python 3.10+** minimum — cannot run on older Python
- **Depends on `pattern_kit`** — third-party event library (small but another dependency)
- **No explicit reconnection event per plant** — `on_disconnected`/`on_connected` fire, but no per-plant granularity exposed to user

---

## 10. Final Verdict for NQHUB

### Recommendation: **async_rithmic** — decisively

The choice is unambiguous for NQHUB's requirements:

| NQHUB Requirement | pyrithmic | async_rithmic |
|---|---|---|
| Real-time NQ tick streaming | ✅ | ✅ |
| Multi-account (eval vs paper via account_id) | ❌ | ✅ |
| Order execution for DQN agent | ✅ (but silently swallows errors) | ✅ (proper error propagation) |
| Historical tick download to TimescaleDB | ✅ | ✅ |
| 24/5 operation surviving network blips | ❌ (fatal, no reconnection) | ✅ (auto-reconnect + re-subscribe) |
| Minimum custom resilience code | ❌ (need to build everything) | ✅ (built-in) |
| Python 3.11+ asyncio-native | ❌ (sync API with threading) | ✅ |
| System: APEX | ✅ | ✅ (with system name validation) |

**pyrithmic is disqualified** by the 24/5 uptime requirement alone. Its order plant silently swallows disconnection errors — a trading system cannot tolerate this.

### Minimal Wrapper Code NQHUB Needs on Top of async_rithmic

async_rithmic is production-ready for NQHUB's use case with minimal additions:

```python
# 1. Configure reconnection for 24/5 operation
from async_rithmic import RithmicClient, ReconnectionSettings

client = RithmicClient(
    user="...", password="...", system_name="APEX",
    app_name="NQHUB", app_version="1.0",
    url="wss://...",
    reconnection_settings=ReconnectionSettings(
        max_retries=None,          # infinite retries for 24/5
        backoff_type="exponential",
        interval=5,
        max_delay=60,
        jitter_range=(0.5, 3.0),
    ),
)

# 2. Add connection state logging/alerting
client.on_disconnected += alert_ops_team
client.on_connected += log_reconnection

# 3. NQHUB must build:
#    - TimescaleDB sink: on_tick handler that batches inserts
#    - Account router: map account_ids to eval/paper labels
#    - Order state tracker: since async_rithmic lacks StatusManager,
#      track order lifecycle via on_exchange_order_notification
#    - DQN action → submit_order translation layer
#    - Graceful shutdown handler (SIGTERM → client.disconnect())
```

**What you do NOT need to build** (async_rithmic handles it):
- Reconnection logic
- Subscription recovery after reconnect
- Heartbeat management
- WebSocket error handling
- Multi-plant coordination
- Request retry with backoff
- Concurrent access protection

---

## Appendix A: Main Classes & Method Signatures

### pyrithmic

#### `RithmicBaseApi` — `src/rithmic/interfaces/base.py`

```python
class RithmicBaseApi(metaclass=ABCMeta):
    def __init__(self, env: RithmicEnvironment = None, callback_manager: CallbackManager = None,
                 auto_connect: bool = True, loop: AbstractEventLoop = None)
    def connect_and_login(self)
    def disconnect_and_logout(self)
    @property
    def is_connected(self) -> bool
    def get_reference_data(self, security_code: str, exchange_code: str) -> Union[dict, None]
    def add_callback_manager(self, callback_manager: Union[CallbackManager, None])
    def detach_callback_manager(self)
    async def send_heartbeat(self)
    async def rithmic_login(self)
    async def rithmic_logout(self)
    async def disconnect_from_rithmic(self)
    async def send_buffer(self, message: bytes)
    async def recv_buffer(self)
```

#### `RithmicTickerApi` — `src/rithmic/interfaces/ticker/ticker_api.py`

```python
class RithmicTickerApi(RithmicBaseApi):
    def stream_market_data(self, security_code: str, exchange_code: str) -> TickDataStream
    def stop_market_data_stream(self, security_code: str, exchange_code: str) -> None
    def get_front_month_contract(self, underlying_code: str, exchange_code: str) -> Union[str, None]
    @property
    def total_tick_count(self) -> int
    @property
    def streams_consuming_count(self) -> int
```

#### `RithmicOrderApi` — `src/rithmic/interfaces/order/order_api.py`

```python
class RithmicOrderApi(RithmicBaseApi):
    def submit_market_order(self, order_id: str, security_code: str, exchange_code: str,
                            quantity: int, is_buy: bool) -> MarketOrder
    def submit_limit_order(self, order_id: str, security_code: str, exchange_code: str,
                           quantity: int, is_buy: bool, limit_price: float) -> LimitOrder
    def submit_bracket_order(self, order_id: str, security_code: str, exchange_code: str,
                             quantity: int, is_buy: bool, limit_price: float,
                             take_profit_ticks: int, stop_loss_ticks: int) -> BracketOrder
    def submit_cancel_order(self, order_id: str) -> None
    def submit_cancel_bracket_order_all_children(self, order_id: str) -> None
    def submit_amend_limit_order(self, order_id: str, security_code: str, exchange_code: str,
                                 quantity: int, limit_price: float)
    def submit_amend_stop_loss_order(self, order_id: str, security_code: str, exchange_code: str,
                                     quantity: int, stop_loss: float) -> None
    def submit_amend_bracket_order_all_stop_loss_orders(self, order_id: str, stop_loss: float) -> None
    def submit_amend_bracket_order_all_take_profit_orders(self, order_id: str, limit_price: float) -> None
    def get_order_by_order_id(self, order_id: str) -> VALID_ORDER_TYPES
    @property
    def primary_account_id(self) -> str
    def save_status_manager_state(self, file_path: Path)
```

#### `RithmicHistoryApi` — `src/rithmic/interfaces/history/history_api.py`

```python
class RithmicHistoryApi(RithmicBaseApi):
    def download_historical_tick_data(self, security_code: str, exchange_code: str,
                                      start_time: dt, end_time: dt) -> DownloadRequest
    @property
    def downloads_in_progress(self) -> bool
    @property
    def downloads_are_complete(self) -> bool
```

#### `CallbackManager` — `src/rithmic/callbacks/callbacks.py`

```python
class CallbackId(enum.Enum):
    TICKER_LAST_TRADE = 150
    TICKER_PERIODIC_LIVE_TICK_DATA_SYNCING = 901
    ORDER_RITHMIC_NOTIFICATIONS = 351
    ORDER_EXCHANGE_NOTIFICATIONS = 352
    ORDER_NEW_FILL_NOTIFICATION = 904
    HISTORY_DOWNLOAD_INTERMITTENT_PROCESSING = 902
    HISTORY_DOWNLOAD_COMPLETE_PROCESSING = 903

class CallbackManager:
    def register_callback(self, callback_id: CallbackId, func: Callable) -> None
    def register_callbacks(self, callback_mapping: dict) -> None
    def get_callback_by_callback_id(self, callback_id: CallbackId) -> Union[Callable, None]
    def get_callback_by_template_id(self, template_id: int) -> Union[Callable, None]
```

### async_rithmic

#### `RithmicClient` — `async_rithmic/client.py`

```python
class RithmicClient(DelegateMixin):
    def __init__(self, user: str, password: str, system_name: str,
                 app_name: str, app_version: str, url: str,
                 manual_or_auto: OrderPlacement = OrderPlacement.MANUAL, **kwargs)
    async def connect(self, **kwargs)       # kwargs: plants=[list of SysInfraType]
    async def disconnect(self, timeout=5.0)

    # Events
    on_connected: Event
    on_disconnected: Event
    on_tick: Event
    on_time_bar: Event
    on_order_book: Event
    on_market_depth: Event
    on_rithmic_order_notification: Event
    on_exchange_order_notification: Event
    on_bracket_update: Event
    on_historical_tick: Event
    on_historical_time_bar: Event
    on_instrument_pnl_update: Event
    on_account_pnl_update: Event
```

#### `TickerPlant` — `async_rithmic/plants/ticker.py`

```python
class TickerPlant(BasePlant):
    async def list_exchanges(self)
    async def get_front_month_contract(self, symbol: str, exchange: str) -> str | None
    async def subscribe_to_market_data(self, symbol: str, exchange: str, data_type: DataType | int)
    async def unsubscribe_from_market_data(self, symbol: str, exchange: str, data_type: DataType | int)
    async def search_symbols(self, search_text, **kwargs)
    async def request_market_depth(self, symbol: str, exchange: str, depth_price: float)
    async def subscribe_to_market_depth(self, symbol: str, exchange: str, depth_price: float)
    async def unsubscribe_from_market_depth(self, symbol: str, exchange: str, depth_price: float)
```

#### `OrderPlant` — `async_rithmic/plants/order.py`

```python
class OrderPlant(BasePlant):
    async def list_accounts(self) -> list
    async def get_account_rms(self)
    async def get_product_rms(self, **kwargs)
    async def list_orders(self, **kwargs)
    async def list_brackets(self, **kwargs)
    async def get_order(self, **kwargs)
    async def submit_order(self, order_id: str, symbol: str, exchange: str, qty: int,
                           transaction_type: TransactionType, order_type: OrderType, **kwargs)
    async def cancel_order(self, **kwargs)
    async def cancel_all_orders(self, **kwargs)
    async def modify_order(self, **kwargs)
    async def exit_position(self, **kwargs)
```

#### `HistoryPlant` — `async_rithmic/plants/history.py`

```python
class HistoryPlant(BasePlant):
    async def get_historical_tick_data(self, symbol: str, exchange: str,
                                       start_time: datetime, end_time: datetime, wait: bool = True)
    async def get_historical_time_bars(self, symbol: str, exchange: str,
                                        start_time: datetime, end_time: datetime,
                                        bar_type: TimeBarType, bar_type_periods: int, wait: bool = True)
    async def subscribe_to_time_bar_data(self, symbol: str, exchange: str,
                                          bar_type: TimeBarType, bar_type_periods: int)
    async def unsubscribe_from_time_bar_data(self, symbol: str, exchange: str,
                                              bar_type: TimeBarType, bar_type_periods: int)
```

#### `PnlPlant` — `async_rithmic/plants/pnl.py`

```python
class PnlPlant(BasePlant):
    async def subscribe_to_pnl_updates(self)
    async def unsubscribe_from_pnl_updates(self)
    async def list_positions(self, **kwargs)
    async def list_account_summary(self, **kwargs)
```

#### `ReconnectionSettings` — `async_rithmic/objects.py`

```python
@dataclass
class ReconnectionSettings:
    max_retries: int | None = None
    backoff_type: Literal["constant", "linear", "exponential"] = "linear"
    interval: float = 10
    max_delay: float = None
    jitter_range: tuple = None
    def get_delay(self, attempt: int) -> float
```

#### `RetrySettings` — `async_rithmic/objects.py`

```python
@dataclass
class RetrySettings:
    max_retries: int
    timeout: float
    jitter_range: tuple = None
```
