"""
NQHUB - async_rithmic connectivity test script
Prueba progresiva: conexion -> datos -> ordenes -> historico -> PNL

Uso:
  python test_async_rithmic.py              # Ejecuta todas las pruebas
  python test_async_rithmic.py connect      # Solo prueba conexion
  python test_async_rithmic.py ticks        # Prueba streaming de ticks
  python test_async_rithmic.py history      # Prueba descarga historica
  python test_async_rithmic.py accounts     # Lista cuentas disponibles
  python test_async_rithmic.py orders       # Lista ordenes activas
  python test_async_rithmic.py pnl          # Prueba PNL streaming
"""

import asyncio
import ssl
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Asegurar que se usa el paquete async_rithmic instalado, no el directorio local
# (el repo clonado en ./async_rithmic/ no tiene __init__.py en la raiz y lo sombrea)
sys.path = [p for p in sys.path if not p.endswith('nqhub-rithmic')]

# ---------------------------------------------------------------------------
# Cargar .env si existe (sin depender de python-dotenv)
# ---------------------------------------------------------------------------
def load_dotenv(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not os.getenv(key):  # no sobreescribir env vars ya seteadas
            os.environ[key] = value

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# CONFIGURACION - Lee de .env o variables de entorno
# ---------------------------------------------------------------------------
RITHMIC_USER = os.getenv("RITHMIC_USER", "")
RITHMIC_PASSWORD = os.getenv("RITHMIC_PASSWORD", "")
RITHMIC_SYSTEM = os.getenv("RITHMIC_SYSTEM", "Apex")
RITHMIC_URL = os.getenv("RITHMIC_URL", "wss://rituz00100.rithmic.com:443")
APP_NAME = os.getenv("RITHMIC_APP_NAME", "NQHUB")
APP_VERSION = os.getenv("RITHMIC_APP_VERSION", "1.0")

# Instrumento - NQM6 es el front month al 12 de marzo 2026
# (el script resuelve automaticamente via get_front_month_contract)
SYMBOL = os.getenv("RITHMIC_SYMBOL", "NQ")
EXCHANGE = os.getenv("RITHMIC_EXCHANGE", "CME")
FALLBACK_CONTRACT = "NQM6"  # June 2026 - front month actual


async def test_connect():
    """Prueba 1: Conexion basica y login a todos los plants"""
    from async_rithmic import RithmicClient

    print("=" * 60)
    print("TEST 1: Conexion y autenticacion")
    print("=" * 60)

    client = RithmicClient(
        user=RITHMIC_USER,
        password=RITHMIC_PASSWORD,
        system_name=RITHMIC_SYSTEM,
        app_name=APP_NAME,
        app_version=APP_VERSION,
        url=RITHMIC_URL,
    )

    # Deshabilitar verificacion de hostname - los gateways paper de Rithmic
    # usan certificados que no coinciden con el hostname del servidor
    client.ssl_context.check_hostname = False
    client.ssl_context.verify_mode = ssl.CERT_NONE

    try:
        print(f"Conectando a {RITHMIC_URL} como {RITHMIC_USER}...")
        await client.connect()
        print("[OK] Conectado exitosamente a todos los plants")
        print(f"  FCM ID: {client.fcm_id}")
        print(f"  IB ID:  {client.ib_id}")
        return client
    except Exception as e:
        print(f"[ERROR] Fallo la conexion: {e}")
        raise


async def test_accounts(client):
    """Prueba 2: Listar cuentas disponibles"""
    print()
    print("=" * 60)
    print("TEST 2: Cuentas disponibles")
    print("=" * 60)

    try:
        accounts = await client.list_accounts()
        print(f"[OK] {len(accounts)} cuenta(s) encontrada(s):")
        for acc in accounts:
            print(f"  - {acc}")
        return accounts
    except Exception as e:
        print(f"[ERROR] No se pudieron listar cuentas: {e}")
        return []


async def test_front_month(client):
    """Prueba 3: Resolver front month contract"""
    print()
    print("=" * 60)
    print("TEST 3: Front month contract")
    print("=" * 60)

    try:
        contract = await client.get_front_month_contract(SYMBOL, EXCHANGE)
        if contract:
            print(f"[OK] Front month de {SYMBOL}: {contract}")
            return contract
        else:
            print(f"[WARN] No se encontro front month para {SYMBOL}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


async def test_ticks(client, contract):
    """Prueba 4: Streaming de ticks en tiempo real"""
    from async_rithmic import DataType

    print()
    print("=" * 60)
    print("TEST 4: Streaming de ticks (3 minutos)")
    print("=" * 60)

    tick_count = 0

    async def on_tick(data):
        nonlocal tick_count
        tick_count += 1
        ts = data.get("datetime", "")
        price = data.get("trade_price", "")
        size = data.get("trade_size", "")
        vol = data.get("volume", "")
        if price:
            print(f"  #{tick_count:>6}  {ts}  price={price}  size={size}  vol={vol}")

    client.on_tick += on_tick

    symbol = contract or FALLBACK_CONTRACT
    try:
        print(f"Suscribiendo a {symbol} en {EXCHANGE}...")
        await client.subscribe_to_market_data(symbol, EXCHANGE, DataType.LAST_TRADE)
        print("[OK] Suscrito. Esperando ticks por 3 minutos...")

        await asyncio.sleep(180)

        await client.unsubscribe_from_market_data(symbol, EXCHANGE, DataType.LAST_TRADE)
        print(f"[OK] Recibidos {tick_count} ticks en 3 minutos")

        if tick_count == 0:
            print("[WARN] 0 ticks recibidos - el mercado puede estar cerrado")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client.on_tick -= on_tick


async def test_bbo(client, contract):
    """Prueba 5: Best Bid/Offer streaming"""
    from async_rithmic import DataType

    print()
    print("=" * 60)
    print("TEST 5: BBO streaming (5 segundos)")
    print("=" * 60)

    bbo_count = 0

    async def on_bbo(data):
        nonlocal bbo_count
        bbo_count += 1
        if bbo_count <= 3:
            print(f"  BBO #{bbo_count}: {data}")

    client.on_tick += on_bbo

    symbol = contract or f"{SYMBOL}H6"
    try:
        await client.subscribe_to_market_data(symbol, EXCHANGE, DataType.BBO)
        print(f"[OK] Suscrito a BBO de {symbol}. Esperando 5 segundos...")
        await asyncio.sleep(5)
        await client.unsubscribe_from_market_data(symbol, EXCHANGE, DataType.BBO)
        print(f"[OK] Recibidos {bbo_count} actualizaciones BBO")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client.on_tick -= on_bbo


async def test_history(client, contract):
    """Prueba 6: Descarga de datos historicos"""
    print()
    print("=" * 60)
    print("TEST 6: Datos historicos (ultimos 30 minutos)")
    print("=" * 60)

    symbol = contract or FALLBACK_CONTRACT
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)

    try:
        print(f"Descargando ticks de {symbol} desde {start_time} hasta {end_time}...")
        ticks = await client.get_historical_tick_data(
            symbol, EXCHANGE,
            start_time=start_time,
            end_time=end_time,
            wait=True,
        )

        if ticks:
            print(f"[OK] Descargados {len(ticks)} ticks historicos")
            print(f"  Primer tick: {ticks[0]}")
            print(f"  Ultimo tick: {ticks[-1]}")
        else:
            print("[WARN] 0 ticks historicos - mercado cerrado o sin datos en test env")
    except Exception as e:
        print(f"[ERROR] {e}")


async def test_orders(client):
    """Prueba 7: Listar ordenes activas (NO coloca ordenes)"""
    print()
    print("=" * 60)
    print("TEST 7: Ordenes activas (solo lectura)")
    print("=" * 60)

    try:
        orders = await client.list_orders()
        print(f"[OK] {len(orders)} orden(es) activa(s):")
        for o in orders:
            print(f"  - {o}")
    except Exception as e:
        print(f"[ERROR] {e}")


async def test_pnl(client):
    """Prueba 8: PNL streaming"""
    print()
    print("=" * 60)
    print("TEST 8: PNL streaming (5 segundos)")
    print("=" * 60)

    pnl_updates = 0

    async def on_account_pnl(data):
        nonlocal pnl_updates
        pnl_updates += 1
        if pnl_updates <= 3:
            print(f"  PNL update #{pnl_updates}: {data}")

    client.on_account_pnl_update += on_account_pnl

    try:
        await client.subscribe_to_pnl_updates()
        print("[OK] Suscrito a PNL updates. Esperando 5 segundos...")
        await asyncio.sleep(5)
        await client.unsubscribe_from_pnl_updates()
        print(f"[OK] Recibidas {pnl_updates} actualizaciones PNL")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client.on_account_pnl_update -= on_account_pnl


async def test_reconnection(client):
    """Prueba 9: Verificar configuracion de reconexion"""
    print()
    print("=" * 60)
    print("TEST 9: Configuracion de reconexion")
    print("=" * 60)

    settings = client.reconnection_settings
    print(f"  Max retries:  {settings.max_retries}")
    print(f"  Backoff type: {settings.backoff_type}")
    print(f"  Interval:     {settings.interval}s")
    print(f"  Max delay:    {settings.max_delay}")
    print(f"  Jitter range: {settings.jitter_range}")
    print("[OK] Reconexion configurada correctamente")


async def run_all():
    """Ejecuta todas las pruebas en secuencia"""
    client = await test_connect()
    try:
        accounts = await test_accounts(client)
        contract = await test_front_month(client)
        await test_ticks(client, contract)
        await test_bbo(client, contract)
        await test_history(client, contract)
        await test_orders(client)
        await test_pnl(client)
        await test_reconnection(client)
    finally:
        print()
        print("=" * 60)
        print("Desconectando...")
        await client.disconnect()
        print("[OK] Desconectado limpiamente")

    print()
    print("=" * 60)
    print("TODAS LAS PRUEBAS COMPLETADAS")
    print("=" * 60)


async def run_single(test_name):
    """Ejecuta una prueba individual"""
    client = await test_connect()
    try:
        if test_name == "connect":
            pass  # ya se probo arriba
        elif test_name == "accounts":
            await test_accounts(client)
        elif test_name == "ticks":
            contract = await test_front_month(client)
            await test_ticks(client, contract)
        elif test_name == "bbo":
            contract = await test_front_month(client)
            await test_bbo(client, contract)
        elif test_name == "history":
            contract = await test_front_month(client)
            await test_history(client, contract)
        elif test_name == "orders":
            await test_orders(client)
        elif test_name == "pnl":
            await test_pnl(client)
        elif test_name == "reconnect":
            await test_reconnection(client)
        else:
            print(f"Test desconocido: {test_name}")
            print("Opciones: connect, accounts, ticks, bbo, history, orders, pnl, reconnect")
    finally:
        await client.disconnect()
        print("[OK] Desconectado")


def main():
    if not RITHMIC_USER or not RITHMIC_PASSWORD:
        print("ERROR: Credenciales no configuradas.")
        print()
        print("Crea un archivo .env a partir del sample:")
        print("  cp .env.sample .env")
        print("  # Edita .env con tus credenciales de Apex/Rithmic")
        print()
        print("O usa variables de entorno:")
        print("  export RITHMIC_USER=tu_usuario")
        print("  export RITHMIC_PASSWORD=tu_password")
        sys.exit(1)

    test_name = sys.argv[1] if len(sys.argv) > 1 else None

    if test_name:
        asyncio.run(run_single(test_name))
    else:
        asyncio.run(run_all())


if __name__ == "__main__":
    main()
