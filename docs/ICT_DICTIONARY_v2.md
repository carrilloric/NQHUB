# ICT & Smart Money Dictionary

Diccionario completo de términos utilizados en metodologías Smart Money Concepts (SMC), ICT (Inner Circle Trader) y Order Flow para análisis de mercados financieros.

---

## 🏛️ Contexto: Cómo se Relacionan

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART MONEY CONCEPTS (SMC)                   │
│         Filosofía: "Seguir al dinero institucional"             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │    ICT      │  │   Wyckoff   │  │  Volume Spread Analysis │ │
│  │ (Huddleston)│  │             │  │         (VSA)           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
│  Análisis basado en ESTRUCTURA DE PRECIO (velas OHLC)          │
└─────────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────────┐
│                        ORDER FLOW                               │
│         Análisis de TRANSACCIONES REALES                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Footprint  │  │   Delta     │  │    Volume Profile       │ │
│  │   Charts    │  │  Analysis   │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
│  Análisis basado en VOLUMEN y FLUJO DE ÓRDENES                 │
└─────────────────────────────────────────────────────────────────┘
                              =
┌─────────────────────────────────────────────────────────────────┐
│                   ANÁLISIS COMBINADO                            │
│                                                                 │
│  ICT/SMC identifica ZONAS TEÓRICAS de interés institucional    │
│  Order Flow CONFIRMA actividad real en esas zonas              │
│                                                                 │
│  Resultado: Señales de mayor probabilidad                       │
└─────────────────────────────────────────────────────────────────┘
```

### Diferencias Clave

| Aspecto | ICT/SMC | Order Flow |
|---------|---------|------------|
| Datos | Velas (OHLC) | Volumen, Tick, Trades |
| Enfoque | Estructura de precio | Transacciones reales |
| Pregunta | "¿Dónde DEBERÍA actuar Smart Money?" | "¿Dónde ESTÁ actuando?" |
| Ventaja | Anticipación | Confirmación |
| Limitación | Teórico/Predictivo | Reactivo/Confirmatorio |

---

## 📊 Estructura de Mercado (Market Structure)

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Break of Structure | BOS | Ruptura de un nivel estructural que confirma continuación de tendencia |
| Change of Character | CHoCH | Cambio repentino en la tendencia del mercado, indica posible reversión |
| Market Structure Shift | MSS | Cambio en la estructura del mercado que señala nueva dirección |
| Higher High | HH | Máximo más alto que el anterior (tendencia alcista) |
| Higher Low | HL | Mínimo más alto que el anterior (tendencia alcista) |
| Lower High | LH | Máximo más bajo que el anterior (tendencia bajista) |
| Lower Low | LL | Mínimo más bajo que el anterior (tendencia bajista) |
| Equal Highs | EQH | Máximos que se alinean al mismo nivel (zona de liquidez) |
| Equal Lows | EQL | Mínimos que se alinean al mismo nivel (zona de liquidez) |
| Swing High | - | Punto máximo local en el precio |
| Swing Low | - | Punto mínimo local en el precio |

---

## 🎯 PD Arrays (Premium/Discount Arrays)

Las PD Arrays son zonas de precio donde Smart Money opera. No son indicadores técnicos tradicionales.

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Premium Zone | - | Zona por encima del 50% del rango (precios "caros") |
| Discount Zone | - | Zona por debajo del 50% del rango (precios "baratos") |
| Equilibrium | EQ | Nivel del 50% de un rango, punto de balance |
| Point of Interest | POI | Nivel de precio donde se anticipa reacción significativa |
| First Trouble Area | FTA | Zona que puede interrumpir la continuación del precio |

---

## 📦 Order Blocks (OB)

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Order Block | OB | Última vela alcista/bajista antes de un movimiento fuerte. Zona donde instituciones colocaron órdenes grandes |
| Bullish Order Block | OB+ | Order block que confirma tendencia alcista (última vela bajista antes de subida) |
| Bearish Order Block | OB- | Order block que confirma tendencia bajista (última vela alcista antes de bajada) |
| Breaker Block | BB | Order block fallido que cambia de rol (soporte→resistencia o viceversa) |
| Mitigation Block | MB | Bloque donde Smart Money reduce riesgo/cubre posiciones |
| Propulsion Block | PB | Bloque responsable de movimientos fuertes y sostenidos |
| Rejection Block | RB | Versión refinada del OB usando las mechas de las velas |
| Return to Order Block | RTO | Cuando el precio regresa a testear un order block |

### Validación de Order Blocks
Un OB válido debe:
1. Barrer liquidez (sweep)
2. Crear imbalance
3. Permanecer sin tocar
4. Causar ruptura de estructura

---

## ⚡ Fair Value Gaps (FVG)

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Fair Value Gap | FVG | Gap de precio en patrón de 3 velas donde el precio se movió muy rápido, creando "negocio sin terminar" |
| Bullish FVG | BFVG | Gap alcista - el máximo de vela 1 no traslapa con mínimo de vela 3 |
| Bearish FVG | SFVG | Gap bajista - el mínimo de vela 1 no traslapa con máximo de vela 3 |
| Inversion FVG | IFVG | FVG que fue roto y ahora actúa en dirección opuesta (soporte↔resistencia) |
| Fair Value for Buying | FVFB | Gap en zona de descuento, oportunidad de compra |
| Fair Value for Selling | FVFS | Gap en zona premium, oportunidad de venta |
| Consequent Encroachment | CE | Punto medio (50%) del FVG - nivel de reacción importante |
| Volume Imbalance | VI | Gap entre cuerpos de velas (no mechas), muestra urgencia |
| Liquidity Void | LV | Área sin actividad de trading después de movimientos bruscos |
| Breakaway Gap | BAG | Gap que se forma en nivel de ruptura clave, indica cambio estructural |

### Formación de FVG
```
Bullish FVG:
Vela 1: [===]
Vela 2:        [========]  ← Vela grande
Vela 3:              [===]
         ↑___↑ = GAP (FVG)

Bearish FVG:
Vela 1:              [===]
Vela 2:        [========]  ← Vela grande
Vela 3: [===]
         ↑___↑ = GAP (FVG)
```

---

## 💧 Liquidez (Liquidity)

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Liquidity | LQ | Facilidad para convertir activo en efectivo sin afectar precio |
| Liquidity Pool | LP | Zona con alta concentración de órdenes (incluye stop losses) |
| Buy-Side Liquidity | BSL | Liquidez por encima de máximos (stop losses de shorts) |
| Sell-Side Liquidity | SSL | Liquidez por debajo de mínimos (stop losses de longs) |
| Draw on Liquidity | DOL | Movimiento del precio hacia zonas de alta liquidez |
| Liquidity Grab | - | Precio que brevemente toca nivel de liquidez antes de revertir |
| Liquidity Sweep | - | Barrido de liquidez que activa stop losses |
| Stop Hunt | - | Movimiento diseñado para activar stop losses antes de revertir |
| Inducement | IDM | Cuando Smart Money mueve precio para atrapar traders retail |
| First Point of Liquidity | FPOL | Primer nivel de liquidez que refleja actividad del mercado |

---

## 🔄 Reacciones e Interacciones con Zonas

| Término | Definición |
|---------|------------|
| Reaction | Precio reacciona/rebota en una zona (la respeta) |
| Respect | La zona mantiene su función (soporte/resistencia) |
| Mitigation | Penetración parcial de la zona |
| Fill | Precio llena completamente un FVG |
| Partial Fill | Precio llena parcialmente un FVG |
| Breach | Precio rompe completamente la zona |
| Sweep | Precio barre liquidez de una zona |
| Tap | Precio toca brevemente una zona |
| Displacement | Movimiento fuerte que crea FVG, muestra intención direccional |

### Estados de una Zona
```
1. Fresh/Untested  → Zona sin tocar (más fuerte)
2. Tested          → Zona testeada una vez
3. Mitigated       → Zona parcialmente penetrada
4. Filled          → Zona completamente llenada
5. Breached        → Zona rota/invalidada
6. Inverted        → Zona que cambió de rol
```

---

## 📈 Order Flow Analysis

Order Flow analiza las transacciones reales del mercado para confirmar o invalidar zonas identificadas por ICT/SMC.

### Conceptos Fundamentales

| Término | Definición |
|---------|------------|
| Order Flow | Flujo de órdenes de compra/venta en tiempo real |
| Tape Reading | Lectura del flujo de transacciones (Time & Sales) |
| Level 2 / DOM | Depth of Market - libro de órdenes visible |
| Market Depth | Profundidad del mercado (órdenes pendientes) |

### Métricas de Volumen

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Volume | VOL | Cantidad total de contratos/acciones negociados |
| Delta | Δ | Diferencia entre volumen comprado y vendido (Ask - Bid) |
| Cumulative Delta | CD | Delta acumulado a lo largo del tiempo |
| Delta Divergence | - | Cuando precio y delta van en direcciones opuestas |
| Volume Profile | VP | Distribución del volumen por nivel de precio |
| Point of Control | POC | Nivel de precio con mayor volumen negociado |
| Value Area | VA | Rango donde se negoció ~70% del volumen |
| Value Area High | VAH | Límite superior del Value Area |
| Value Area Low | VAL | Límite inferior del Value Area |

### Footprint Charts

| Término | Definición |
|---------|------------|
| Footprint Chart | Gráfico que muestra volumen bid/ask por nivel de precio dentro de cada vela |
| Bid Volume | Volumen ejecutado al precio bid (ventas agresivas) |
| Ask Volume | Volumen ejecutado al precio ask (compras agresivas) |
| Imbalance | Desequilibrio significativo entre bid y ask en un nivel |
| Stacked Imbalances | Múltiples imbalances consecutivos (señal fuerte) |
| Absorption | Cuando un lado absorbe la presión del otro sin mover precio |
| Exhaustion | Volumen alto sin movimiento de precio (fin de tendencia) |

### Tipos de Órdenes

| Término | Definición |
|---------|------------|
| Market Order | Orden ejecutada inmediatamente al mejor precio disponible |
| Limit Order | Orden pendiente a un precio específico |
| Passive Order | Orden limit esperando ser ejecutada |
| Aggressive Order | Orden market que "ataca" el libro |
| Iceberg Order | Orden grande dividida para ocultar tamaño real |
| Spoofing | Órdenes falsas para manipular percepción (ilegal) |

### Patrones de Order Flow

| Patrón | Descripción | Implicación |
|--------|-------------|-------------|
| Absorption | Alto volumen sin movimiento | Posible reversión |
| Exhaustion | Volumen decreciente en tendencia | Fin de tendencia |
| Initiative Buying/Selling | Órdenes agresivas moviendo precio | Continuación |
| Responsive Buying/Selling | Órdenes en zonas de valor | Reversión al valor |
| Trapped Traders | Volumen en dirección equivocada | Combustible para movimiento opuesto |

### Big Trades Detection

| Término | Definición |
|---------|------------|
| Big Trade | Transacción de tamaño significativamente mayor al promedio |
| Block Trade | Orden institucional grande ejecutada fuera del libro |
| Iceberg Detection | Identificación de órdenes ocultas por patrones de ejecución |
| Sweep | Serie rápida de órdenes que "barren" múltiples niveles |

---

## ⏰ Tiempo y Sesiones

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Higher Time Frame | HTF | Marco temporal mayor para análisis macro |
| Lower Time Frame | LTF | Marco temporal menor para entradas precisas |
| Kill Zone | KZ | Períodos de alta actividad institucional |
| London Kill Zone | LKZ | 2:00 AM - 5:00 AM EST |
| New York Kill Zone | NYKZ | 7:00 AM - 11:00 AM EST |
| Asian Session | AS | Sesión de menor volatilidad |
| High of Day | HOD | Máximo del día |
| Low of Day | LOD | Mínimo del día |
| Previous Day High | PDH | Máximo del día anterior |
| Previous Day Low | PDL | Mínimo del día anterior |
| Previous Week High | PWH | Máximo de la semana anterior |
| Previous Week Low | PWL | Mínimo de la semana anterior |

---

## 📐 Herramientas de Entrada

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Optimal Trade Entry | OTE | Zona de retroceso 62%-79% donde instituciones re-entran |
| Mean Threshold | MT | Punto medio de un order block, usado como nivel de retroceso |
| Decisional Zone | - | Zona donde Smart Money toma decisiones clave |
| Extreme Zone | - | Última área significativa de ejecución institucional |

---

## 🏦 Smart Money Concepts (SMC)

| Término | Abreviación | Definición |
|---------|-------------|------------|
| Smart Money | SM | Instituciones financieras (bancos, hedge funds) |
| Market Maker | MM | Creador de mercado, provee liquidez |
| Retail Trader | - | Trader individual/minorista |
| Accumulation | - | Fase donde SM acumula posiciones |
| Distribution | - | Fase donde SM distribuye/vende posiciones |
| Manipulation | - | Movimientos para atrapar traders retail |
| CISD | Change in State of Delivery | Cambio en la dirección de entrega del precio |

---

## 📈 Algoritmos y Modelos de Precio

| Término | Definición |
|---------|------------|
| IPDA | Interbank Price Delivery Algorithm - algoritmo de entrega de precio |
| AMD | Accumulation, Manipulation, Distribution - ciclo de mercado |
| PO3 | Power of 3 - Accumulation, Manipulation, Distribution |
| Judas Swing | Movimiento falso inicial diseñado para atrapar traders |
| True Day Open | Precio de apertura real del día (midnight NY time) |

---

## ✅ Validación y Confirmación

### Criterios ICT/SMC

| Criterio | Descripción |
|----------|-------------|
| Liquidity Sweep | ¿Barrió liquidez antes de la zona? |
| Structure Break | ¿Causó ruptura de estructura? |
| Displacement | ¿Hubo desplazamiento fuerte? |
| Imbalance | ¿Creó FVG/imbalance? |
| Time & Price | ¿Ocurrió en kill zone? |

### Confirmación con Order Flow

| Confirmación | Qué buscar |
|--------------|------------|
| Delta Confirmation | Delta positivo en zonas alcistas, negativo en bajistas |
| Volume Spike | Incremento de volumen en la zona |
| Absorption | Alto volumen sin movimiento (soporte/resistencia fuerte) |
| Imbalance Stacking | Múltiples imbalances en dirección del trade |
| Big Trade Activity | Presencia de transacciones institucionales |

---

## 🎯 Aplicación en NQHUB

### Mapeo de Términos a Código

| Concepto | Archivo en NQHUB |
|----------|------------------|
| Fair Value Gap | `fvg_detector.py` |
| Liquidity Pool | `lp_detector.py` |
| Order Block | `ob_detector.py` |
| Reactions/Mitigation | `interaction_tracker.py` |
| Big Trades | `DETECCION_BIG_TRADES.md` |

### Estados de Detección

```python
# Estados de FVG
FVG_STATUS = {
    'fresh': 'Sin tocar',
    'tested': 'Testeado',
    'mitigated': 'Mitigado parcialmente',
    'filled': 'Llenado completamente',
    'inverted': 'Invertido (IFVG)'
}

# Tipos de reacción
REACTION_TYPE = {
    'bounce': 'Rebote (respeta zona)',
    'tap': 'Toque breve',
    'mitigation': 'Penetración parcial',
    'ce_touch': 'Toque en Consequent Encroachment (50%)',
    'breach': 'Ruptura completa'
}

# Calidad basada en reacciones
QUALITY_SCORE = {
    'high': 'Múltiples rebotes, zona respetada',
    'medium': 'Una reacción clara',
    'low': 'Sin reacciones aún',
    'invalid': 'Zona rota/invalidada'
}

# Confirmación Order Flow
OF_CONFIRMATION = {
    'strong': 'Delta + Volume + Big Trades alineados',
    'moderate': 'Al menos 2 confirmaciones',
    'weak': 'Solo 1 confirmación',
    'none': 'Sin confirmación de order flow'
}
```

### Flujo de Análisis Combinado

```
1. ICT/SMC Detection
   ├── Identificar FVG, OB, LP
   └── Determinar zonas de interés

2. Order Flow Confirmation
   ├── Analizar delta en la zona
   ├── Buscar absorption/exhaustion
   └── Detectar big trades

3. Quality Scoring
   ├── ICT criteria score
   ├── Order Flow confirmation score
   └── Combined probability score

4. Interaction Tracking
   ├── Monitorear reacciones
   ├── Actualizar estados
   └── Recalcular calidad
```

---

## 📚 Fuentes y Referencias

### Metodología ICT
- **Inner Circle Trader (ICT)** - Michael Huddleston
  - YouTube: The Inner Circle Trader
  - Metodología original de Smart Money Concepts

### Recursos Consultados

1. **FXOpen Blog** - PD Arrays in ICT
   - https://fxopen.com/blog/en/what-is-a-pd-array-in-ict-and-how-can-you-use-it-in-trading/
   - Premium/Discount zones, Order Blocks, FVGs

2. **TradingView - ICT Concept Indicator**
   - https://www.tradingview.com/script/5n6Lawvs-ICT-Concept-TradingFinder-Order-Block-FVG-Liquidity-Sweeps/
   - Implementación técnica de conceptos ICT

3. **TradeZella - Key ICT Concepts**
   - https://www.tradezella.com/learning-items/key-ict-concepts
   - FVG formations, inversions, reactions

4. **TradingFinder - ICT Abbreviations**
   - https://tradingfinder.com/education/forex/ict-abbreviation/
   - Terminología completa ICT/SMC

5. **TradingFinder - Order Block Strategy**
   - https://tradingfinder.com/education/forex/trade-continuations-using-order-blocks/
   - Estrategias de continuación con OB

6. **Altrady - PD Array Matrix**
   - https://www.altrady.com/crypto-trading/smart-money-concept/pd-array-matrix-top-down-analysis-for-crypto-trading
   - Multi-timeframe analysis, POI prioritization

7. **Forex Factory - ICT Breakaway Gaps**
   - https://www.forexfactory.com/thread/1343903-ict-breakaway-gaps-a-traders-guide-tflab
   - Breakaway gaps, breaker blocks

8. **SlideShare - Order Block in Trend Following**
   - https://www.slideshare.net/slideshow/order-block-in-trend-following-with-ict-entry-using-ob-and-fvg-2818/279908425
   - SMC terminologies, liquidity concepts

### Order Flow Resources
- **ATAS Platform** - Order Flow analysis tools
- **Bookmap** - DOM visualization
- **Jigsaw Trading** - Order flow education
- **Axia Futures** - Footprint chart analysis

### Libros Recomendados
- "Trading and Exchanges" - Larry Harris (Market Microstructure)
- "The Art and Science of Technical Analysis" - Adam Grimes
- "Auction Market Theory" - Various authors

---

## 🔄 Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | Dic 2024 | Versión inicial - ICT terminology |
| 2.0 | Dic 2024 | Agregado Order Flow, relación SMC/ICT/OF, fuentes |

---

*Para uso en proyecto NQHUB - Pattern Detection Module*
*Automation Labs - PlantTalk AI*
