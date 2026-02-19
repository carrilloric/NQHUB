"""
Audit API Endpoints

Endpoints for generating audit reports to validate patterns against ATAS.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_sync
from app.schemas.audit import AuditOrderBlocksRequest, AuditOrderBlocksResponse
from app.services.audit import AuditReportGenerator

router = APIRouter()


@router.post("/order-blocks", response_model=AuditOrderBlocksResponse)
def generate_order_blocks_audit(
    request: AuditOrderBlocksRequest,
    db: Session = Depends(get_db_sync)
) -> AuditOrderBlocksResponse:
    """
    Generate audit report for Order Blocks at a specific timestamp

    This endpoint generates a markdown-formatted report with:
    - All ACTIVE Order Blocks at the specified snapshot_time
    - Detailed ATAS validation instructions for each OB
    - Summary statistics by type and quality

    Args:
        request: AuditOrderBlocksRequest with symbol, timeframe, snapshot_time
        db: Database session

    Returns:
        AuditOrderBlocksResponse with markdown report and OB details

    Example:
        POST /api/v1/audit/order-blocks
        {
            "symbol": "NQZ5",
            "timeframe": "5min",
            "snapshot_time": "2025-11-24T14:30:00"
        }
    """
    try:
        # Initialize audit report generator
        generator = AuditReportGenerator(db)

        # Generate audit report
        audit_response = generator.generate_order_blocks_audit(
            symbol=request.symbol,
            timeframe=request.timeframe,
            snapshot_time=request.snapshot_time
        )

        return audit_response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating audit report: {str(e)}"
        )
