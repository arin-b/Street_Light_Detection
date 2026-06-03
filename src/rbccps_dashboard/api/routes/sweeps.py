"""REST API routes for Hyperparameter Sweeps (Phase 4)."""

from __future__ import annotations

import itertools
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rbccps_dashboard.database import get_session
from rbccps_dashboard.models import Experiment
from rbccps_dashboard.schemas import ExperimentRead

router = APIRouter(prefix="/sweeps", tags=["sweeps"])


class SweepRequest(BaseModel):
    base_experiment_id: int
    parameters: dict[str, list[Any]]


def _set_nested_value(d: dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


@router.post("", response_model=list[ExperimentRead], status_code=status.HTTP_201_CREATED)
def create_sweep(
    request: SweepRequest,
    session: Annotated[Session, Depends(get_session)],
) -> list[ExperimentRead]:
    """Generate multiple experiments from a grid search sweep."""
    base_exp = session.get(Experiment, request.base_experiment_id)
    if not base_exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Base experiment not found")

    # Generate all combinations of parameters
    keys = list(request.parameters.keys())
    values = list(request.parameters.values())
    combinations = list(itertools.product(*values))
    
    if not combinations:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No combinations generated")

    if len(combinations) > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many combinations (max 50)")

    created_experiments = []
    
    for i, combo in enumerate(combinations):
        # Create a deep copy of the base config
        import copy
        new_config = copy.deepcopy(base_exp.config_snapshot)
        
        # Apply the parameters
        combo_desc_parts = []
        for key, value in zip(keys, combo):
            _set_nested_value(new_config, key, value)
            combo_desc_parts.append(f"{key}={value}")
            
        combo_desc = ", ".join(combo_desc_parts)
        
        # Create new experiment
        new_exp = Experiment(
            name=f"{base_exp.name} - Sweep {i+1}",
            description=f"Sweep combination: {combo_desc}\n\nBase: {base_exp.description}",
            status="draft",
            config_snapshot=new_config,
            tags=[*base_exp.tags, "sweep"],
        )
        session.add(new_exp)
        created_experiments.append(new_exp)
        
    session.commit()
    
    for exp in created_experiments:
        session.refresh(exp)
        
    return [ExperimentRead.model_validate(exp) for exp in created_experiments]
