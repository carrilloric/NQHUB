# Order Blocks Sample - 23 de Noviembre 2025 (Sábado)

## ⚠️ IMPORTANTE: NO HAY DATOS DISPONIBLES

### Razón: Mercado Cerrado

El mercado de futuros del NQ (Nasdaq-100 E-mini) **NO opera los sábados**.

## Horario de Trading de NQ Futures

### Horario Regular (CME Globex)

| Día | Apertura | Cierre | Estado |
|-----|----------|--------|---------|
| **Domingo** | 6:00 PM ET | - | ✅ Abierto |
| **Lunes** | - | 5:00 PM ET | ✅ Abierto |
| **Martes** | 6:00 PM ET (del lunes) | 5:00 PM ET | ✅ Abierto |
| **Miércoles** | 6:00 PM ET (del martes) | 5:00 PM ET | ✅ Abierto |
| **Jueves** | 6:00 PM ET (del miércoles) | 5:00 PM ET | ✅ Abierto |
| **Viernes** | 6:00 PM ET (del jueves) | 5:00 PM ET | ✅ Abierto |
| **Sábado** | - | - | ❌ CERRADO |

### Pausas Diarias
- **Pausa diaria**: 5:00 PM - 6:00 PM ET (lunes a viernes)
- **Fin de semana**: Cierra viernes 5:00 PM ET, reabre domingo 6:00 PM ET

## Implicaciones para el Análisis

### 1. Períodos Sin Datos
- **Sábado completo**: Sin datos
- **Domingo antes de 6:00 PM ET**: Sin datos
- **Lunes-Viernes 5:00-6:00 PM ET**: Sin datos (pausa diaria)

### 2. Períodos de Mayor Interés para Order Blocks

#### Domingo (6:00 PM ET en adelante)
- **Características**: Volumen bajo, apertura semanal
- **Relevancia**: OBs frecuentemente respetados el lunes
- **Ejemplo**: Ver `OB_24NOV_SAMPLE.md` (domingo)

#### Lunes-Viernes
- **Pre-market** (4:00-9:30 AM ET): Volumen moderado
- **RTH** (9:30 AM-4:00 PM ET): Mayor volumen y liquidez
- **Post-market** (4:00-5:00 PM ET): Volumen decreciente

## Alternativas para Análisis del Fin de Semana

Si necesitas analizar Order Blocks del fin de semana, considera:

1. **Domingo por la tarde/noche** (después de 6:00 PM ET)
   - Primera sesión de la semana
   - Gaps frecuentes desde el cierre del viernes

2. **Viernes por la tarde** (antes de 5:00 PM ET)
   - Última sesión antes del fin de semana
   - Posicionamiento para el fin de semana

## Recomendación

Para un análisis completo de Order Blocks con datos reales, sugerimos:

1. **Período óptimo**: Lunes a Viernes, 9:30 AM - 4:00 PM ET (RTH)
2. **Período alternativo**: Domingo 6:00 PM - 11:00 PM ET (apertura semanal)
3. **Evitar**: Sábados y domingos antes de 6:00 PM ET

## Ejemplo de Comando para Período Válido

```python
# Ejemplo: Analizar viernes 22 de noviembre, sesión RTH
start_time = '2025-11-22 14:30:00'  # 9:30 AM ET en UTC
end_time = '2025-11-22 21:00:00'    # 4:00 PM ET en UTC

# O analizar domingo 24 de noviembre, apertura
start_time = '2025-11-24 23:00:00'  # 6:00 PM ET en UTC
end_time = '2025-11-25 04:00:00'    # 11:00 PM ET en UTC
```

---

*Documento generado: 2025-11-30 10:09:00*

*Nota: Los futuros del NQ siguen el calendario de CME Globex*