"""REST API routes for PDF Reporting (Phase 4)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from rbccps_dashboard.database import get_session
from rbccps_dashboard.services.reporting import generate_run_report

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/{run_id}/pdf")
def download_run_report(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> StreamingResponse:
    """Generate and download a PDF report for a training run."""
    try:
        buffer = generate_run_report(run_id, session)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_run_{run_id}.pdf"
            },
        )
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report generation failed: {error}") from error
