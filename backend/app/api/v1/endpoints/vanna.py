"""
Vanna.AI Learning Statistics Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

from app.core.deps import get_current_user
from app.models.user import User
from app.assistant.tools.vanna_monitor import get_vanna_monitor

logger = logging.getLogger(__name__)

router = APIRouter()


class SimilarQueryRequest(BaseModel):
    """Request body for similarity search"""
    question: str
    limit: int = 5


@router.get("/stats", response_model=Dict[str, Any])
async def get_vanna_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Vanna.AI training statistics

    Returns:
        Dict with status, total_documents, collections, breakdown, etc.
    """
    try:
        monitor = get_vanna_monitor()

        # Get base stats
        stats = monitor.get_training_stats()

        # Add category breakdown
        if stats.get("status") == "active":
            stats["breakdown"] = monitor.get_category_breakdown()

        return stats

    except Exception as e:
        logger.error(f"Failed to get Vanna stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Vanna stats: {str(e)}")


@router.get("/queries", response_model=List[Dict[str, Any]])
async def get_vanna_queries(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get learned queries from Vanna

    Args:
        limit: Maximum number of queries to return (default 50)

    Returns:
        List of learned queries with id, content, metadata
    """
    try:
        monitor = get_vanna_monitor()
        queries = monitor.get_learned_queries(limit=limit)

        return queries

    except Exception as e:
        logger.error(f"Failed to get Vanna queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queries: {str(e)}")


@router.post("/similar", response_model=List[Dict[str, Any]])
async def find_similar_queries(
    request: SimilarQueryRequest,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Find similar queries to a given question

    Args:
        request: SimilarQueryRequest with question and limit

    Returns:
        List of similar queries with content, distance, metadata
    """
    try:
        monitor = get_vanna_monitor()
        similar = monitor.get_similar_queries(
            question=request.question,
            limit=request.limit
        )

        return similar

    except Exception as e:
        logger.error(f"Failed to find similar queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar queries: {str(e)}")


@router.get("/export")
async def export_vanna_data(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export all Vanna training data as JSON

    Returns:
        Complete export of stats and learned queries
    """
    try:
        monitor = get_vanna_monitor()

        # Get all data
        stats = monitor.get_training_stats()
        queries = monitor.get_learned_queries(limit=1000)

        # Add breakdown if active
        if stats.get("status") == "active":
            stats["breakdown"] = monitor.get_category_breakdown()

        export_data = {
            "exported_at": monitor.export_training_data.__globals__["datetime"].utcnow().isoformat(),
            "stats": stats,
            "learned_queries": queries
        }

        return export_data

    except Exception as e:
        logger.error(f"Failed to export Vanna data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")
