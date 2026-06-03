"""REST API routes for Tracking Viewer (Phase 3)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from rbccps_dashboard.config import get_settings

router = APIRouter(prefix="/tracking", tags=["tracking"])


def get_tracking_dir() -> Path:
    settings = get_settings()
    tracking_dir = settings.project_root / "runs" / "tracking"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    return tracking_dir


@router.get("/videos")
def list_tracking_videos() -> list[dict[str, str]]:
    """List available output videos from the tracking pipeline."""
    tracking_dir = get_tracking_dir()
    
    videos = []
    valid_extensions = {".mp4", ".avi", ".webm"}
    for file_path in tracking_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Check if there is a corresponding JSON file with trajectories
            has_json = (file_path.parent / f"{file_path.stem}.json").exists()
            videos.append({
                "filename": file_path.name,
                "has_trajectories": has_json,
                "size_bytes": file_path.stat().st_size,
            })
            
    videos.sort(key=lambda x: x["filename"])
    return videos


@router.get("/videos/{filename}")
def stream_video(filename: str) -> FileResponse:
    """Stream a tracked video file."""
    # Prevent directory traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    file_path = get_tracking_dir() / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    # FastAPI's FileResponse automatically handles HTTP Range requests (206 Partial Content)
    # which is required for video seeking in standard HTML5 players.
    return FileResponse(file_path, media_type="video/mp4")


@router.get("/trajectories/{filename}")
def get_trajectories(filename: str) -> list | dict:
    """Get tracked object JSON metadata."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    # Expecting filename to be the base name without extension, or ending in .json
    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    file_path = get_tracking_dir() / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trajectories not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
