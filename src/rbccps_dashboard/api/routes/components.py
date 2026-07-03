"""REST API routes for User-Defined Components (Architecture Builder Extension)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rbccps_dashboard.config import get_settings
from rbccps_dashboard.database import get_session

router = APIRouter(prefix="/components", tags=["components"])

# Regex: alphanumeric + underscores, 1-80 chars, must start with a letter
_VALID_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,79}$")


def _components_dir() -> Path:
    """Return (and ensure) the user_components directory."""
    settings = get_settings()
    d = settings.project_root / "user_components"
    d.mkdir(parents=True, exist_ok=True)
    return d


class ComponentSaveRequest(BaseModel):
    name: str
    code: str


class ComponentSummary(BaseModel):
    name: str
    filename: str


@router.get("", response_model=list[ComponentSummary])
def list_components() -> list[ComponentSummary]:
    """List all user-defined component files."""
    d = _components_dir()
    results = []
    for f in sorted(d.glob("*.py")):
        if f.name.startswith("_"):
            continue
        # Derive component name from filename (e.g. custom_conv.py → CustomConv)
        stem = f.stem
        results.append(ComponentSummary(name=stem, filename=f.name))
    return results


@router.post("", response_model=ComponentSummary, status_code=status.HTTP_201_CREATED)
def save_component(req: ComponentSaveRequest) -> ComponentSummary:
    """Save a user-defined component as a Python file."""
    name = req.name.strip()

    if not _VALID_NAME.match(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid component name. Must be alphanumeric + underscores, start with a letter, max 80 chars.",
        )

    # Convert PascalCase/camelCase to snake_case for filename
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    filename = f"{snake}.py"
    filepath = _components_dir() / filename

    # Basic security: ensure no path traversal
    if ".." in str(filepath) or not filepath.resolve().is_relative_to(_components_dir().resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path injection detected.",
        )

    filepath.write_text(req.code, encoding="utf-8")

    return ComponentSummary(name=snake, filename=filename)


@router.get("/{name}/code")
def get_component_code(name: str) -> dict[str, str]:
    """Retrieve the Python source of a user-defined component."""
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    filepath = _components_dir() / f"{snake}.py"
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Component '{name}' not found")
    return {"name": snake, "code": filepath.read_text(encoding="utf-8")}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(name: str) -> None:
    """Delete a user-defined component file."""
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    filepath = _components_dir() / f"{snake}.py"
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Component '{name}' not found")
    filepath.unlink()
