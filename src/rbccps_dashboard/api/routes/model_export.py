"""REST API route for exporting architecture graph as model code."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any

from rbccps_dashboard.services.model_export import generate_model_code

router = APIRouter(prefix="/architecture", tags=["architecture"])


class ExportRequest(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


@router.post("/export")
def export_model(req: ExportRequest) -> Response:
    """Generate and return a PyTorch model file from the architecture graph."""
    try:
        graph = {"nodes": req.nodes, "edges": req.edges}
        code = generate_model_code(graph)
        return Response(
            content=code,
            media_type="text/x-python",
            headers={
                "Content-Disposition": "attachment; filename=custom_yolo_model.py",
            },
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {error}",
        ) from error
