"""
Descubre qué system names soporta cada gateway conocido de Rithmic.
No requiere credenciales - solo consulta la info pública del servidor.
"""
import asyncio
import ssl
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "async_rithmic", "NQasyncrithmic", "Lib", "site-packages"))

import websockets
from async_rithmic.protocol_buffers.request_rithmic_system_info_pb2 import RequestRithmicSystemInfo
from async_rithmic.protocol_buffers.response_rithmic_system_info_pb2 import ResponseRithmicSystemInfo

KNOWN_GATEWAYS = [
    "wss://rituz00100.rithmic.com:443",
    "wss://rituz00101.rithmic.com:443",
    "wss://rituz01000.rithmic.com:443",
    "wss://rituz01001.rithmic.com:443",
    "wss://rituz01002.rithmic.com:443",
    "wss://rituz01003.rithmic.com:443",
    "wss://rituz01004.rithmic.com:443",
    "wss://rituz04000.rithmic.com:443",
    "wss://rituz04001.rithmic.com:443",
    "wss://rituz04002.rithmic.com:443",
    "wss://rituz05000.rithmic.com:443",
    "wss://rituz05001.rithmic.com:443",
]

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def query_gateway(url):
    try:
        ws = await asyncio.wait_for(
            websockets.connect(url, ssl=ssl_context, ping_interval=10, ping_timeout=5),
            timeout=5,
        )

        # Build request with 4-byte length prefix (Rithmic protocol)
        req = RequestRithmicSystemInfo()
        req.template_id = 16
        serialized = req.SerializeToString()
        length = len(serialized)
        buffer = length.to_bytes(4, byteorder='big', signed=True) + serialized
        await ws.send(buffer)

        # Receive response with 4-byte length prefix
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        resp = ResponseRithmicSystemInfo()
        resp.ParseFromString(raw[4:])  # skip 4-byte length header

        systems = list(resp.system_name)
        await ws.close()
        return systems
    except asyncio.TimeoutError:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


async def main():
    print("Consultando gateways de Rithmic...\n")

    # Run all queries concurrently
    tasks = [(url, asyncio.create_task(query_gateway(url))) for url in KNOWN_GATEWAYS]

    for url, task in tasks:
        result = await task
        if isinstance(result, list) and result:
            has_apex = any("apex" in s.lower() for s in result)
            marker = "  <-- APEX!" if has_apex else ""
            print(f"  {url}")
            print(f"    Systems: {result}{marker}")
        elif isinstance(result, list):
            print(f"  {url}")
            print(f"    (sin sistemas)")
        else:
            print(f"  {url}")
            print(f"    {result}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
