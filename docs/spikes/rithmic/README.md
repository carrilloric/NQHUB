# NQHUB Rithmic

Conexión a la API de Rithmic (Protocol Buffer sobre WebSocket) para trading de futuros NQ en cuentas Apex Trader Funding.

Usa el paquete [`async_rithmic`](https://github.com/rundef/async_rithmic) v1.5.9 — API async nativa con reconexión automática, soporte multi-cuenta y streaming de datos en tiempo real.

## Requisitos

- Python >= 3.10
- Cuenta Apex Trader Funding con acceso Rithmic API

## Instalación

```bash
pip install async_rithmic
```

## Configuración

Copia el archivo de ejemplo y rellena con tus credenciales de Apex/Rithmic:

```bash
cp .env.sample .env
```

```env
RITHMIC_USER=tu_usuario_rithmic
RITHMIC_PASSWORD=tu_password_rithmic
RITHMIC_SYSTEM=Apex
RITHMIC_URL=wss://rituz00100.rithmic.com:443
```

Las credenciales se obtienen en: **Apex Trader Funding > Plataformas > Rithmic API Access**

## Scripts

### `tick_viewer.py` — Visualizador de ticks en tiempo real

Muestra los últimos 10 ticks en scroll con dirección de agresión:
- Verde (ASK) = comprador agresivo
- Rojo (BID) = vendedor agresivo

```bash
python tick_viewer.py              # NQ front month automático
python tick_viewer.py NQM6         # Contrato específico
```

### `test_async_rithmic.py` — Test progresivo de conectividad

Pruebas paso a paso: conexión, cuentas, ticks, historial, órdenes, PNL.

```bash
python test_async_rithmic.py              # Todas las pruebas
python test_async_rithmic.py connect      # Solo conexión y login
python test_async_rithmic.py accounts     # Listar cuentas Apex
python test_async_rithmic.py ticks        # Streaming de ticks (3 min)
python test_async_rithmic.py history      # Datos históricos (30 min)
python test_async_rithmic.py orders       # Órdenes activas (solo lectura)
python test_async_rithmic.py pnl          # Streaming de PNL
```

### `discover_gateways.py` — Descubrir gateways Rithmic

Consulta todos los gateways conocidos y muestra qué sistemas soportan (no requiere credenciales).

```bash
python discover_gateways.py
```

## Estructura del proyecto

```
nqhub-rithmic/
├── .env.sample                        # Template de credenciales
├── .env                               # Credenciales (no versionado)
├── .gitignore
├── tick_viewer.py                     # Visualizador de ticks en tiempo real
├── test_async_rithmic.py              # Tests de conectividad
├── discover_gateways.py               # Descubrimiento de gateways
├── PYRITHMIC_VS_ASYNC_RITHMIC.md      # Análisis comparativo pyrithmic vs async_rithmic
├── async_rithmic/                     # Repo clonado + venv del paquete
└── pyrithmic/                         # Repo clonado (descartado, solo referencia)
```

## Horario del mercado

CME Globex para NQ (E-mini Nasdaq 100): domingo 17:00 CT — viernes 16:00 CT, con pausa diaria 16:00–17:00 CT.

Si ejecutas los scripts fuera de horario, la conexión y cuentas funcionarán pero no recibirás ticks.

## Decisión técnica

Se evaluaron `pyrithmic` y `async_rithmic`. Se eligió **async_rithmic** por:
- Reconexión automática con backoff configurable (crítico para operación 24/5)
- API async nativa (sin threading)
- Soporte multi-cuenta (`account_id` en órdenes)
- Propagación correcta de errores (pyrithmic los traga silenciosamente)
- Mantenimiento activo (146 commits vs 19)

Ver [`PYRITHMIC_VS_ASYNC_RITHMIC.md`](PYRITHMIC_VS_ASYNC_RITHMIC.md) para el análisis completo.
