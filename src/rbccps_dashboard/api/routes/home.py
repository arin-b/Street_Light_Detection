from __future__ import annotations

from typing import Annotated

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from rbccps_dashboard.database import get_session
from rbccps_dashboard.models import Experiment
from rbccps_dashboard.schemas import DashboardSummary
from rbccps_dashboard.services.yaml_store import YAMLStore

router = APIRouter(tags=["dashboard"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/summary", response_model=DashboardSummary)
def summary(session: Annotated[Session, Depends(get_session)]) -> DashboardSummary:
    total = session.scalar(select(func.count()).select_from(Experiment)) or 0
    active = session.scalar(select(func.count()).select_from(Experiment).where(Experiment.status.in_(["queued", "running"]))) or 0
    completed = session.scalar(select(func.count()).select_from(Experiment).where(Experiment.status == "completed")) or 0
    failed = session.scalar(select(func.count()).select_from(Experiment).where(Experiment.status == "failed")) or 0
    return DashboardSummary(
        experiments_total=total,
        experiments_active=active,
        experiments_completed=completed,
        experiments_failed=failed,
        yaml_configs=len(YAMLStore().list_configs()),
        cpu_percent=psutil.cpu_percent(interval=None),
        ram_percent=psutil.virtual_memory().percent,
    )
