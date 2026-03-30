"""
NQHUB - Tick Viewer con direccion BID/ASK y display scrolling

Muestra los ultimos 10 ticks en scroll con colores:
  Verde (ASK) = comprador agresivo hit ask
  Rojo  (BID) = vendedor agresivo hit bid

Uso:
  python tick_viewer.py          # NQ front month
  python tick_viewer.py ESM6     # Contrato especifico

Ctrl+C para salir limpiamente.
"""

import asyncio
import ssl
import sys
import os
from collections import deque
from pathlib import Path

# Evitar que el directorio local sombree el paquete instalado
sys.path = [p for p in sys.path if not p.endswith('nqhub-rithmic')]

# --- Cargar .env ---
def load_dotenv(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not os.getenv(key):
            os.environ[key] = value

load_dotenv(Path(__file__).parent / ".env")

RITHMIC_USER = os.getenv("RITHMIC_USER", "")
RITHMIC_PASSWORD = os.getenv("RITHMIC_PASSWORD", "")
RITHMIC_SYSTEM = os.getenv("RITHMIC_SYSTEM", "Apex")
RITHMIC_URL = os.getenv("RITHMIC_URL", "wss://rituz00100.rithmic.com:443")
APP_NAME = os.getenv("RITHMIC_APP_NAME", "NQHUB")
APP_VERSION = os.getenv("RITHMIC_APP_VERSION", "1.0")
SYMBOL = os.getenv("RITHMIC_SYMBOL", "NQ")
EXCHANGE = os.getenv("RITHMIC_EXCHANGE", "CME")

# --- ANSI colors ---
GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

LINES = 11  # 10 history + 1 current


def format_tick(data, tick_num):
    ts = data.get("datetime", "")
    price = data.get("trade_price", 0)
    size = data.get("trade_size", 0)
    aggressor = data.get("aggressor", 0)

    time_str = ts.strftime("%H:%M:%S.%f")[:-3] if hasattr(ts, "strftime") else str(ts)

    if aggressor == 1:
        side = f"{GREEN}ASK \u25b2{RESET}"
    elif aggressor == 2:
        side = f"{RED}BID \u25bc{RESET}"
    else:
        side = f"{DIM} ?  {RESET}"

    return f"  {time_str}  {price:>10.2f}  x{size:<4}  {side}"


def redraw(header, history, current, tick_count):
    # Move cursor up to top of our display area and clear
    up = f"\033[{LINES + 2}A"
    clear = "\033[K"

    lines = [up]
    lines.append(f"{clear}{DIM}\u2500\u2500\u2500 {header} \u2500\u2500\u2500 Ticks: {tick_count} \u2500\u2500\u2500{RESET}")

    for row in history:
        lines.append(f"{clear}{row}")
    # Pad empty rows if history is not full yet
    for _ in range(10 - len(history)):
        lines.append(clear)

    if current:
        lines.append(f"{clear}{BOLD}>{RESET}{current[1:]}")  # replace leading space with >
    else:
        lines.append(clear)

    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


async def run(contract_override=None):
    from async_rithmic import RithmicClient, DataType, SysInfraType

    client = RithmicClient(
        user=RITHMIC_USER,
        password=RITHMIC_PASSWORD,
        system_name=RITHMIC_SYSTEM,
        app_name=APP_NAME,
        app_version=APP_VERSION,
        url=RITHMIC_URL,
    )
    client.ssl_context.check_hostname = False
    client.ssl_context.verify_mode = ssl.CERT_NONE

    print(f"Conectando a {RITHMIC_URL} como {RITHMIC_USER}...")
    await client.connect(plants=[SysInfraType.TICKER_PLANT])

    # Resolve contract
    if contract_override:
        contract = contract_override
    else:
        contract = await client.get_front_month_contract(SYMBOL, EXCHANGE)
        if not contract:
            contract = f"{SYMBOL}M6"
    print(f"Suscribiendo a {contract} @ {EXCHANGE}...")

    history = deque(maxlen=10)
    tick_count = 0
    current_line = None
    header = f"{contract} @ {EXCHANGE}"

    # Print blank lines to reserve space for our display
    sys.stdout.write("\n" * (LINES + 2))
    sys.stdout.flush()

    async def on_tick(data):
        nonlocal tick_count, current_line
        if data.get("data_type") != DataType.LAST_TRADE:
            return
        if not data.get("trade_price"):
            return

        tick_count += 1

        # Push previous current into history
        if current_line is not None:
            history.append(current_line)

        current_line = format_tick(data, tick_count)
        redraw(header, history, current_line, tick_count)

    client.on_tick += on_tick

    await client.subscribe_to_market_data(contract, EXCHANGE, DataType.LAST_TRADE)
    print(f"\033[{LINES + 2}A\033[K[OK] Streaming... Ctrl+C para salir\n" + "\n" * (LINES + 1))

    try:
        await asyncio.Event().wait()  # Run forever
    except asyncio.CancelledError:
        pass
    finally:
        client.on_tick -= on_tick
        await client.unsubscribe_from_market_data(contract, EXCHANGE, DataType.LAST_TRADE)
        await client.disconnect()
        print(f"\n{DIM}[OK] Desconectado. {tick_count} ticks recibidos.{RESET}")


def main():
    if not RITHMIC_USER or not RITHMIC_PASSWORD:
        print("ERROR: Credenciales no configuradas. Revisa tu .env")
        sys.exit(1)

    contract = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        asyncio.run(run(contract))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
