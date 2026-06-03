from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from rbccps_dashboard.config import DashboardSettings, get_settings


@dataclass(frozen=True)
class YAMLDocument:
    path: str
    content: str
    parsed: Any
    modified_at: datetime


@dataclass(frozen=True)
class YAMLSummary:
    path: str
    name: str
    size_bytes: int
    modified_at: datetime


class YAMLStore:
    def __init__(self, settings: DashboardSettings | None = None) -> None:
        self.settings = settings or get_settings()

    def list_configs(self) -> list[YAMLSummary]:
        seen: set[Path] = set()
        summaries: list[YAMLSummary] = []
        for root in self.settings.yaml_roots:
            if not root.exists():
                continue
            for path in sorted([*root.rglob("*.yaml"), *root.rglob("*.yml")]):
                resolved = path.resolve()
                if resolved in seen or not resolved.is_file():
                    continue
                seen.add(resolved)
                stat = resolved.stat()
                summaries.append(
                    YAMLSummary(
                        path=self._relative_path(resolved),
                        name=resolved.name,
                        size_bytes=stat.st_size,
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                    )
                )
        return sorted(summaries, key=lambda item: item.path)

    def read_config(self, relative_path: str) -> YAMLDocument:
        path = self._resolve_allowed(relative_path, must_exist=True)
        content = path.read_text(encoding="utf-8")
        parsed = self.parse(content)
        return YAMLDocument(
            path=self._relative_path(path),
            content=content,
            parsed=parsed,
            modified_at=datetime.fromtimestamp(path.stat().st_mtime),
        )

    def write_config(self, relative_path: str, content: str) -> YAMLDocument:
        path = self._resolve_allowed(relative_path, must_exist=False)
        self.parse(content)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return self.read_config(self._relative_path(path))

    def validate(self, content: str) -> tuple[bool, Any, str | None]:
        try:
            return True, self.parse(content), None
        except yaml.YAMLError as error:
            return False, None, str(error)

    @staticmethod
    def parse(content: str) -> Any:
        loaded = yaml.safe_load(content)
        return {} if loaded is None else loaded

    def dump(self, payload: dict[str, Any]) -> str:
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def _resolve_allowed(self, relative_path: str, must_exist: bool) -> Path:
        if not relative_path:
            raise ValueError("YAML path is required.")
        if Path(relative_path).is_absolute():
            raise ValueError("YAML path must be relative to the project root.")
        if Path(relative_path).suffix.lower() not in {".yaml", ".yml"}:
            raise ValueError("Only .yaml and .yml files are editable.")

        path = (self.settings.project_root / relative_path).resolve()
        allowed = any(self._is_relative_to(path, root) for root in self.settings.yaml_roots)
        if not allowed:
            raise ValueError(f"YAML path is outside editable config roots: {relative_path}")
        if must_exist and not path.exists():
            raise FileNotFoundError(relative_path)
        return path

    def _relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.settings.project_root).as_posix()

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
