# Liquidity Pools - 20 Nov 2025 - NIVELES CRÍTICOS PARA ATAS

**VALIDACIÓN RÁPIDA** - Marcar estos niveles primero

---

## 🎯 PRIORIDAD 1: Session Highs/Lows (CRÍTICOS)

### NY Session (09:30-16:00 ET) - MÁS IMPORTANTES ⭐

```
NYH: 25,310.00  🔴 Buy-Side Liquidity (MÁXIMO DEL DÍA)
NYL: 24,098.00  🟢 Sell-Side Liquidity (MÍNIMO DEL DÍA)
```

**Validar en ATAS:**
- [ ] NYH @ 10:35 ET - Debe ser el pico máximo visible
- [ ] Después de NYH, buscar vela BEARISH grande (Order Block)
- [ ] NYL @ ~16:00 ET - Debe ser el valle mínimo
- [ ] Ver si hubo reversión alcista desde NYL

**SWEEP CONFIRMADO:**
```
10:35 ET - NYH @ 25,310.00
         ↓ Sweep alcista (liquidity grab)
10:35 ET - BEARISH OB formado (25,258.75-25,310.00)
         ↓ Reversión bajista
10:40 ET - Impulso -134.50 pts
         ↓ Continuación
12:00 ET - Llegada a 24,520.00 (-790 pts desde sweep)
```

---

### London Session (03:00-08:00 ET)

```
LSH: 25,185.00  🔴 Buy-Side Liquidity
LSL: 25,022.25  🟢 Sell-Side Liquidity
```

**Validar en ATAS:**
- [ ] LSH debe estar en el rango 03:00-08:00 ET
- [ ] LSL debe estar en el rango 03:00-08:00 ET
- [ ] Ver si fueron respetados o barridos

---

### Asian Session (20:00 prev-02:00 ET)

```
ASH: 25,209.00  🔴 Buy-Side Liquidity
ASL: 25,102.75  🟢 Sell-Side Liquidity
```

**Validar en ATAS:**
- [ ] ASH en período overnight (19 Nov 20:00 - 20 Nov 02:00)
- [ ] Rango pequeño (~106 pts) típico de Asian
- [ ] Ver si fueron barridos en London open

---

## 🔥 PRIORIDAD 2: Triple Highs (Alta Confiabilidad)

### STRONG TRIPLE HIGH #1
```
Nivel:    25,188.75  🟠 (4 toques)
Período:  22:05 - 00:40 ET
Toques:   22:05, 22:50, 23:30, 00:40
Volumen:  1,675 contratos
```

**Validar en ATAS:**
- [ ] Ir a 22:05 ET - Ver swing high cerca de 25,188
- [ ] Ir a 22:50 ET - Ver swing high cerca de 25,188
- [ ] Ir a 23:30 ET - Ver swing high cerca de 25,188
- [ ] Ir a 00:40 ET - Ver swing high cerca de 25,188
- [ ] Confirmar que los 4 highs están dentro de ±5 puntos

### STRONG TRIPLE HIGH #2
```
Nivel:    25,183.13  🟠 (4 toques)
Período:  23:10 - 03:45 ET
Toques:   23:10, 01:00, 01:35, 03:45
Volumen:  2,133 contratos
```

**Validar en ATAS:**
- [ ] Similar al TH #1, verificar los 4 toques
- [ ] Nivel ligeramente más bajo que TH #1 (~5 pts)

---

## ⚖️ PRIORIDAD 3: Equal Highs (Top 3)

### EQH #1
```
Nivel:     25,208.00  🟡
Toque 1:   00:05 ET
Toque 2:   02:30 ET
Diferencia: 2.00 puntos
```

### EQH #2
```
Nivel:     25,189.75  🟡
Toque 1:   22:05 ET
Toque 2:   00:40 ET
Diferencia: 9.00 puntos
```

### EQH #3
```
Nivel:     25,186.25  🟡
Toque 1:   22:50 ET
Toque 2:   00:40 ET
Diferencia: 2.00 puntos
```

**Validar en ATAS:**
- [ ] Ver que hay 2 swing highs al mismo nivel
- [ ] Separación temporal > 1 hora
- [ ] Diferencia ≤ 10 puntos

---

## 📊 Template de Marcado en ATAS

### Colores Sugeridos

**Horizontal Lines:**
```
NYH/NYL:    Rojo/Verde FUERTE (#FF0000 / #00FF00) - Width: 2
LSH/LSL:    Rojo/Verde normal (#CC0000 / #00CC00) - Width: 1
ASH/ASL:    Rojo/Verde claro (#FF6666 / #66FF66) - Width: 1
```

**Rectangles (para Triple/Equal Highs):**
```
Triple Highs:  Naranja (#FFA500) - Altura ±5 puntos
Equal Highs:   Amarillo (#FFFF00) - Altura ±5 puntos
```

**Order Blocks (para comparar):**
```
BEARISH OB:  Azul (#0000FF) - Rectángulo vertical
BULLISH OB:  Cyan (#00FFFF) - Rectángulo vertical
```

---

## 🎯 Checklist de Validación Rápida (15 minutos)

### Paso 1: Cargar Chart
- [ ] Symbol: NQ 12-25 (NQZ5)
- [ ] Timeframe: 5 min
- [ ] Range: 19 Nov 19:00 - 20 Nov 19:00 ET

### Paso 2: Marcar Session Levels (5 min)
- [ ] NYH @ 25,310.00 (línea roja fuerte)
- [ ] NYL @ 24,098.00 (línea verde fuerte)
- [ ] LSH @ 25,185.00
- [ ] LSL @ 25,022.25
- [ ] ASH @ 25,209.00
- [ ] ASL @ 25,102.75

### Paso 3: Validar NYH Sweep (3 min)
- [ ] Ir a 10:35 ET
- [ ] Confirmar sweep de NYH
- [ ] Marcar BEARISH OB después del sweep
- [ ] Ver la caída masiva

### Paso 4: Marcar Triple Highs (5 min)
- [ ] TH @ 25,188.75 (rectángulo naranja)
- [ ] TH @ 25,183.13 (rectángulo naranja)
- [ ] Verificar toques en cada timestamp

### Paso 5: (Opcional) Equal Highs (2 min)
- [ ] EQH @ 25,208.00
- [ ] EQH @ 25,189.75
- [ ] EQH @ 25,186.25

---

## 💡 Qué Esperar Ver

### En NYH (25,310.00) @ 10:35 ET
```
Antes:  Precio sube hacia 25,310
10:35:  Vela alcista rompe 25,310 (SWEEP) 🔥
10:35:  Vela BEARISH grande (ORDER BLOCK) 📦
10:40+: Caída masiva (-134 pts inmediato)
```

### En Triple Highs (25,188.75)
```
22:05:  High toca ~25,188 ✓
22:50:  High toca ~25,188 ✓
23:30:  High toca ~25,188 ✓
00:40:  High toca ~25,188 ✓
→ 4 toques = STRONG LP
→ ¿Fue barrido después? (buscar sweep)
```

### En Session Lows
```
NYL @ 24,098.00:
- Debe ser el punto MÁS BAJO del gráfico
- Buscar reversión alcista (BULLISH OB)
- Ver si fue respetado o penetrado
```

---

## ⚠️ Notas Importantes

1. **Tolerancia de Precios**:
   - Los niveles pueden variar ±2-3 puntos por spread/slippage
   - Si ves el nivel a 25,308 en lugar de 25,310 = OK

2. **Timestamps en ET**:
   - ATAS debe estar configurado en Eastern Time
   - Si usas UTC, suma/resta según corresponda

3. **Session Boundaries**:
   - Asian: 20:00 (día anterior) - 02:00
   - London: 03:00 - 08:00
   - NY: 09:30 - 16:00

4. **Swept vs Respected**:
   - **Swept**: Precio rompe +5 pts arriba/abajo del LP
   - **Respected**: Precio toca pero reversa inmediatamente

---

## 📸 Screenshot Checklist

Después de marcar todo, toma screenshots de:

- [ ] Vista completa del día con todos los session levels
- [ ] Zoom en NYH sweep @ 10:35 ET
- [ ] Zoom en Triple High #1 mostrando los 4 toques
- [ ] Zoom en NYL @ 16:00 ET

---

**Generado**: 2025-11-30
**Datos**: NQZ5 - 20 Noviembre 2025
**Propósito**: Validación rápida de Liquidity Pools en ATAS

