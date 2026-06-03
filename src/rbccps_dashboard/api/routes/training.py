"""REST API routes for training run management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from rbccps_dashboard.database import get_session
from rbccps_dashboard.schemas import LogEntryRead, RunRead
from rbccps_dashboard.services.training import get_training_service

router = APIRouter(prefix="/runs", tags=["training"])


@router.get("", response_model=list[RunRead])
def list_runs(
    session: Annotated[Session, Depends(get_session)],
    run_status: str | None = Query(None, alias="status"),
    experiment_id: int | None = Query(None),
) -> list[RunRead]:
    """List all training runs, optionally filtered."""
    service = get_training_service()
    runs = service.list_runs(session, status=run_status, experiment_id=experiment_id)
    return [RunRead.model_validate(run) for run in runs]


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: int, session: Annotated[Session, Depends(get_session)]) -> RunRead:
    """Get details for a specific run."""
    service = get_training_service()
    try:
        return RunRead.model_validate(service.get_run(run_id, session))
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{experiment_id}/start", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def start_training(
    experiment_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> RunRead:
    """Launch a training run for the given experiment."""
    service = get_training_service()
    try:
        run = service.launch(experiment_id, session)
        return RunRead.model_validate(run)
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/{run_id}/stop", response_model=RunRead)
def stop_training(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> RunRead:
    """Stop a running training process."""
    service = get_training_service()
    try:
        run = service.stop(run_id, session)
        return RunRead.model_validate(run)
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, session: Annotated[Session, Depends(get_session)]) -> None:
    """Delete a run record."""
    service = get_training_service()
    try:
        service.delete_run(run_id, session)
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{run_id}/logs", response_model=list[LogEntryRead])
def get_run_logs(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
) -> list[LogEntryRead]:
    """Get persisted log entries for a run."""
    service = get_training_service()
    try:
        service.get_run(run_id, session)  # Validate run exists
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    entries = service.get_logs(run_id, session, limit=limit, offset=offset)
    return [LogEntryRead.model_validate(entry) for entry in entries]


@router.get("/{run_id}/progress")
def get_run_progress(run_id: int, session: Annotated[Session, Depends(get_session)]) -> dict:
    """Get current epoch progress for a running training."""
    service = get_training_service()
    try:
        service.get_run(run_id, session)
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    progress = service.get_progress(run_id)
    progress["is_running"] = service.is_running(run_id)
    return progress
