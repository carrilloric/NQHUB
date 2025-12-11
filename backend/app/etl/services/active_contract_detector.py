"""
Active Contract Detector

Analiza volumen diario de contratos futuros NQ para identificar
cuál es el contrato "activo" (front month) en cada período.

Detecta automáticamente rollovers (cambios de contrato dominante).
"""
from typing import List, Dict, Tuple
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


async def detect_active_contracts(
    session: AsyncSession,
    start_date: date,
    end_date: date
) -> List[Dict]:
    """
    Analiza volumen diario de todos los contratos y detecta
    cuál es el activo en cada período.

    Args:
        session: Async database session
        start_date: Fecha inicial del análisis
        end_date: Fecha final del análisis

    Returns:
        Lista de períodos de contrato activo:
        [
            {
                'symbol': 'NQU4',
                'start_date': date(2024, 6, 18),
                'end_date': date(2024, 7, 15),
                'volume_score': 2358787,
                'tick_count': 2358787,
                'is_current': True,
                'rollover_period': False
            },
            ...
        ]
    """
    logger.info(f"🔍 Detecting active contracts for date range: {start_date} to {end_date}")

    # STEP 1: Obtener volumen diario por símbolo
    daily_volumes = await _get_daily_volumes(session, start_date, end_date)

    if not daily_volumes:
        logger.warning("⚠️ No volume data found for date range")
        return []

    logger.info(f"📊 Analyzed {len(daily_volumes)} days of volume data")

    # STEP 2: Identificar contrato líder por día
    daily_leaders = {}
    for day_data in daily_volumes:
        day = day_data['date']
        symbol = day_data['symbol']
        volume = day_data['volume']
        ticks = day_data['ticks']

        if day not in daily_leaders or volume > daily_leaders[day]['volume']:
            daily_leaders[day] = {
                'symbol': symbol,
                'volume': volume,
                'ticks': ticks
            }

    logger.info(f"📅 Identified leaders for {len(daily_leaders)} days")

    # STEP 3: Agrupar en períodos continuos
    active_periods = _group_into_periods(daily_leaders, end_date)

    logger.info(f"✅ Identified {len(active_periods)} active contract periods")
    for period in active_periods:
        logger.info(
            f"  → {period['symbol']}: "
            f"{period['start_date']} to {period['end_date']} "
            f"({period['volume_score']:,} volume, {period['tick_count']:,} ticks)"
        )

    return active_periods


async def _get_daily_volumes(
    session: AsyncSession,
    start_date: date,
    end_date: date
) -> List[Dict]:
    """
    Obtiene volumen total por día y símbolo desde tabla candlestick_daily.
    Solo incluye contratos outright (excluye spreads).
    """
    query = text("""
        SELECT
            DATE(time_interval) as date,
            symbol,
            SUM(volume) as daily_volume,
            SUM(tick_count) as daily_ticks
        FROM candlestick_daily
        WHERE symbol NOT LIKE '%-%'  -- Excluir spreads
          AND DATE(time_interval) BETWEEN :start_date AND :end_date
        GROUP BY DATE(time_interval), symbol
        ORDER BY date, daily_volume DESC
    """)

    result = await session.execute(query, {
        'start_date': start_date,
        'end_date': end_date
    })

    rows = result.fetchall()

    return [
        {
            'date': row[0],
            'symbol': row[1],
            'volume': row[2],
            'ticks': row[3]
        }
        for row in rows
    ]


def _group_into_periods(
    daily_leaders: Dict[date, Dict],
    end_date: date
) -> List[Dict]:
    """
    Agrupa días con el mismo símbolo líder en períodos continuos.
    Detecta cambios de contrato (rollovers).
    """
    if not daily_leaders:
        return []

    active_periods = []
    sorted_dates = sorted(daily_leaders.keys())

    current_symbol = None
    period_start = None
    period_volume = 0
    period_ticks = 0

    for day in sorted_dates:
        leader_data = daily_leaders[day]
        leader_symbol = leader_data['symbol']

        if leader_symbol != current_symbol:
            # Cambio de contrato líder

            if current_symbol is not None:
                # Cerrar período anterior
                active_periods.append({
                    'symbol': current_symbol,
                    'start_date': period_start,
                    'end_date': day - timedelta(days=1),
                    'volume_score': period_volume,
                    'tick_count': period_ticks,
                    'is_current': False,  # Será actualizado al final
                    'rollover_period': False
                })

                logger.info(
                    f"🔄 Rollover detected on {day}: "
                    f"{current_symbol} → {leader_symbol}"
                )

            # Iniciar nuevo período
            current_symbol = leader_symbol
            period_start = day
            period_volume = leader_data['volume']
            period_ticks = leader_data['ticks']
        else:
            # Mismo contrato, acumular métricas
            period_volume += leader_data['volume']
            period_ticks += leader_data['ticks']

    # Cerrar último período
    if current_symbol is not None:
        last_day = sorted_dates[-1]
        is_current_contract = (last_day == end_date or
                              (end_date - last_day).days <= 3)

        active_periods.append({
            'symbol': current_symbol,
            'start_date': period_start,
            'end_date': None if is_current_contract else last_day,
            'volume_score': period_volume,
            'tick_count': period_ticks,
            'is_current': is_current_contract,
            'rollover_period': False
        })

    return active_periods


async def save_active_periods(
    session: AsyncSession,
    periods: List[Dict]
) -> int:
    """
    Guarda períodos de contrato activo en la base de datos.

    Args:
        session: Async database session
        periods: Lista de períodos detectados

    Returns:
        Número de registros insertados/actualizados
    """
    if not periods:
        logger.warning("⚠️ No active periods to save")
        return 0

    logger.info(f"💾 Saving {len(periods)} active contract periods to database")

    # Primero, marcar todos los contratos actuales como no actuales
    await session.execute(text("""
        UPDATE active_contracts
        SET is_current = false
        WHERE is_current = true
    """))

    # Insertar/actualizar cada período
    saved_count = 0
    for period in periods:
        query = text("""
            INSERT INTO active_contracts
            (symbol, start_date, end_date, volume_score, tick_count, is_current, rollover_period)
            VALUES (:symbol, :start_date, :end_date, :volume_score, :tick_count, :is_current, :rollover_period)
            ON CONFLICT (symbol, start_date) DO UPDATE SET
                end_date = EXCLUDED.end_date,
                volume_score = EXCLUDED.volume_score,
                tick_count = EXCLUDED.tick_count,
                is_current = EXCLUDED.is_current,
                rollover_period = EXCLUDED.rollover_period,
                updated_at = NOW()
        """)

        await session.execute(query, {
            'symbol': period['symbol'],
            'start_date': period['start_date'],
            'end_date': period['end_date'],
            'volume_score': period['volume_score'],
            'tick_count': period['tick_count'],
            'is_current': period['is_current'],
            'rollover_period': period['rollover_period']
        })
        saved_count += 1

    await session.commit()
    logger.info(f"✅ Saved {saved_count} active contract periods")

    return saved_count


async def get_current_active_contract(session: AsyncSession) -> Dict | None:
    """
    Obtiene el contrato activo actual.

    Returns:
        {'symbol': 'NQU4', 'start_date': date(...), ...} o None
    """
    query = text("""
        SELECT symbol, start_date, end_date, volume_score, tick_count
        FROM active_contracts
        WHERE is_current = true
        ORDER BY start_date DESC
        LIMIT 1
    """)

    result = await session.execute(query)
    row = result.first()

    if not row:
        return None

    return {
        'symbol': row[0],
        'start_date': row[1],
        'end_date': row[2],
        'volume_score': row[3],
        'tick_count': row[4]
    }


async def get_rollover_history(
    session: AsyncSession,
    limit: int = 10
) -> List[Dict]:
    """
    Obtiene historial de períodos de contrato activo.

    Args:
        session: Async database session
        limit: Máximo número de registros a retornar

    Returns:
        Lista de períodos ordenados por fecha (más reciente primero)
    """
    query = text("""
        SELECT
            id,
            symbol,
            start_date,
            end_date,
            volume_score,
            tick_count,
            is_current,
            rollover_period,
            created_at,
            updated_at
        FROM active_contracts
        ORDER BY start_date DESC
        LIMIT :limit
    """)

    result = await session.execute(query, {'limit': limit})
    rows = result.fetchall()

    return [
        {
            'id': row[0],
            'symbol': row[1],
            'start_date': row[2],
            'end_date': row[3],
            'volume_score': row[4],
            'tick_count': row[5],
            'is_current': row[6],
            'rollover_period': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        }
        for row in rows
    ]
