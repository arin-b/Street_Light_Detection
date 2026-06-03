"""REST API routes for Attention Maps (Phase 3)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/attention", tags=["attention"])

@router.get("/maps")
def list_attention_maps(image_id: str | None = None) -> list[dict]:
    """
    Placeholder endpoint for fetching attention maps.
    In the future, this could trigger a live forward-pass with PyTorch hooks
    to extract Geometry Attention / CSE masks for a given image.
    """
    # Mock data for frontend development
    return [
        {
            "id": "mock_attn_1",
            "layer": "Geometry Attention (Diagonal)",
            "url": "/api/attention/mock-image.png" # Placeholder
        }
    ]
