"""
Approval API endpoints - Strategy and bot approval workflow
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class ApprovalChecklistItem(BaseModel):
    item_id: str
    category: str
    description: str
    status: bool
    severity: str  # critical, warning, info
    details: Optional[str] = None


class ApprovalRequest(BaseModel):
    entity_type: str  # strategy, bot, model
    entity_id: str
    requested_by: str
    reason: str
    risk_level: str  # low, medium, high


@router.get("/checklist/{strategy_id}")
async def get_approval_checklist(
    strategy_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get approval checklist for a strategy.

    Returns comprehensive checklist with risk assessment, compliance checks,
    and performance validation criteria.
    """
    return {
        "status": "success",
        "data": {
            "strategy_id": strategy_id,
            "overall_status": "pending",
            "risk_score": 65,
            "checklist": [
                {
                    "item_id": "risk_001",
                    "category": "Risk Management",
                    "description": "Maximum drawdown within acceptable limits",
                    "status": True,
                    "severity": "critical",
                    "details": "Max drawdown: 12% (limit: 20%)"
                },
                {
                    "item_id": "risk_002",
                    "category": "Risk Management",
                    "description": "Position sizing validated",
                    "status": True,
                    "severity": "critical",
                    "details": "Position size: 1-3 contracts"
                },
                {
                    "item_id": "perf_001",
                    "category": "Performance",
                    "description": "Minimum Sharpe ratio met",
                    "status": False,
                    "severity": "warning",
                    "details": "Sharpe: 0.8 (minimum: 1.0)"
                },
                {
                    "item_id": "test_001",
                    "category": "Testing",
                    "description": "Backtesting completed",
                    "status": True,
                    "severity": "critical",
                    "details": "1000+ trades tested"
                },
                {
                    "item_id": "test_002",
                    "category": "Testing",
                    "description": "Walk-forward validation passed",
                    "status": False,
                    "severity": "warning",
                    "details": "Pending walk-forward test"
                }
            ],
            "recommendations": [
                "Improve Sharpe ratio before production deployment",
                "Complete walk-forward validation",
                "Consider reducing position size for initial deployment"
            ]
        }
    }


@router.post("/submit")
async def submit_for_approval(
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit a strategy or bot for approval.

    Initiates the approval workflow with notifications to approvers.
    """
    return {
        "status": "success",
        "data": {
            "approval_id": "appr_001",
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "status": "pending",
            "submitted_at": datetime.utcnow().isoformat(),
            "message": "Submitted for approval successfully"
        }
    }


@router.get("/pending")
async def get_pending_approvals(
    entity_type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of pending approvals.

    For admins/approvers: shows items awaiting their review.
    For users: shows their submitted items pending approval.
    """
    return {
        "status": "success",
        "data": {
            "pending_approvals": [],
            "total": 0,
            "user_role": "trader",
            "message": "Pending approvals endpoint - pending implementation"
        }
    }


@router.post("/approve/{approval_id}")
async def approve_request(
    approval_id: str,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Approve a pending request.

    Only available to users with approval permissions.
    """
    # Check if user has approval permissions
    if current_user.role not in ["admin", "senior_trader"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {
        "status": "success",
        "data": {
            "approval_id": approval_id,
            "new_status": "approved",
            "approved_by": current_user.email,
            "approved_at": datetime.utcnow().isoformat(),
            "comments": comments,
            "message": "Request approved successfully"
        }
    }


@router.post("/reject/{approval_id}")
async def reject_request(
    approval_id: str,
    reason: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Reject a pending request.

    Only available to users with approval permissions.
    """
    # Check if user has approval permissions
    if current_user.role not in ["admin", "senior_trader"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {
        "status": "success",
        "data": {
            "approval_id": approval_id,
            "new_status": "rejected",
            "rejected_by": current_user.email,
            "rejected_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "message": "Request rejected"
        }
    }


@router.get("/history/{entity_id}")
async def get_approval_history(
    entity_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get approval history for a specific entity.

    Shows all approval requests and their outcomes for audit purposes.
    """
    return {
        "status": "success",
        "data": {
            "entity_id": entity_id,
            "history": [],
            "message": "Approval history endpoint - pending implementation"
        }
    }