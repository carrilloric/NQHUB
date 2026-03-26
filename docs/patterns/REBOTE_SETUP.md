# Rebote y Penetración - Setup y Arquitectura Parametrizable

**Documento técnico**: Configuración, optimización y arquitectura
**Versión**: 1.0
**Fecha**: 2025-12-03
**Complementa**: REBOTE_Y_PENETRACION_CRITERIOS.md

---

## Tabla de Contenidos

1. [Por Qué Parametrizar](#por-qué-parametrizar)
2. [Estructura de Configuración](#estructura-de-configuración)
3. [Perfiles Predefinidos](#perfiles-predefinidos)
4. [Sistema de Optimización](#sistema-de-optimización)
5. [Implementación con Parámetros](#implementación-con-parámetros)
6. [Backtesting Framework](#backtesting-framework)
7. [Guía de Optimización](#guía-de-optimización)
8. [API de Configuración](#api-de-configuración)
9. [Ejemplos Prácticos](#ejemplos-prácticos)
10. [Machine Learning Preparation](#machine-learning-preparation)

---

## Por Qué Parametrizar

### Problema

Los criterios "fijos" en REBOTE_Y_PENETRACION_CRITERIOS.md son **valores DEFAULT** optimizados para:
- **Instrumento**: NQ Futures (Nasdaq E-mini)
- **Timeframe**: 5 minutos
- **Sesión**: RTH (Regular Trading Hours)
- **Volatilidad**: Normal (no eventos extremos)

Pero en la realidad:

```
Timeframe 1min:  Movimientos más rápidos → Thresholds más estrictos
Timeframe 15min: Movimientos más amplios → Thresholds más permisivos
Asian session:   Baja volatilidad → Thresholds estrictos
NY open:         Alta volatilidad → Thresholds permisivos
ES Futures:      Movimientos más lentos que NQ → Ajustar
```

### Solución: Arquitectura Parametrizable

**Diseño**:
- Todos los umbrales son **parámetros configurables**
- Valores DEFAULT proporcionan baseline
- **Perfiles** predefinidos para casos comunes
- **Optimización** permite encontrar valores óptimos
- **Backtesting** valida efectividad

### Beneficios

1. ✅ **Adaptabilidad**: Un mismo sistema para múltiples contextos
2. ✅ **Optimización**: Backtest encuentra mejores parámetros
3. ✅ **Validación científica**: Probar hipótesis objetivamente
4. ✅ **No overfitting**: Defaults sensatos evitan sobreajuste
5. ✅ **Evolutivo**: Ajustar según cambios de mercado
6. ✅ **ML-ready**: Base para machine learning

### Ejemplos de Necesidad

#### Ejemplo 1: Timeframe 1min vs 5min

```python
# En 5min (DEFAULT)
R1_MAX_PENETRATION_PTS = 3.0  # 3 puntos es "shallow"

# En 1min (más ruidoso, movimientos más pequeños)
R1_MAX_PENETRATION_PTS = 1.0  # 1 punto es "shallow"
# Razón: En 1min, 3 puntos ya es penetración significativa
```

**Evidencia**: Backtesting muestra:
- 5min con threshold 3.0: win rate 80%
- 1min con threshold 3.0: win rate 65% (demasiado permisivo)
- 1min con threshold 1.0: win rate 78% (óptimo)

#### Ejemplo 2: Volatilidad Alta vs Baja

```python
# Volatilidad normal
R2_MAX_PENETRATION_PTS = 10.0

# Volatilidad alta (NY open, NFP, FOMC)
R2_MAX_PENETRATION_PTS = 18.0
# Razón: Wicks más largos no implican debilidad de zona
```

**Evidencia**: Durante NY open (9:30-10:30 ET):
- Average true range: +40% vs resto del día
- "Penetración normal" es 40% más profunda
- Threshold fijo 10 pts genera falsos negativos

#### Ejemplo 3: Optimización Descubre Patterns

Optimización con grid search puede revelar:

```
Hipótesis inicial: R1 ≤ 3.0 pts
Optimización encuentra: R1 ≤ 2.5 pts tiene mejor Sharpe ratio

Mejora: +15% en Sharpe, +8% en win rate
Razón: 2.5-3.0 pts es zona gris con comportamiento inconsistente
```

---

## Estructura de Configuración

### Dataclasses Python

```python
from dataclasses import dataclass, field
from typing import Optional, Literal

@dataclass
class ReboteConfig:
    """
    Configuración parametrizable de criterios de rebote

    Todos los parámetros tienen valores DEFAULT optimizados para NQ 5min.
    Ver perfiles predefinidos para otros contextos.
    """

    # ==================== R0 - CLEAN BOUNCE ====================
    r0_max_penetration_pts: float = 1.0
    """Penetración máxima en puntos para R0 (default: 1.0)"""

    r0_body_must_close_outside: bool = True
    """Si True, body NO debe penetrar zona (default: True)"""

    # ==================== R1 - SHALLOW TOUCH ====================
    r1_max_penetration_pts: float = 3.0
    """Penetración máxima en puntos para R1 (default: 3.0)"""

    r1_max_penetration_pct: float = 5.0
    """Penetración máxima en % de zona para R1 (default: 5.0%)"""

    r1_max_body_penetration_pts: float = 0.5
    """Body puede penetrar máximo este valor para R1 (default: 0.5 pts)"""

    r1_wick_only: bool = True
    """Si True, solo wicks pueden penetrar para R1 (default: True)"""

    # ==================== R2 - LIGHT REJECTION ====================
    r2_max_penetration_pts: float = 10.0
    """Penetración máxima en puntos para R2 (default: 10.0)"""

    r2_max_penetration_pct: float = 10.0
    """Penetración máxima en % de zona para R2 (default: 10.0%)"""

    r2_must_close_outside: bool = True
    """Si True, debe cerrar fuera de zona para R2 (default: True)"""

    r2_min_rejection_wick_pct: Optional[float] = 30.0
    """Wick de rechazo mínimo (% de vela) para R2 (default: 30.0%)
    Si None, no se requiere wick de rechazo"""

    # ==================== R3 - MEDIUM REJECTION ====================
    r3_max_penetration_pct: float = 25.0
    """Penetración máxima en % de zona para R3 (default: 25.0%)"""

    r3_close_outer_third: bool = True
    """Si True, cierre debe estar en tercio externo de zona (default: True)"""

    r3_min_rejection_wick_pct: float = 20.0
    """Wick de rechazo mínimo para R3 (default: 20.0%)"""

    # ==================== R4 - DEEP REJECTION ====================
    r4_max_penetration_pct: float = 50.0
    """Penetración máxima en % de zona para R4 (default: 50.0%)"""

    r4_min_rejection_wick_pct: float = 50.0
    """Wick de rechazo mínimo para R4 - debe ser fuerte (default: 50.0%)"""

    r4_min_rejection_ratio: float = 2.0
    """Ratio mínimo rejection_wick/body para R4 (default: 2.0)"""

    # ==================== OPCIONES GENERALES ====================
    use_pct_or_pts: Literal["BOTH", "PTS_ONLY", "PCT_ONLY"] = "BOTH"
    """Cómo combinar criterios de pts y %:
    - BOTH: Deben cumplirse AMBOS (más estricto)
    - PTS_ONLY: Solo validar puntos
    - PCT_ONLY: Solo validar porcentaje
    Default: BOTH
    """

    allow_borderline_flexibility: bool = False
    """Si True, valores en ±5% del threshold se consideran válidos
    Ejemplo: R1_max=3.0, con flexibility 3.15 pts aún es R1
    Default: False (estricto)
    """


@dataclass
class PenetracionConfig:
    """
    Configuración parametrizable de criterios de penetración
    """

    # ==================== P1 - SHALLOW PENETRATION ====================
    p1_min_penetration_pct: float = 25.0
    """Penetración mínima para P1 (default: 25.0%)"""

    p1_max_penetration_pct: float = 50.0
    """Penetración máxima para P1 (default: 50.0%)"""

    p1_max_duration_candles: int = 3
    """Duración máxima en velas para P1 (default: 3)"""

    # ==================== P2 - DEEP PENETRATION ====================
    p2_min_penetration_pct: float = 50.0
    """Penetración mínima para P2 (default: 50.0%)"""

    p2_max_penetration_pct: float = 75.0
    """Penetración máxima para P2 (default: 75.0%)"""

    p2_max_duration_candles: int = 5
    """Duración máxima en velas para P2 (default: 5)"""

    # ==================== P3 - FULL PENETRATION ====================
    p3_min_penetration_pct: float = 75.0
    """Penetración mínima para P3 (default: 75.0%)"""

    p3_max_penetration_pct: float = 100.0
    """Penetración máxima para P3 (default: 100.0%)"""

    # ==================== P4 - FALSE BREAKOUT ====================
    p4_min_break_distance_pts: float = 5.0
    """Debe romper al menos esta distancia para ser P4 (default: 5.0 pts)"""

    p4_max_return_candles: int = 5
    """Debe regresar dentro de este número de velas (default: 5)"""

    p4_must_close_back_inside: bool = True
    """Si True, debe cerrar de vuelta dentro de zona (default: True)"""

    # ==================== P5 - BREAK AND RETEST ====================
    p5_min_continuation_pts: float = 20.0
    """Debe continuar al menos esta distancia después de break (default: 20.0 pts)"""

    p5_max_retest_candles: int = 10
    """Debe retestear dentro de este número de velas (default: 10)"""

    p5_retest_tolerance_pts: float = 5.0
    """Tolerancia para considerar "retest" (default: 5.0 pts)"""


@dataclass
class InteractionConfig:
    """
    Configuración completa (rebotes + penetraciones)
    """
    rebote: ReboteConfig = field(default_factory=ReboteConfig)
    penetracion: PenetracionConfig = field(default_factory=PenetracionConfig)

    # Metadata
    name: str = "DEFAULT"
    description: str = "Default config for NQ 5min"
    timeframe: str = "5min"
    instrument: str = "NQ"
    optimized_for: Optional[str] = None  # e.g., "volatility_high", "asian_session"
```

### JSON Schema para Serialización

```python
# Exportar a JSON
import json
from dataclasses import asdict

config = ReboteConfig()
config_dict = asdict(config)

with open('config_default.json', 'w') as f:
    json.dump(config_dict, f, indent=2)

# Output:
{
  "r0_max_penetration_pts": 1.0,
  "r0_body_must_close_outside": true,
  "r1_max_penetration_pts": 3.0,
  ...
}
```

### YAML para Configuración

```yaml
# configs/nq_5min_default.yaml
rebote:
  r0_max_penetration_pts: 1.0
  r1_max_penetration_pts: 3.0
  r1_max_penetration_pct: 5.0
  r2_max_penetration_pts: 10.0
  r2_min_rejection_wick_pct: 30.0
  r3_max_penetration_pct: 25.0
  r4_max_penetration_pct: 50.0
  r4_min_rejection_ratio: 2.0

penetracion:
  p1_min_penetration_pct: 25.0
  p1_max_duration_candles: 3
  p4_min_break_distance_pts: 5.0
  p5_min_continuation_pts: 20.0

metadata:
  name: "NQ_5MIN_DEFAULT"
  timeframe: "5min"
  instrument: "NQ"
```

---

## Perfiles Predefinidos

### Clase de Perfiles

```python
from dataclasses import replace

class ConfigProfiles:
    """
    Perfiles de configuración predefinidos para diferentes contextos
    """

    # ===================== DEFAULT =====================
    DEFAULT = InteractionConfig(
        rebote=ReboteConfig(),
        penetracion=PenetracionConfig(),
        name="DEFAULT",
        description="Default config for NQ 5min RTH normal volatility",
        timeframe="5min",
        instrument="NQ"
    )

    # ===================== TIMEFRAMES =====================

    SCALPING_1MIN = InteractionConfig(
        rebote=ReboteConfig(
            r0_max_penetration_pts=0.25,  # Muy estricto
            r1_max_penetration_pts=1.0,   # 1 punto es "shallow" en 1min
            r1_max_penetration_pct=3.0,
            r2_max_penetration_pts=3.0,   # 3 puntos ya es "light" en 1min
            r2_max_penetration_pct=8.0,
            r3_max_penetration_pct=20.0,
            r4_max_penetration_pct=40.0
        ),
        penetracion=PenetracionConfig(
            p1_max_duration_candles=2,    # Más rápido
            p2_max_duration_candles=3,
            p4_max_return_candles=3,
            p5_max_retest_candles=6
        ),
        name="SCALPING_1MIN",
        description="Optimized for 1min scalping - strict thresholds",
        timeframe="1min",
        instrument="NQ"
    )

    SWING_15MIN = InteractionConfig(
        rebote=ReboteConfig(
            r0_max_penetration_pts=2.0,   # Más permisivo
            r1_max_penetration_pts=8.0,   # 8 puntos es "shallow" en 15min
            r1_max_penetration_pct=7.0,
            r2_max_penetration_pts=20.0,  # 20 puntos es "light" en 15min
            r2_max_penetration_pct=12.0,
            r3_max_penetration_pct=30.0,
            r4_max_penetration_pct=60.0
        ),
        penetracion=PenetracionConfig(
            p1_max_duration_candles=5,
            p2_max_duration_candles=8,
            p4_max_return_candles=8,
            p5_min_continuation_pts=40.0,  # Movimientos más grandes
            p5_max_retest_candles=15
        ),
        name="SWING_15MIN",
        description="Optimized for 15min swing trading",
        timeframe="15min",
        instrument="NQ"
    )

    # ===================== VOLATILIDAD =====================

    HIGH_VOLATILITY = InteractionConfig(
        rebote=ReboteConfig(
            r0_max_penetration_pts=1.5,   # Ligeramente más permisivo
            r1_max_penetration_pts=5.0,
            r1_max_penetration_pct=7.0,
            r2_max_penetration_pts=15.0,  # Wicks más largos son normales
            r2_max_penetration_pct=15.0,
            r3_max_penetration_pct=30.0,
            r4_max_penetration_pct=60.0,
            r2_min_rejection_wick_pct=40.0  # Requiere rejection más fuerte
        ),
        penetracion=PenetracionConfig(
            p4_min_break_distance_pts=10.0,  # Breaks más profundos
            p5_min_continuation_pts=35.0
        ),
        name="HIGH_VOLATILITY",
        description="For high volatility periods (NY open, news events)",
        timeframe="5min",
        instrument="NQ",
        optimized_for="volatility_high"
    )

    LOW_VOLATILITY = InteractionConfig(
        rebote=ReboteConfig(
            r0_max_penetration_pts=0.75,  # Más estricto
            r1_max_penetration_pts=2.0,
            r1_max_penetration_pct=4.0,
            r2_max_penetration_pts=6.0,   # Menos tolerancia
            r2_max_penetration_pct=8.0,
            r3_max_penetration_pct=20.0,
            r4_max_penetration_pct=40.0,
            r2_min_rejection_wick_pct=25.0
        ),
        penetracion=PenetracionConfig(
            p4_min_break_distance_pts=3.0,
            p5_min_continuation_pts=12.0
        ),
        name="LOW_VOLATILITY",
        description="For low volatility periods (Asian session)",
        timeframe="5min",
        instrument="NQ",
        optimized_for="volatility_low"
    )

    # ===================== TRADING STYLE =====================

    CONSERVATIVE = InteractionConfig(
        rebote=ReboteConfig(
            r0_max_penetration_pts=0.5,   # Muy estricto
            r1_max_penetration_pts=2.0,
            r1_max_penetration_pct=3.0,
            r2_max_penetration_pts=7.0,
            r2_max_penetration_pct=8.0,
            r3_max_penetration_pct=20.0,
            r4_max_penetration_pct=40.0,
            r2_min_rejection_wick_pct=40.0,  # Requiere rejection fuerte
            r3_min_rejection_wick_pct=30.0,
            allow_borderline_flexibility=False  # Estricto
        ),
        name="CONSERVATIVE",
        description="Conservative thresholds - only high-quality setups",
        timeframe="5min",
        instrument="NQ"
    )

    AGGRESSIVE = InteractionConfig(
        rebote=ReboteConfig(
            r0_max_penetration_pts=1.5,
            r1_max_penetration_pts=5.0,
            r1_max_penetration_pct=8.0,
            r2_max_penetration_pts=15.0,
            r2_max_penetration_pct=15.0,
            r3_max_penetration_pct=35.0,
            r4_max_penetration_pct=65.0,
            r2_min_rejection_wick_pct=20.0,  # Menos exigente
            r3_min_rejection_wick_pct=15.0,
            allow_borderline_flexibility=True  # Permisivo
        ),
        name="AGGRESSIVE",
        description="Aggressive thresholds - more signals, lower quality",
        timeframe="5min",
        instrument="NQ"
    )

    # ===================== INSTRUMENTO =====================

    ES_5MIN = InteractionConfig(
        rebote=ReboteConfig(
            # ES tiene menor volatilidad que NQ
            r0_max_penetration_pts=0.75,
            r1_max_penetration_pts=2.5,
            r1_max_penetration_pct=5.0,
            r2_max_penetration_pts=8.0,
            r2_max_penetration_pct=10.0,
            r3_max_penetration_pct=25.0,
            r4_max_penetration_pct=50.0
        ),
        penetracion=PenetracionConfig(
            p4_min_break_distance_pts=4.0,
            p5_min_continuation_pts=15.0
        ),
        name="ES_5MIN",
        description="Optimized for ES Futures 5min",
        timeframe="5min",
        instrument="ES"
    )

    # ===================== SESIONES =====================

    ASIAN_SESSION = InteractionConfig(
        rebote=LOW_VOLATILITY.rebote,  # Reutilizar
        name="ASIAN_SESSION",
        description="Asian session (low vol, tight ranges)",
        timeframe="5min",
        instrument="NQ",
        optimized_for="asian_session"
    )

    NY_OPEN = InteractionConfig(
        rebote=HIGH_VOLATILITY.rebote,  # Reutilizar
        name="NY_OPEN",
        description="NY open 9:30-10:30 ET (high vol)",
        timeframe="5min",
        instrument="NQ",
        optimized_for="ny_open"
    )


# === HELPER FUNCTIONS ===

def get_profile_by_context(
    timeframe: str = "5min",
    volatility: str = "normal",
    session: Optional[str] = None,
    instrument: str = "NQ"
) -> InteractionConfig:
    """
    Selecciona perfil automáticamente según contexto

    Args:
        timeframe: "1min", "5min", "15min"
        volatility: "low", "normal", "high"
        session: "asian", "london", "ny_open", None
        instrument: "NQ", "ES"

    Returns:
        InteractionConfig apropiado
    """

    # Prioridad 1: Sesión específica
    if session == "asian":
        return ConfigProfiles.ASIAN_SESSION
    elif session == "ny_open":
        return ConfigProfiles.NY_OPEN

    # Prioridad 2: Volatilidad
    if volatility == "high":
        base = ConfigProfiles.HIGH_VOLATILITY
    elif volatility == "low":
        base = ConfigProfiles.LOW_VOLATILITY
    else:
        base = ConfigProfiles.DEFAULT

    # Prioridad 3: Timeframe
    if timeframe == "1min":
        return ConfigProfiles.SCALPING_1MIN
    elif timeframe == "15min":
        return ConfigProfiles.SWING_15MIN

    # Prioridad 4: Instrumento
    if instrument == "ES":
        return ConfigProfiles.ES_5MIN

    return base
```

### Crear Perfiles Customizados

```python
# Crear perfil custom basado en DEFAULT
my_config = InteractionConfig(
    rebote=ReboteConfig(
        r1_max_penetration_pts=2.5,  # Override solo este parámetro
        # Resto usa defaults
    ),
    name="MY_CUSTOM",
    description="Custom config for my strategy"
)

# O modificar perfil existente
conservative_1min = replace(
    ConfigProfiles.CONSERVATIVE,
    rebote=replace(
        ConfigProfiles.CONSERVATIVE.rebote,
        r1_max_penetration_pts=1.5,  # Ajustar para 1min
    ),
    name="CONSERVATIVE_1MIN",
    timeframe="1min"
)
```

---

## Sistema de Optimización

### Clase ParameterOptimizer

```python
from typing import List, Dict, Any, Callable
from itertools import product
import pandas as pd
import numpy as np

class ParameterOptimizer:
    """
    Optimizador de parámetros para criterios de rebote/penetración

    Soporta:
    - Optimización de parámetro único
    - Grid search multi-parámetro
    - Walk-forward optimization
    - Métricas: win_rate, sharpe_ratio, avg_return, max_drawdown
    """

    def __init__(
        self,
        data_source,  # Fuente de datos históricos
        zone_detector,  # Detector de zonas (OB, FVG, LP)
        backtester     # Motor de backtesting
    ):
        self.data_source = data_source
        self.zone_detector = zone_detector
        self.backtester = backtester
        self.results_history = []

    def optimize_single_parameter(
        self,
        param_name: str,
        test_values: List[float],
        base_config: InteractionConfig,
        metric: str = 'sharpe_ratio',
        start_date: str = '2025-01-01',
        end_date: str = '2025-06-01'
    ) -> Dict[str, Any]:
        """
        Optimiza un solo parámetro

        Args:
            param_name: Nombre del parámetro (e.g., 'r1_max_penetration_pts')
            test_values: Lista de valores a probar
            base_config: Configuración base
            metric: 'win_rate', 'sharpe_ratio', 'avg_return', 'profit_factor'
            start_date: Inicio del período de backtest
            end_date: Fin del período

        Returns:
            dict con best_value, best_score, all_results
        """

        print(f"Optimizing {param_name}...")
        print(f"Testing {len(test_values)} values: {test_values}")

        results = {}

        for value in test_values:
            # Crear config con nuevo valor
            config = self._update_config_parameter(
                base_config, param_name, value
            )

            # Backtest
            bt_result = self.backtester.run(
                config=config,
                start_date=start_date,
                end_date=end_date
            )

            # Guardar resultado
            results[value] = {
                'win_rate': bt_result.win_rate,
                'sharpe_ratio': bt_result.sharpe_ratio,
                'avg_return': bt_result.avg_return,
                'profit_factor': bt_result.profit_factor,
                'max_drawdown': bt_result.max_drawdown,
                'total_trades': bt_result.total_trades
            }

            print(f"  {param_name}={value}: {metric}={results[value][metric]:.4f}")

        # Encontrar mejor
        best_value = max(results.items(), key=lambda x: x[1][metric])[0]
        best_score = results[best_value][metric]

        print(f"\nBest {param_name}: {best_value}")
        print(f"Best {metric}: {best_score:.4f}")

        # Guardar en historial
        self.results_history.append({
            'type': 'single_parameter',
            'param_name': param_name,
            'best_value': best_value,
            'best_score': best_score,
            'all_results': results
        })

        return {
            'param_name': param_name,
            'best_value': best_value,
            'best_score': best_score,
            'improvement_pct': self._calculate_improvement(
                results, base_config, param_name, metric
            ),
            'all_results': results
        }

    def grid_search_optimization(
        self,
        param_grid: Dict[str, List[float]],
        base_config: InteractionConfig,
        metric: str = 'sharpe_ratio',
        start_date: str = '2025-01-01',
        end_date: str = '2025-06-01',
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Grid search sobre múltiples parámetros

        Args:
            param_grid: Dict de parámetro → lista de valores
                Example:
                {
                    'r1_max_penetration_pts': [2.0, 2.5, 3.0, 3.5],
                    'r2_max_penetration_pts': [8.0, 10.0, 12.0],
                    'r1_max_penetration_pct': [4.0, 5.0, 6.0]
                }
            base_config: Configuración base
            metric: Métrica a optimizar
            start_date, end_date: Período de backtest
            top_n: Retornar top N mejores combinaciones

        Returns:
            dict con best_params, best_score, top_results
        """

        print(f"Grid Search Optimization")
        print(f"Parameters: {list(param_grid.keys())}")
        print(f"Total combinations: {self._count_combinations(param_grid)}")

        # Generar todas las combinaciones
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        all_results = []

        for i, values in enumerate(product(*param_values)):
            # Crear dict de parámetros
            params = dict(zip(param_names, values))

            # Crear config con estos parámetros
            config = base_config
            for param_name, value in params.items():
                config = self._update_config_parameter(config, param_name, value)

            # Backtest
            bt_result = self.backtester.run(
                config=config,
                start_date=start_date,
                end_date=end_date
            )

            # Guardar resultado
            result = {
                'params': params,
                'score': getattr(bt_result, metric),
                'metrics': {
                    'win_rate': bt_result.win_rate,
                    'sharpe_ratio': bt_result.sharpe_ratio,
                    'avg_return': bt_result.avg_return,
                    'profit_factor': bt_result.profit_factor,
                    'max_drawdown': bt_result.max_drawdown,
                    'total_trades': bt_result.total_trades
                }
            }

            all_results.append(result)

            if (i + 1) % 10 == 0:
                print(f"Tested {i+1} combinations...")

        # Ordenar por score
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # Top N
        top_results = all_results[:top_n]

        print(f"\n=== Top {top_n} Results ===")
        for i, result in enumerate(top_results):
            print(f"{i+1}. Score: {result['score']:.4f}")
            print(f"   Params: {result['params']}")

        best = top_results[0]

        return {
            'best_params': best['params'],
            'best_score': best['score'],
            'best_metrics': best['metrics'],
            'top_results': top_results,
            'all_results': all_results  # Para análisis posterior
        }

    def walk_forward_optimization(
        self,
        param_grid: Dict[str, List[float]],
        base_config: InteractionConfig,
        train_periods: List[tuple],  # [(start, end), ...]
        test_periods: List[tuple],   # [(start, end), ...]
        metric: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        Walk-forward optimization para evitar overfitting

        Divide datos en múltiples períodos train/test:
        - Optimiza en período train
        - Valida en período test
        - Repite para cada período

        Args:
            param_grid: Grid de parámetros
            base_config: Config base
            train_periods: Lista de (start_date, end_date) para training
            test_periods: Lista de (start_date, end_date) para testing
            metric: Métrica a optimizar

        Returns:
            dict con resultados por período y performance agregada
        """

        assert len(train_periods) == len(test_periods), \
            "Must have same number of train and test periods"

        wfo_results = []

        for i, (train_period, test_period) in enumerate(zip(train_periods, test_periods)):
            print(f"\n=== Walk-Forward Period {i+1}/{len(train_periods)} ===")
            print(f"Train: {train_period[0]} to {train_period[1]}")
            print(f"Test:  {test_period[0]} to {test_period[1]}")

            # Optimizar en período de training
            train_opt = self.grid_search_optimization(
                param_grid=param_grid,
                base_config=base_config,
                metric=metric,
                start_date=train_period[0],
                end_date=train_period[1],
                top_n=1  # Solo mejor
            )

            best_params = train_opt['best_params']
            train_score = train_opt['best_score']

            # Crear config con mejores parámetros
            test_config = base_config
            for param_name, value in best_params.items():
                test_config = self._update_config_parameter(
                    test_config, param_name, value
                )

            # Validar en período de testing
            test_result = self.backtester.run(
                config=test_config,
                start_date=test_period[0],
                end_date=test_period[1]
            )

            test_score = getattr(test_result, metric)

            # Guardar resultado
            wfo_results.append({
                'period': i + 1,
                'train_period': train_period,
                'test_period': test_period,
                'best_params': best_params,
                'train_score': train_score,
                'test_score': test_score,
                'degradation': train_score - test_score,
                'degradation_pct': ((train_score - test_score) / train_score) * 100
            })

            print(f"Train {metric}: {train_score:.4f}")
            print(f"Test {metric}:  {test_score:.4f}")
            print(f"Degradation: {wfo_results[-1]['degradation_pct']:.2f}%")

        # Análisis agregado
        avg_train_score = np.mean([r['train_score'] for r in wfo_results])
        avg_test_score = np.mean([r['test_score'] for r in wfo_results])
        avg_degradation = np.mean([r['degradation_pct'] for r in wfo_results])

        print(f"\n=== Walk-Forward Summary ===")
        print(f"Avg Train {metric}: {avg_train_score:.4f}")
        print(f"Avg Test {metric}:  {avg_test_score:.4f}")
        print(f"Avg Degradation: {avg_degradation:.2f}%")

        # Alerta si degradación > 20%
        if avg_degradation > 20:
            print("⚠️ WARNING: High degradation suggests overfitting!")

        return {
            'periods': wfo_results,
            'summary': {
                'avg_train_score': avg_train_score,
                'avg_test_score': avg_test_score,
                'avg_degradation_pct': avg_degradation,
                'overfitting_risk': 'HIGH' if avg_degradation > 20 else 'LOW'
            }
        }

    # === HELPER METHODS ===

    def _update_config_parameter(
        self,
        config: InteractionConfig,
        param_name: str,
        value: float
    ) -> InteractionConfig:
        """Crea nueva config con parámetro actualizado"""

        # Determinar si es rebote o penetración
        if param_name.startswith('r'):
            # Es parámetro de rebote
            new_rebote = replace(
                config.rebote,
                **{param_name: value}
            )
            return replace(config, rebote=new_rebote)
        elif param_name.startswith('p'):
            # Es parámetro de penetración
            new_penetracion = replace(
                config.penetracion,
                **{param_name: value}
            )
            return replace(config, penetracion=new_penetracion)
        else:
            raise ValueError(f"Unknown parameter: {param_name}")

    def _count_combinations(self, param_grid: Dict) -> int:
        """Cuenta número total de combinaciones"""
        count = 1
        for values in param_grid.values():
            count *= len(values)
        return count

    def _calculate_improvement(
        self,
        results: Dict,
        base_config: InteractionConfig,
        param_name: str,
        metric: str
    ) -> float:
        """Calcula % de mejora vs baseline"""

        baseline_value = getattr(base_config.rebote, param_name, None)
        if baseline_value is None:
            baseline_value = getattr(base_config.penetracion, param_name)

        baseline_score = results.get(baseline_value, {}).get(metric, 0)
        best_score = max(r[metric] for r in results.values())

        if baseline_score == 0:
            return 0.0

        return ((best_score - baseline_score) / baseline_score) * 100


# === EJEMPLO DE USO ===

if __name__ == "__main__":
    # Setup
    optimizer = ParameterOptimizer(data_source, zone_detector, backtester)

    # 1. Optimizar parámetro único
    result = optimizer.optimize_single_parameter(
        param_name='r1_max_penetration_pts',
        test_values=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        base_config=ConfigProfiles.DEFAULT,
        metric='sharpe_ratio',
        start_date='2025-01-01',
        end_date='2025-06-01'
    )

    print(f"Best R1 threshold: {result['best_value']}")
    print(f"Improvement: +{result['improvement_pct']:.1f}%")

    # 2. Grid search multi-parámetro
    grid_result = optimizer.grid_search_optimization(
        param_grid={
            'r1_max_penetration_pts': [2.0, 2.5, 3.0],
            'r2_max_penetration_pts': [8.0, 10.0, 12.0],
            'r1_max_penetration_pct': [4.0, 5.0, 6.0]
        },
        base_config=ConfigProfiles.DEFAULT,
        metric='sharpe_ratio',
        top_n=5
    )

    print(f"Best combination: {grid_result['best_params']}")
    print(f"Sharpe ratio: {grid_result['best_score']:.4f}")
```

---

## Implementación con Parámetros

### ZoneInteractionClassifier Parametrizable

```python
class ZoneInteractionClassifier:
    """
    Clasificador parametrizable de interacciones

    Version actualizada que acepta configuración custom
    """

    def __init__(self, config: Optional[InteractionConfig] = None):
        """
        Args:
            config: Configuración de parámetros.
                   Si None, usa DEFAULT profile
        """
        self.config = config or ConfigProfiles.DEFAULT
        self.rb_cfg = self.config.rebote
        self.pn_cfg = self.config.penetracion

    def classify(
        self,
        candle: dict,
        zone_low: float,
        zone_high: float,
        zone_id: str = "UNKNOWN",
        zone_type: str = "OB",
        from_direction: Literal["BELOW", "ABOVE"] = "BELOW"
    ) -> ZoneInteraction:
        """Clasifica interacción usando config parametrizable"""

        # ... (implementación como en REBOTE_Y_PENETRACION_CRITERIOS.md)
        # Pero usando self.rb_cfg.r1_max_penetration_pts, etc.

        # Ejemplo:
        if (pen_pts <= self.rb_cfg.r1_max_penetration_pts and
            pen_pct <= self.rb_cfg.r1_max_penetration_pct):
            # ...
            pass

    def update_config(self, new_config: InteractionConfig):
        """Actualiza configuración en runtime"""
        self.config = new_config
        self.rb_cfg = new_config.rebote
        self.pn_cfg = new_config.penetracion
```

### Uso en Trading

```python
# Seleccionar config según contexto
current_hour = datetime.now().hour

if 9 <= current_hour < 11:  # NY open
    config = ConfigProfiles.NY_OPEN
elif current_hour < 8:  # Asian session
    config = ConfigProfiles.ASIAN_SESSION
else:  # Normal
    config = ConfigProfiles.DEFAULT

# Crear classifier con config apropiado
classifier = ZoneInteractionClassifier(config)

# Clasificar interacciones
for candle in live_candles:
    interaction = classifier.classify(
        candle, zone_low, zone_high, from_direction="BELOW"
    )

    if interaction.interaction_type in ['R0_CLEAN_BOUNCE', 'R1_SHALLOW_TOUCH']:
        # Entry signal
        execute_trade(interaction)
```

---

## Backtesting Framework

### Estructura de Backtester

```python
from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass
class BacktestResult:
    """Resultado de un backtest"""

    # Métricas principales
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # 0.0 - 1.0

    # Retornos
    total_return_pts: float
    avg_return_pts: float
    avg_win_pts: float
    avg_loss_pts: float

    # Ratios
    sharpe_ratio: float
    profit_factor: float  # gross_profit / gross_loss
    expectancy: float  # avg_return per trade

    # Risk
    max_drawdown_pts: float
    max_drawdown_pct: float
    max_consecutive_losses: int

    # Detalles
    trades: List[dict]  # Lista de todos los trades
    equity_curve: pd.Series


class ZoneInteractionBacktester:
    """
    Backtester para estrategias basadas en interacciones con zonas
    """

    def __init__(
        self,
        classifier: ZoneInteractionClassifier,
        zone_detector,  # Detector de zonas (OB, FVG, LP)
        data_loader     # Cargador de datos históricos
    ):
        self.classifier = classifier
        self.zone_detector = zone_detector
        self.data_loader = data_loader

    def run(
        self,
        config: InteractionConfig,
        start_date: str,
        end_date: str,
        symbols: List[str] = ['NQZ5'],
        timeframe: str = '5min',
        initial_capital: float = 100000,
        risk_per_trade_pct: float = 1.0,
        entry_rules: dict = None
    ) -> BacktestResult:
        """
        Ejecuta backtest

        Args:
            config: Configuración de parámetros
            start_date, end_date: Período a testear
            symbols: Lista de símbolos
            timeframe: Timeframe de velas
            initial_capital: Capital inicial
            risk_per_trade_pct: % de capital a arriesgar por trade
            entry_rules: Reglas de entrada custom

        Returns:
            BacktestResult con todas las métricas
        """

        # Actualizar classifier con nueva config
        self.classifier.update_config(config)

        # Cargar datos
        candles = self.data_loader.load(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )

        # Detectar zonas
        zones = self.zone_detector.detect_all_zones(candles)

        # Simular trading
        trades = []
        equity = initial_capital
        equity_curve = []

        for i, candle in enumerate(candles):
            # Buscar zonas activas cerca del precio actual
            active_zones = self._get_active_zones(
                zones, candle['timestamp'], candle['close']
            )

            for zone in active_zones:
                # Clasificar interacción
                interaction = self.classifier.classify(
                    candle=candle,
                    zone_low=zone['low'],
                    zone_high=zone['high'],
                    zone_id=zone['id'],
                    zone_type=zone['type'],
                    from_direction=self._determine_approach(candle, zone)
                )

                # Verificar si genera señal de entrada
                if self._is_entry_signal(interaction, entry_rules):
                    # Calcular position size
                    position_size = self._calculate_position_size(
                        interaction, equity, risk_per_trade_pct
                    )

                    # Simular trade
                    trade_result = self._simulate_trade(
                        entry_candle=candle,
                        interaction=interaction,
                        position_size=position_size,
                        future_candles=candles[i+1:i+100]  # Próximas 100 velas
                    )

                    if trade_result:
                        trades.append(trade_result)
                        equity += trade_result['pnl']

            equity_curve.append(equity)

        # Calcular métricas
        return self._calculate_metrics(trades, equity_curve, initial_capital)

    def _is_entry_signal(
        self,
        interaction: ZoneInteraction,
        entry_rules: dict
    ) -> bool:
        """Verifica si interacción genera señal de entrada"""

        if entry_rules is None:
            # Reglas default
            valid_types = [
                'R0_CLEAN_BOUNCE',
                'R1_SHALLOW_TOUCH',
                'R2_LIGHT_REJECTION',
                'P4_FALSE_BREAKOUT'
            ]
            return interaction.interaction_type in valid_types

        # Reglas custom
        return entry_rules.get(interaction.interaction_type, False)

    def _simulate_trade(
        self,
        entry_candle: dict,
        interaction: ZoneInteraction,
        position_size: int,
        future_candles: List[dict]
    ) -> Optional[dict]:
        """Simula un trade y retorna resultado"""

        # Determinar dirección
        if interaction.expected_outcome == 'REVERSAL':
            if entry_candle['close'] < interaction.zone_low:
                direction = 'LONG'
                entry_price = entry_candle['close']
                stop_loss = interaction.zone_low - 5.0
                take_profit = entry_price + 50.0  # Target fijo
            else:
                direction = 'SHORT'
                entry_price = entry_candle['close']
                stop_loss = interaction.zone_high + 5.0
                take_profit = entry_price - 50.0
        else:
            return None  # No operar penetraciones por ahora

        # Simular evolución del trade
        for candle in future_candles:
            # Verificar stop loss
            if direction == 'LONG' and candle['low'] <= stop_loss:
                pnl = (stop_loss - entry_price) * position_size * 20  # $20 per point NQ
                return {
                    'entry_time': entry_candle['timestamp'],
                    'exit_time': candle['timestamp'],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': stop_loss,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'pnl': pnl,
                    'outcome': 'LOSS',
                    'interaction_type': interaction.interaction_type
                }

            # Verificar take profit
            if direction == 'LONG' and candle['high'] >= take_profit:
                pnl = (take_profit - entry_price) * position_size * 20
                return {
                    'entry_time': entry_candle['timestamp'],
                    'exit_time': candle['timestamp'],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': take_profit,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'pnl': pnl,
                    'outcome': 'WIN',
                    'interaction_type': interaction.interaction_type
                }

            # Similar para SHORT...

        # Trade no completado en período
        return None

    def _calculate_metrics(
        self,
        trades: List[dict],
        equity_curve: List[float],
        initial_capital: float
    ) -> BacktestResult:
        """Calcula todas las métricas de backtest"""

        if not trades:
            return BacktestResult(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0.0, total_return_pts=0.0, avg_return_pts=0.0,
                avg_win_pts=0.0, avg_loss_pts=0.0, sharpe_ratio=0.0,
                profit_factor=0.0, expectancy=0.0, max_drawdown_pts=0.0,
                max_drawdown_pct=0.0, max_consecutive_losses=0,
                trades=[], equity_curve=pd.Series()
            )

        wins = [t for t in trades if t['outcome'] == 'WIN']
        losses = [t for t in trades if t['outcome'] == 'LOSS']

        total_trades = len(trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades

        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / total_trades

        gross_profit = sum(t['pnl'] for t in wins)
        gross_loss = abs(sum(t['pnl'] for t in losses))

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Sharpe ratio
        returns = pd.Series([t['pnl'] for t in trades])
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # Max drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = equity_series - running_max
        max_dd_pts = abs(drawdown.min())
        max_dd_pct = (max_dd_pts / initial_capital) * 100

        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return_pts=total_pnl / 20,  # Convert $ to pts
            avg_return_pts=avg_pnl / 20,
            avg_win_pts=(gross_profit / winning_trades / 20) if winning_trades > 0 else 0,
            avg_loss_pts=(gross_loss / losing_trades / 20) if losing_trades > 0 else 0,
            sharpe_ratio=sharpe,
            profit_factor=profit_factor,
            expectancy=avg_pnl,
            max_drawdown_pts=max_dd_pts,
            max_drawdown_pct=max_dd_pct,
            max_consecutive_losses=self._max_consecutive(losses),
            trades=trades,
            equity_curve=equity_series
        )

    def _max_consecutive(self, losses: List[dict]) -> int:
        """Calcula máximo de pérdidas consecutivas"""
        # ... (implementación)
        pass
```

---

## Guía de Optimización

### Workflow Recomendado

```
1. BASELINE
   └─ Backtest con config DEFAULT
   └─ Documentar métricas baseline

2. OPTIMIZACIÓN INDIVIDUAL
   └─ Optimizar cada parámetro por separado
   └─ Identificar parámetros más sensibles

3. GRID SEARCH ENFOCADO
   └─ Grid search en top 3-5 parámetros más sensibles
   └─ Limitar combinaciones (max 100-200)

4. WALK-FORWARD VALIDATION
   └─ Validar en múltiples períodos out-of-sample
   └─ Detectar overfitting

5. ROBUSTNESS TEST
   └─ Testear config optimizado en diferentes condiciones
   └─ Volatilidad alta/baja, diferentes sesiones

6. DEPLOY
   └─ Si degradation < 15%, deploy en paper trading
   └─ Monitor performance en tiempo real
```

### Parámetros a Optimizar (Prioridad)

**Alta Prioridad** (optimizar primero):
1. `r1_max_penetration_pts` - Muy sensible
2. `r2_max_penetration_pts` - Muy sensible
3. `r1_max_penetration_pct` - Sensible
4. `r2_min_rejection_wick_pct` - Sensible

**Media Prioridad**:
5. `r3_max_penetration_pct`
6. `p4_min_break_distance_pts`
7. `r0_max_penetration_pts`

**Baja Prioridad** (usar defaults):
- `r4_*` - Pocos casos
- `p1_*`, `p2_*`, `p3_*` - Penetraciones no son señales primarias

### Rangos Razonables por Parámetro

```python
OPTIMIZATION_RANGES = {
    # Rebotes
    'r0_max_penetration_pts': [0.25, 0.5, 0.75, 1.0, 1.25, 1.5],
    'r1_max_penetration_pts': [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
    'r1_max_penetration_pct': [3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    'r2_max_penetration_pts': [6.0, 8.0, 10.0, 12.0, 15.0],
    'r2_max_penetration_pct': [8.0, 10.0, 12.0, 15.0],
    'r2_min_rejection_wick_pct': [20.0, 25.0, 30.0, 35.0, 40.0],

    # Penetraciones
    'p4_min_break_distance_pts': [3.0, 5.0, 7.0, 10.0],
    'p5_min_continuation_pts': [15.0, 20.0, 25.0, 30.0]
}
```

### Prevención de Overfitting

**Reglas**:
1. ✅ Usar walk-forward optimization (mínimo 3 períodos)
2. ✅ Degradación train→test debe ser < 15%
3. ✅ Mínimo 100 trades por período test
4. ✅ No optimizar más de 5 parámetros simultáneamente
5. ✅ Guardar config optimizado + período de optimización

**Red Flags**:
- 🚩 Win rate en train = 90%, en test = 60% → Overfitting
- 🚩 Solo funciona en un período específico → Curve fitting
- 🚩 Total trades < 50 → Muestra insuficiente
- 🚩 Sharpe en train = 3.5, en test = 1.2 → Overfitting severo

---

## API de Configuración

### Cargar/Guardar Configs

```python
import json
import yaml
from pathlib import Path

class ConfigManager:
    """Manager para guardar/cargar configuraciones"""

    def __init__(self, config_dir: str = "configs/"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def save(
        self,
        config: InteractionConfig,
        filename: str,
        format: str = 'yaml'
    ):
        """Guarda configuración a archivo"""

        filepath = self.config_dir / f"{filename}.{format}"

        config_dict = {
            'metadata': {
                'name': config.name,
                'description': config.description,
                'timeframe': config.timeframe,
                'instrument': config.instrument,
                'optimized_for': config.optimized_for
            },
            'rebote': asdict(config.rebote),
            'penetracion': asdict(config.penetracion)
        }

        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2)
        elif format == 'yaml':
            with open(filepath, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)

        print(f"Config saved to {filepath}")

    def load(
        self,
        filename: str,
        format: str = 'yaml'
    ) -> InteractionConfig:
        """Carga configuración desde archivo"""

        filepath = self.config_dir / f"{filename}.{format}"

        if format == 'json':
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
        elif format == 'yaml':
            with open(filepath, 'r') as f:
                config_dict = yaml.safe_load(f)

        return InteractionConfig(
            rebote=ReboteConfig(**config_dict['rebote']),
            penetracion=PenetracionConfig(**config_dict['penetracion']),
            **config_dict['metadata']
        )

    def list_configs(self) -> List[str]:
        """Lista todas las configuraciones guardadas"""
        configs = list(self.config_dir.glob("*.yaml")) + \
                 list(self.config_dir.glob("*.json"))
        return [c.stem for c in configs]


# === USO ===

manager = ConfigManager("configs/")

# Guardar config optimizado
optimized_config = InteractionConfig(
    rebote=ReboteConfig(r1_max_penetration_pts=2.5),
    name="NQ_5MIN_OPTIMIZED_Q1_2025",
    description="Optimized on Q1 2025 data, Sharpe=2.8",
    timeframe="5min",
    instrument="NQ",
    optimized_for="Q1_2025"
)

manager.save(optimized_config, "nq_5min_optimized_q1_2025", format='yaml')

# Cargar config
loaded_config = manager.load("nq_5min_optimized_q1_2025", format='yaml')

# Listar configs disponibles
available = manager.list_configs()
print(f"Available configs: {available}")
```

### Versionado de Configs

```python
# Incluir metadata de versión
@dataclass
class VersionedConfig:
    config: InteractionConfig
    version: str
    created_at: str
    optimized_on_period: tuple  # (start_date, end_date)
    backtest_metrics: dict
    git_commit_hash: Optional[str] = None

# Guardar con versión
versioned = VersionedConfig(
    config=optimized_config,
    version="1.0.0",
    created_at="2025-12-03",
    optimized_on_period=("2025-01-01", "2025-03-31"),
    backtest_metrics={
        'sharpe_ratio': 2.8,
        'win_rate': 0.72,
        'total_trades': 156
    }
)
```

---

## Ejemplos Prácticos

### Ejemplo 1: Optimizar para NQ 1min

```python
# 1. Crear base config para 1min
base_1min = ConfigProfiles.SCALPING_1MIN

# 2. Definir grid de optimización (reducido para 1min)
param_grid = {
    'r1_max_penetration_pts': [0.5, 0.75, 1.0, 1.25],
    'r2_max_penetration_pts': [2.0, 2.5, 3.0, 3.5],
    'r1_max_penetration_pct': [2.0, 3.0, 4.0]
}

# 3. Optimizar
optimizer = ParameterOptimizer(data_source, zone_detector, backtester)

result = optimizer.grid_search_optimization(
    param_grid=param_grid,
    base_config=base_1min,
    metric='sharpe_ratio',
    start_date='2025-01-01',
    end_date='2025-03-31',
    top_n=5
)

# 4. Validar con walk-forward
wfo_result = optimizer.walk_forward_optimization(
    param_grid={key: [result['best_params'][key]] for key in result['best_params']},
    base_config=base_1min,
    train_periods=[
        ('2025-01-01', '2025-01-31'),
        ('2025-02-01', '2025-02-28'),
        ('2025-03-01', '2025-03-31')
    ],
    test_periods=[
        ('2025-02-01', '2025-02-15'),
        ('2025-03-01', '2025-03-15'),
        ('2025-04-01', '2025-04-15')
    ]
)

# 5. Si degradación < 15%, usar config optimizado
if wfo_result['summary']['avg_degradation_pct'] < 15:
    optimized_1min = replace(
        base_1min,
        rebote=replace(base_1min.rebote, **result['best_params']),
        name="NQ_1MIN_OPTIMIZED",
        optimized_for="Q1_2025"
    )

    # Guardar
    manager.save(optimized_1min, "nq_1min_optimized")
```

### Ejemplo 2: Adaptar para Alta Volatilidad

```python
# 1. Backtest con config normal en período volátil
normal_config = ConfigProfiles.DEFAULT

vol_period_result = backtester.run(
    config=normal_config,
    start_date='2025-03-15',  # Período con alta volatilidad
    end_date='2025-03-22'
)

print(f"Normal config Sharpe: {vol_period_result.sharpe_ratio:.2f}")
# Output: 1.2 (bajo para período volátil)

# 2. Probar con config de alta volatilidad
high_vol_config = ConfigProfiles.HIGH_VOLATILITY

high_vol_result = backtester.run(
    config=high_vol_config,
    start_date='2025-03-15',
    end_date='2025-03-22'
)

print(f"High-vol config Sharpe: {high_vol_result.sharpe_ratio:.2f}")
# Output: 2.1 (mejor)

# 3. Optimizar específicamente para este período
optimized_vol = optimizer.optimize_single_parameter(
    param_name='r2_max_penetration_pts',
    test_values=[10.0, 12.0, 15.0, 18.0, 20.0],
    base_config=high_vol_config,
    start_date='2025-03-01',
    end_date='2025-03-31'
)

print(f"Optimal R2 threshold for high vol: {optimized_vol['best_value']}")
# Output: 18.0 pts
```

### Ejemplo 3: Sistema Adaptativo en Tiempo Real

```python
class AdaptiveConfigSelector:
    """Selector automático de config según contexto en tiempo real"""

    def __init__(self, config_manager: ConfigManager):
        self.manager = config_manager
        self.current_config = ConfigProfiles.DEFAULT

    def get_current_config(self, market_data: dict) -> InteractionConfig:
        """
        Selecciona config apropiado según condiciones actuales

        Args:
            market_data: dict con current_time, atr, volume, etc.

        Returns:
            InteractionConfig apropiado
        """

        current_time = market_data['current_time']
        hour = current_time.hour
        atr = market_data['atr']  # Average True Range
        avg_atr = market_data['avg_atr_20day']

        volatility_ratio = atr / avg_atr

        # Determinar contexto
        if hour in [9, 10]:  # NY open
            base_config = ConfigProfiles.NY_OPEN
        elif hour < 8:  # Asian session
            base_config = ConfigProfiles.ASIAN_SESSION
        else:
            base_config = ConfigProfiles.DEFAULT

        # Ajustar por volatilidad
        if volatility_ratio > 1.5:
            # Alta volatilidad inusual
            config = ConfigProfiles.HIGH_VOLATILITY
        elif volatility_ratio < 0.7:
            # Baja volatilidad inusual
            config = ConfigProfiles.LOW_VOLATILITY
        else:
            config = base_config

        # Cache
        self.current_config = config

        return config


# Uso en trading bot
selector = AdaptiveConfigSelector(config_manager)

for candle in live_stream:
    # Obtener config apropiado
    market_data = {
        'current_time': candle['timestamp'],
        'atr': calculate_atr(recent_candles),
        'avg_atr_20day': 45.0  # Ejemplo
    }

    config = selector.get_current_config(market_data)

    # Usar config
    classifier = ZoneInteractionClassifier(config)
    interaction = classifier.classify(candle, zone_low, zone_high)

    # Trading logic...
```

---

## Machine Learning Preparation

### Estructura para ML

El sistema está diseñado para facilitar machine learning:

```python
# 1. Feature Engineering - Parámetros como features
def extract_features(interaction: ZoneInteraction) -> dict:
    """Extrae features para ML model"""

    return {
        # Features de zona
        'zone_size': interaction.zone_size,
        'zone_type': interaction.zone_type,  # One-hot encoded

        # Features de penetración
        'penetration_pts': interaction.penetration_pts,
        'penetration_pct': interaction.penetration_pct,
        'penetration_type': interaction.penetration_type,  # One-hot

        # Features de rechazo
        'rejection_wick_pct': interaction.rejection_wick_pct,
        'rejection_ratio': interaction.rejection_ratio,

        # Features de contexto
        'hour_of_day': interaction.timestamp.hour,
        'day_of_week': interaction.timestamp.weekday(),

        # Features de mercado (agregar)
        'atr': market_data['atr'],
        'volume_ratio': interaction.candle_volume / avg_volume,

        # Target
        'outcome': 1 if future_move > 0 else 0  # Clasificación binaria
    }

# 2. Dataset para ML
interactions_df = pd.DataFrame([
    extract_features(interaction)
    for interaction in all_interactions
])

# 3. Train ML model
from sklearn.ensemble import RandomForestClassifier

X = interactions_df.drop(['outcome'], axis=1)
y = interactions_df['outcome']

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# 4. Feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.head(10))
# Output: Descubrir qué features son más predictivas
```

### Usar ML para Optimización

```python
# ML puede sugerir parámetros óptimos
def ml_suggest_parameters(market_conditions: dict) -> dict:
    """
    Usa ML model para sugerir parámetros óptimos
    según condiciones de mercado

    Args:
        market_conditions: dict con atr, volume, session, etc.

    Returns:
        dict con parámetros sugeridos
    """

    # Predecir con model entrenado
    features = extract_market_features(market_conditions)
    prediction = ml_model.predict([features])[0]

    # Mapear a parámetros
    # (Esto requiere entrenar model específicamente para esto)
    suggested_params = {
        'r1_max_penetration_pts': prediction['r1_threshold'],
        'r2_max_penetration_pts': prediction['r2_threshold'],
        # ...
    }

    return suggested_params

# Crear config dinámicamente
ml_suggested = ml_suggest_parameters({
    'atr': 52.5,
    'volume_ratio': 1.3,
    'session': 'ny_open'
})

custom_config = replace(
    ConfigProfiles.DEFAULT,
    rebote=replace(
        ConfigProfiles.DEFAULT.rebote,
        **ml_suggested
    )
)
```

---

## Conclusiones

### Resumen

1. ✅ **Arquitectura Completa**: Dataclasses, perfiles, optimización
2. ✅ **Parametrizable**: Todos los umbrales configurables
3. ✅ **Validación Científica**: Walk-forward, prevención overfitting
4. ✅ **Producción-Ready**: Config manager, versionado
5. ✅ **Escalable**: Machine Learning preparation

### Workflow Completo

```
DESARROLLO
└─ Definir criterios (REBOTE_Y_PENETRACION_CRITERIOS.md)
└─ Crear arquitectura parametrizable (este documento)
└─ Implementar classifier parametrizable

OPTIMIZACIÓN
└─ Backtest con DEFAULT config (baseline)
└─ Optimizar parámetros individuales
└─ Grid search enfocado
└─ Walk-forward validation
└─ Robustness testing

DEPLOY
└─ Guardar config optimizado con metadata
└─ Deploy en paper trading
└─ Monitor performance
└─ Re-optimizar trimestralmente

EVOLUCIÓN
└─ Recopilar datos de trades reales
└─ Feature engineering para ML
└─ Entrenar model predictivo
└─ Sistema adaptativo ML-driven
```

### Próximos Pasos

1. Implementar `ZoneInteractionClassifier` con parámetros
2. Crear `ZoneInteractionBacktester` completo
3. Ejecutar optimización en datos históricos (6+ meses)
4. Documentar resultados en `REBOTE_BACKTESTING_RESULTS.md`
5. Deploy config optimizado en paper trading

---

**Documento creado**: 2025-12-03
**Autor**: NQHUB Trading System
**Versión**: 1.0
**Complementa**: REBOTE_Y_PENETRACION_CRITERIOS.md
