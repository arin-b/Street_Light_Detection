"""REST API routes for system monitoring."""

from __future__ import annotations

from fastapi import APIRouter, Query

from rbccps_dashboard.schemas import GPUInfo, SystemMetrics
from rbccps_dashboard.services.monitoring import get_monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/snapshot", response_model=SystemMetrics)
def monitoring_snapshot() -> SystemMetrics:
    """Get a single system metrics snapshot (REST fallback for non-WebSocket clients)."""
    service = get_monitoring_service()
    return service.snapshot()


@router.get("/gpu-info", response_model=GPUInfo)
def gpu_info() -> GPUInfo:
    """Get static GPU device information."""
    service = get_monitoring_service()
    return service.gpu_info()


@router.get("/history")
def monitoring_history(minutes: int = Query(5, ge=1, le=60)) -> list[dict]:
    """Get recent system stats from the database.

    This is a lightweight endpoint; for real-time data use the WebSocket.
    """
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from rbccps_dashboard.database import SessionLocal
    from rbccps_dashboard.models import SystemStat

    cutoff = datetime.now(UTC) - timedelta(minutes=minutes)
    session = SessionLocal()
    try:
        query = (
            select(SystemStat)
            .where(SystemStat.captured_at >= cutoff)
            .order_by(SystemStat.captured_at)
        )
        stats = list(session.scalars(query))
        return [
            {
                "cpu_percent": s.cpu_percent,
                "ram_percent": s.ram_percent,
                "gpu_percent": s.gpu_percent,
                "metadata_json": s.metadata_json,
                "timestamp": s.captured_at.isoformat(),
            }
            for s in stats
        ]
    finally:
        session.close()
