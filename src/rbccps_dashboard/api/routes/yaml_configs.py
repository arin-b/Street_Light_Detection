from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from rbccps_dashboard.schemas import (
    YAMLConfigRead,
    YAMLConfigSummary,
    YAMLConfigUpdate,
    YAMLValidationRequest,
    YAMLValidationResponse,
)
from rbccps_dashboard.services.yaml_store import YAMLStore

router = APIRouter(prefix="/yaml-configs", tags=["yaml-configs"])


@router.get("", response_model=list[YAMLConfigSummary])
def list_yaml_configs() -> list[YAMLConfigSummary]:
    return [YAMLConfigSummary(**item.__dict__) for item in YAMLStore().list_configs()]


@router.get("/file", response_model=YAMLConfigRead)
def read_yaml_config(path: str) -> YAMLConfigRead:
    try:
        return YAMLConfigRead(**YAMLStore().read_config(path).__dict__)
    except FileNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/file", response_model=YAMLConfigRead)
def write_yaml_config(payload: YAMLConfigUpdate) -> YAMLConfigRead:
    try:
        return YAMLConfigRead(**YAMLStore().write_config(payload.path, payload.content).__dict__)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/validate", response_model=YAMLValidationResponse)
def validate_yaml(payload: YAMLValidationRequest) -> YAMLValidationResponse:
    valid, parsed, error = YAMLStore().validate(payload.content)
    return YAMLValidationResponse(valid=valid, parsed=parsed, error=error)
