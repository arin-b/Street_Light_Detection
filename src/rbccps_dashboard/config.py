from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Find the repository root without hardcoding a workstation path."""
    env_root = os.environ.get("RBCCPS_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents, *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "rbccps_od").exists():
            return candidate.resolve()
    return Path.cwd().resolve()


@dataclass(frozen=True)
class DashboardSettings:
    project_root: Path
    database_url: str
    yaml_roots: tuple[Path, ...]
    generated_config_root: Path
    frontend_dist: Path
    runs_output_root: Path
    log_buffer_size: int

    def ensure_directories(self) -> None:
        self.generated_config_root.mkdir(parents=True, exist_ok=True)
        self.runs_output_root.mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)


def _default_database_url(project_root: Path) -> str:
    return f"sqlite:///{project_root / '.dashboard' / 'dashboard.sqlite3'}"


@lru_cache(maxsize=1)
def get_settings() -> DashboardSettings:
    project_root = find_project_root()
    generated_config_root = project_root / "configs" / "dashboard" / "experiments"
    yaml_roots = (
        project_root / "src" / "rbccps_od" / "config",
        project_root / "configs",
        generated_config_root,
    )
    database_url = os.environ.get("RBCCPS_DASHBOARD_DATABASE_URL") or _default_database_url(project_root)
    frontend_dist = project_root / "dashboard" / "frontend" / "dist"
    runs_output_root = project_root / "runs" / "dashboard"
    log_buffer_size = int(os.environ.get("RBCCPS_LOG_BUFFER_SIZE", "2000"))
    return DashboardSettings(
        project_root=project_root,
        database_url=database_url,
        yaml_roots=tuple(root.resolve() for root in yaml_roots),
        generated_config_root=generated_config_root.resolve(),
        frontend_dist=frontend_dist.resolve(),
        runs_output_root=runs_output_root.resolve(),
        log_buffer_size=log_buffer_size,
    )
