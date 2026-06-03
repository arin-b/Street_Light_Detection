"""REST API routes for Visualizations (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from rbccps_dashboard.config import get_settings
from rbccps_dashboard.database import get_session
from rbccps_dashboard.models import Metric, Run

router = APIRouter(prefix="/visualizations", tags=["visualizations"])


@router.get("/compare")
def compare_runs(
    session: Annotated[Session, Depends(get_session)],
    run_ids: list[int] = Query(...),
) -> dict[str, list[dict[str, float | int]]]:
    """Fetch and align metrics from multiple runs for comparison charts."""
    
    # We want to return a structure like:
    # {
    #   "box_loss": [{"step": 0, "run_1": 0.5, "run_2": 0.6}, ...],
    #   "mAP50": [{"step": 0, "run_1": 0.1, "run_2": 0.15}, ...]
    # }
    
    # Fetch all metrics for the requested runs
    query = (
        select(Metric)
        .where(Metric.run_id.in_(run_ids))
        .order_by(Metric.name, Metric.step, Metric.run_id)
    )
    metrics = session.scalars(query).all()
    
    # Group by metric name, then by step
    grouped_data: dict[str, dict[int, dict[str, float | int]]] = {}
    for metric in metrics:
        if metric.name not in grouped_data:
            grouped_data[metric.name] = {}
        if metric.step not in grouped_data[metric.name]:
            grouped_data[metric.name][metric.step] = {"step": metric.step}
        grouped_data[metric.name][metric.step][f"run_{metric.run_id}"] = metric.value

    # Convert to sorted lists
    result = {
        name: [step_data[step] for step in sorted(step_data.keys())]
        for name, step_data in grouped_data.items()
    }
    
    return result


@router.get("/{run_id}/artifacts")
def list_run_artifacts(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> list[dict[str, str]]:
    """List image artifacts (plots, predictions) available for a run."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        
    if not run.output_dir:
        return []

    output_path = Path(run.output_dir)
    if not output_path.exists() or not output_path.is_dir():
        return []

    # Find common Ultralytics image artifacts
    valid_extensions = {".png", ".jpg", ".jpeg"}
    artifacts = []
    
    for file_path in output_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Categorize common plots
            category = "other"
            name = file_path.name.lower()
            if "confusion_matrix" in name:
                category = "confusion_matrix"
            elif "val_batch" in name and "pred" in name:
                category = "predictions"
            elif "val_batch" in name and "labels" in name:
                category = "labels"
            elif name in {"results.png", "results.jpg"}:
                category = "results_plot"
            elif "curve" in name:
                category = "curves"
                
            artifacts.append({
                "filename": file_path.name,
                "category": category,
            })
            
    # Sort for consistent ordering
    artifacts.sort(key=lambda x: (x["category"], x["filename"]))
    return artifacts


@router.get("/{run_id}/artifacts/{filename}")
def get_run_artifact(
    run_id: int,
    filename: str,
    session: Annotated[Session, Depends(get_session)],
) -> FileResponse:
    """Serve a specific image artifact from a run."""
    run = session.get(Run, run_id)
    if not run or not run.output_dir:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found or has no output dir")

    # Prevent directory traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    file_path = Path(run.output_dir) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    return FileResponse(file_path)
