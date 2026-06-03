from __future__ import annotations

from pathlib import Path

import pytest

from rbccps_dashboard.config import DashboardSettings
from rbccps_dashboard.services.yaml_store import YAMLStore


def make_settings(root: Path) -> DashboardSettings:
    config_root = root / "src" / "rbccps_od" / "config"
    generated_root = root / "configs" / "dashboard" / "experiments"
    config_root.mkdir(parents=True)
    generated_root.mkdir(parents=True)
    return DashboardSettings(
        project_root=root,
        database_url=f"sqlite:///{root / '.dashboard' / 'dashboard.sqlite3'}",
        yaml_roots=(config_root.resolve(), (root / "configs").resolve(), generated_root.resolve()),
        generated_config_root=generated_root.resolve(),
        frontend_dist=(root / "dashboard" / "frontend" / "dist").resolve(),
    )


def test_yaml_store_reads_lists_and_writes_allowed_configs(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    config = tmp_path / "src" / "rbccps_od" / "config" / "original.yaml"
    config.write_text("path: datasets/processed/original-yolo26m\nnc: 2\n", encoding="utf-8")

    store = YAMLStore(settings)
    summaries = store.list_configs()

    assert [item.path for item in summaries] == ["src/rbccps_od/config/original.yaml"]
    document = store.read_config("src/rbccps_od/config/original.yaml")
    assert document.parsed["nc"] == 2

    written = store.write_config("configs/dashboard/experiments/smoke.yaml", "experiment:\n  name: smoke\n")
    assert written.parsed == {"experiment": {"name": "smoke"}}


def test_yaml_store_rejects_paths_outside_config_roots(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    store = YAMLStore(settings)

    with pytest.raises(ValueError):
        store.write_config("README.yaml", "name: nope\n")
