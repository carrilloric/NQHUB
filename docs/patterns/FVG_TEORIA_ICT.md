# Fair Value Gaps (FVGs) - ICT Theory

## Overview

Fair Value Gaps (FVGs) are areas on a price chart where there is an imbalance between buyers and sellers, resulting in a "gap" that was created by rapid institutional movement. According to ICT (Inner Circle Trader) methodology, these gaps represent areas where Smart Money operates and often act as magnets for future price action.

## FVG Types

### BISI FVG (Buyside Imbalance, Sellside Inefficiency)
- **Type**: BULLISH FVG
- **Formation**: Created when price moves up aggressively, leaving a gap between Vela 1 high and Vela 3 low
- **Market Structure**: Sellside has inefficiency (not enough sellers), Buyside has imbalance (institutional buying)
- **Trading Implication**: Acts as **SUPPORT** when price retraces

### SIBI FVG (Sellside Imbalance, Buyside Inefficiency)
- **Type**: BEARISH FVG
- **Formation**: Created when price moves down aggressively, leaving a gap between Vela 1 low and Vela 3 high
- **Market Structure**: Buyside has inefficiency (not enough buyers), Sellside has imbalance (institutional selling)
- **Trading Implication**: Acts as **RESISTANCE** when price retraces

## 3-Candle Pattern Detection

FVGs are identified using a 3-candle pattern:

```
BULLISH FVG (BISI):
┌─────────────────────────┐
│    Vela 3 (next)       │  Formation Candle
│      ╔═══════╗         │
│      ║       ║         │
│      ╚═══════╝         │
│                        │
│    ═══ GAP ═══         │  <-- FVG Zone (Imbalance)
│                        │
│    Vela 2 (middle)     │
│      ╔═══════╗         │
│      ╚═══════╝         │
│                        │
│    Vela 1 (previous)   │
│      ╔═══════╗         │
│      ╚═══════╝         │
└─────────────────────────┘

Condition: Vela 1 High < Vela 3 Low
```

```
BEARISH FVG (SIBI):
┌─────────────────────────┐
│    Vela 1 (previous)   │
│      ╔═══════╗         │
│      ║       ║         │
│      ╚═══════╝         │
│                        │
│    Vela 2 (middle)     │
│      ╔═══════╗         │
│      ╚═══════╝         │
│                        │
│    ═══ GAP ═══         │  <-- FVG Zone (Imbalance)
│                        │
│    Vela 3 (next)       │  Formation Candle
│      ╔═══════╗         │
│      ╚═══════╝         │
└─────────────────────────┘

Condition: Vela 1 Low > Vela 3 High
```

**Important**: `formation_time` is set to **Vela 3's timestamp** because the FVG is confirmed when Vela 3 closes, not when Vela 2 forms.

## ICT 3 Key Levels

Every FVG has 3 critical price levels that traders use for entries and targets:

### 1. Premium Level 🔴
- **BULLISH FVG**: Top of the gap (Vela 3 Low = `fvg_end`)
- **BEARISH FVG**: Top of the gap (Vela 1 Low = `fvg_start`)
- **Usage**:
  - For BEARISH FVGs: Best entry for shorts
  - For BULLISH FVGs: Profit target zone

### 2. Consequent Encroachment (C.E.) ⚪
- **Both FVG Types**: 50% level, the midpoint of the gap
- **Calculation**: `(premium_level + discount_level) / 2`
- **Usage**:
  - **Primary Entry Zone**: Highest probability entry point
  - Price often reacts strongly at this level
  - ICT teaches this is where Smart Money "fills" the gap partially

### 3. Discount Level 🟢
- **BULLISH FVG**: Bottom of the gap (Vela 1 High = `fvg_start`)
- **BEARISH FVG**: Bottom of the gap (Vela 3 High = `fvg_end`)
- **Usage**:
  - For BULLISH FVGs: Best entry for longs
  - For BEARISH FVGs: Profit target zone

## Displacement

**Displacement** refers to the energetic, aggressive movement that creates the FVG. It indicates strong institutional participation.

### Displacement Score Calculation
```python
displacement_score = gap_size / ATR(14)
```

### Displacement Score Interpretation
- **< 0.5**: Weak displacement, low probability setup
- **0.5 - 1.0**: Normal displacement
- **1.0 - 1.5**: Strong displacement, good setup
- **> 1.5**: Very strong displacement, high probability setup ⚡
  - Indicates institutional "Power 3" or algorithmic movement
  - FVG likely to hold on first retest

### Why Displacement Matters
- High displacement suggests Smart Money urgency
- Often associated with:
  - News releases
  - Liquidity grabs
  - Institutional order flow
  - Break of market structure

## Break of Structure (BOS)

**Break of Structure** occurs when price breaks a significant swing high (for bullish BOS) or swing low (for bearish BOS), indicating a potential trend change.

### BOS Detection in NQHUB
Currently implemented as a simple heuristic:
```python
has_break_of_structure = displacement_score > 1.5
```

A displacement score above 1.5x ATR suggests the movement was strong enough to potentially break market structure.

### BOS Significance
- **With BOS** ⚡: FVG is more likely to hold as support/resistance
- **Without BOS**: FVG may be weaker, treat with caution
- BOS + FVG = High probability setup for continuation

## FVG States

FVGs transition through different states based on how price interacts with them:

### 1. UNMITIGATED (Initial State)
- FVG has been created but price hasn't returned to test it yet
- **Most powerful state** - untested institutional imbalance
- Waiting for price to retrace

### 2. REDELIVERED (Partially Filled)
- Price has returned and touched the FVG zone
- Partial fill: Price entered the gap but didn't fully close it
- Often price reacts at C.E. (50%) level and reverses
- **Still valid** for trading if reaction was strong

### 3. REBALANCED (Fully Filled)
- Price has fully closed/filled the FVG gap
- FVG loses its power as an imbalance
- **No longer valid** for trading
- Market has "balanced" the inefficiency

## Trading Strategy with ICT FVGs

### Entry Zones (in order of conservativeness)
1. **Most Conservative**: Wait for Discount level (BULLISH) or Premium level (BEARISH)
2. **Moderate**: Enter at C.E. (50% level)
3. **Aggressive**: Enter anywhere within the FVG zone

### Confirmation Factors
Look for confluence of multiple factors:
- ✅ High Displacement Score (> 1.5x ATR)
- ✅ Break of Structure detected
- ✅ FVG aligns with higher timeframe trend
- ✅ FVG near liquidity pools or session levels
- ✅ Price shows rejection at C.E. or Premium/Discount

### Stop Loss Placement
- **BULLISH FVG**: Below Discount level (with buffer)
- **BEARISH FVG**: Above Premium level (with buffer)
- Buffer typically 2-5 points for NQ

### Profit Targets
- **BULLISH FVG**:
  - First target: C.E. of next opposing FVG
  - Second target: Premium level of current FVG
  - Final target: Previous swing high
- **BEARISH FVG**:
  - First target: C.E. of next opposing FVG
  - Second target: Discount level of current FVG
  - Final target: Previous swing low

### Invalidation Rules
- **BULLISH FVG**: Clean break and **close** below Discount level
- **BEARISH FVG**: Clean break and **close** above Premium level
- One candle wick through the level is acceptable
- Close beyond the level = invalidated

## Database Schema

### Fields in `detected_fvgs` table

```sql
-- Basic FVG Data
fvg_id                  INTEGER (PK)
symbol                  VARCHAR(20)
timeframe               VARCHAR(10)
formation_time          TIMESTAMP WITH TIME ZONE  -- Vela 3's timestamp
fvg_type                VARCHAR(10)               -- BULLISH, BEARISH
fvg_start               DOUBLE                    -- Low boundary
fvg_end                 DOUBLE                    -- High boundary
gap_size                DOUBLE                    -- fvg_end - fvg_start
midpoint                DOUBLE                    -- (start + end) / 2
significance            VARCHAR(10)               -- MICRO, SMALL, MEDIUM, LARGE, EXTREME

-- ICT-Specific Fields
premium_level           DOUBLE                    -- High boundary (entry for bearish, target for bullish)
discount_level          DOUBLE                    -- Low boundary (entry for bullish, target for bearish)
consequent_encroachment DOUBLE                    -- 50% level (primary entry zone)
displacement_score      DOUBLE                    -- gap_size / ATR(14)
has_break_of_structure  BOOLEAN                   -- Simple BOS detection (displacement > 1.5)

-- Status
status                  VARCHAR(20)               -- UNMITIGATED, REDELIVERED, REBALANCED
created_at              TIMESTAMP WITH TIME ZONE
```

### Level Calculations

**BULLISH FVG (BISI)**:
```python
premium_level = fvg_end              # Vela 3 Low (top of gap)
discount_level = fvg_start           # Vela 1 High (bottom of gap)
consequent_encroachment = midpoint   # 50% level
```

**BEARISH FVG (SIBI)**:
```python
premium_level = fvg_start            # Vela 1 Low (top of gap)
discount_level = fvg_end             # Vela 3 High (bottom of gap)
consequent_encroachment = midpoint   # 50% level
```

## Example Use Cases

### High Probability Bullish Setup
```
Scenario: NQZ5, 5min timeframe
- BULLISH FVG detected at 09:35 EST
- Gap Size: 18.75 pts
- Displacement Score: 2.1x ATR ⚡ (strong)
- BOS: YES ⚡
- Discount Level: 20,125.00
- C.E.: 20,134.375
- Premium Level: 20,143.75

Trading Plan:
1. Wait for price to retrace to Discount (20,125.00)
2. Look for bullish reaction (rejection wick, engulfing candle)
3. Enter long at 20,125.50 (just above Discount)
4. Stop Loss: 20,120.00 (5 pts below Discount)
5. Target 1: 20,143.75 (Premium level) = +18.25 pts
6. Target 2: Next resistance or opposing FVG
```

### Medium Probability Bearish Setup
```
Scenario: NQZ5, 5min timeframe
- BEARISH FVG detected at 14:20 EST
- Gap Size: 12.50 pts
- Displacement Score: 1.2x ATR (moderate)
- BOS: NO
- Premium Level: 20,200.00
- C.E.: 20,193.75
- Discount Level: 20,187.50

Trading Plan:
1. More conservative approach (no BOS)
2. Wait for price to reach Premium (20,200.00)
3. Look for strong bearish confirmation
4. Enter short at 20,199.50
5. Stop Loss: 20,205.00 (5 pts above Premium)
6. Target 1: 20,193.75 (C.E.) = +5.75 pts
7. Target 2: 20,187.50 (Discount) = +12 pts
```

## References

- ICT's Inner Circle Trader methodology
- BISI: Buyside Imbalance, Sellside Inefficiency
- SIBI: Sellside Imbalance, Buyside Inefficiency
- Smart Money Concepts (SMC)
- Displacement and Power 3 concepts

## Implementation Notes

### Timezone Handling
- All dates interpreted as **Eastern Time (ET)** for consistency with market hours
- Database stores timestamps in UTC
- `formation_time` converted to ET for display

### Auto-Calibration
- `min_gap_size` auto-calibrated based on timeframe and recent ATR
- Ensures detection is adaptive to market volatility
- See `auto_calibrate_parameters()` in `fvg_detector.py`

### Future Enhancements
- [ ] Advanced BOS detection using swing highs/lows
- [ ] Automatic state transitions (UNMITIGATED → REDELIVERED → REBALANCED)
- [ ] Real-time monitoring of FVG interactions
- [ ] Integration with Liquidity Pools and Order Blocks
- [ ] Multi-timeframe FVG analysis
- [ ] FVG quality scoring based on multiple factors
