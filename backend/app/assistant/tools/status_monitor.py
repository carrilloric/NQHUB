"""
Status monitoring tools for ETL, patterns, and database stats
"""
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.db.session import SessionLocal
from app.etl.models import ETLJob
from app.models.patterns import DetectedFVG, DetectedLiquidityPool, DetectedOrderBlock

logger = logging.getLogger(__name__)


def get_etl_status(db: Session) -> Dict[str, Any]:
    """Get ETL jobs status"""
    try:
        # Aggregated counts
        total = db.query(ETLJob).count()
        running = db.query(ETLJob).filter(ETLJob.status == "running").count()
        completed = db.query(ETLJob).filter(ETLJob.status == "completed").count()
        failed = db.query(ETLJob).filter(ETLJob.status == "failed").count()

        # Recent jobs
        recent_jobs = db.query(ETLJob).order_by(ETLJob.created_at.desc()).limit(5).all()
        recent_jobs_data = [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "rows_processed": getattr(job, 'rows_processed', 0),
            }
            for job in recent_jobs
        ]

        return {
            "total_jobs": total,
            "running": running,
            "completed": completed,
            "failed": failed,
            "recent_jobs": recent_jobs_data,
        }

    except Exception as e:
        logger.error(f"Failed to get ETL status: {e}")
        return {
            "total_jobs": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "recent_jobs": [],
            "error": str(e)
        }


def get_pattern_status(db: Session) -> Dict[str, Any]:
    """Get pattern detection status"""
    try:
        # Counts
        total_fvgs = db.query(DetectedFVG).count()
        total_lps = db.query(DetectedLiquidityPool).count()
        total_obs = db.query(DetectedOrderBlock).count()

        # Recent detections (last 24h)
        yesterday = datetime.utcnow() - timedelta(hours=24)

        recent_fvgs = db.query(DetectedFVG).filter(
            DetectedFVG.formation_time >= yesterday
        ).limit(5).all()

        recent_lps = db.query(DetectedLiquidityPool).filter(
            DetectedLiquidityPool.created_at >= yesterday
        ).limit(5).all()

        recent_obs = db.query(DetectedOrderBlock).filter(
            DetectedOrderBlock.formation_time >= yesterday
        ).limit(5).all()

        recent_detections = []

        for fvg in recent_fvgs:
            recent_detections.append({
                "type": "FVG",
                "formation_time": fvg.formation_time.isoformat() if fvg.formation_time else None,
                "direction": fvg.direction,
                "status": fvg.status,
                "significance": fvg.significance,
            })

        for lp in recent_lps:
            recent_detections.append({
                "type": "LP",
                "pool_type": lp.pool_type,
                "modal_level": float(lp.modal_level) if lp.modal_level else None,
                "status": lp.status,
            })

        for ob in recent_obs:
            recent_detections.append({
                "type": "OB",
                "formation_time": ob.formation_time.isoformat() if ob.formation_time else None,
                "direction": ob.direction,
                "quality": ob.quality,
                "status": ob.status,
            })

        return {
            "total_fvgs": total_fvgs,
            "total_lps": total_lps,
            "total_obs": total_obs,
            "recent_detections": recent_detections[:10],  # Limit to 10 most recent
        }

    except Exception as e:
        logger.error(f"Failed to get pattern status: {e}")
        return {
            "total_fvgs": 0,
            "total_lps": 0,
            "total_obs": 0,
            "recent_detections": [],
            "error": str(e)
        }


def get_database_stats(db: Session) -> Dict[str, Any]:
    """Get database statistics"""
    try:
        # Query candle counts across timeframes
        candle_counts = {}
        timeframes = ["1min", "5min", "15min", "30min", "1hour", "4hour", "daily"]

        for tf in timeframes:
            try:
                table_name = f"candlestick_{tf}"
                count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                result = db.execute(count_query)
                count = result.scalar()
                candle_counts[tf] = count or 0
            except:
                candle_counts[tf] = 0

        # Total candles
        total_candles = sum(candle_counts.values())

        # Ticks count (if table exists)
        try:
            ticks_query = text("SELECT COUNT(*) FROM market_data_ticks")
            ticks_result = db.execute(ticks_query)
            total_ticks = ticks_result.scalar() or 0
        except:
            total_ticks = 0

        # Active contracts
        try:
            contracts_query = text("SELECT COUNT(*) FROM active_contracts")
            contracts_result = db.execute(contracts_query)
            active_contracts = contracts_result.scalar() or 0
        except:
            active_contracts = 0

        return {
            "total_candles": total_candles,
            "total_ticks": total_ticks,
            "active_contracts": active_contracts,
            "coverage_summary": candle_counts,
        }

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            "total_candles": 0,
            "total_ticks": 0,
            "active_contracts": 0,
            "coverage_summary": {},
            "error": str(e)
        }
