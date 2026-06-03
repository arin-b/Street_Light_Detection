from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from rbccps_dashboard.database import get_session
from rbccps_dashboard.schemas import ExperimentCreate, ExperimentDuplicate, ExperimentRead, ExperimentUpdate
from rbccps_dashboard.services.experiments import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _service(session: Session) -> ExperimentService:
    return ExperimentService(session)


@router.get("", response_model=list[ExperimentRead])
def list_experiments(session: Annotated[Session, Depends(get_session)]) -> list[ExperimentRead]:
    return [ExperimentRead.model_validate(item) for item in _service(session).list()]


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ExperimentRead:
    try:
        return ExperimentRead.model_validate(_service(session).create(payload))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: int, session: Annotated[Session, Depends(get_session)]) -> ExperimentRead:
    try:
        return ExperimentRead.model_validate(_service(session).get(experiment_id))
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.patch("/{experiment_id}", response_model=ExperimentRead)
def update_experiment(
    experiment_id: int,
    payload: ExperimentUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> ExperimentRead:
    try:
        return ExperimentRead.model_validate(_service(session).update(experiment_id, payload))
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(experiment_id: int, session: Annotated[Session, Depends(get_session)]) -> None:
    try:
        _service(session).delete(experiment_id)
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{experiment_id}/duplicate", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def duplicate_experiment(
    experiment_id: int,
    payload: ExperimentDuplicate,
    session: Annotated[Session, Depends(get_session)],
) -> ExperimentRead:
    try:
        return ExperimentRead.model_validate(_service(session).duplicate(experiment_id, payload))
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
