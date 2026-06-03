from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from rbccps_dashboard.config import DashboardSettings
from rbccps_dashboard.database import init_db, make_engine, make_session_factory
from rbccps_dashboard.schemas import ExperimentCreate, ExperimentDuplicate
from rbccps_dashboard.services.experiments import ExperimentService


def make_settings(root: Path) -> DashboardSettings:
    config_root = root / "src" / "rbccps_od" / "config"
    generated_root = root / "configs" / "dashboard" / "experiments"
    config_root.mkdir(parents=True)
    generated_root.mkdir(parents=True)
    (config_root / "original.yaml").write_text(
        "path: datasets/processed/original-yolo26m\ntrain: images/train\nnc: 2\n",
        encoding="utf-8",
    )
    return DashboardSettings(
        project_root=root,
        database_url=f"sqlite:///{root / '.dashboard' / 'dashboard.sqlite3'}",
        yaml_roots=(config_root.resolve(), (root / "configs").resolve(), generated_root.resolve()),
        generated_config_root=generated_root.resolve(),
        frontend_dist=(root / "dashboard" / "frontend" / "dist").resolve(),
    )


def test_experiment_service_creates_generated_yaml(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    engine = make_engine(settings)
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        service = ExperimentService(session, settings)
        experiment = service.create(
            ExperimentCreate(
                name="Retinex Trial",
                description="smoke",
                dataset="src/rbccps_od/config/original.yaml",
                training={"epochs": 3, "batch_size": 2},
            )
        )

        assert experiment.id is not None
        assert experiment.config_path == "configs/dashboard/experiments/retinex-trial.yaml"
        assert (tmp_path / experiment.config_path).exists()
        assert experiment.config_snapshot["training"]["epochs"] == 3


def test_experiment_service_duplicates_config(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    engine = make_engine(settings)
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        service = ExperimentService(session, settings)
        original = service.create(ExperimentCreate(name="Baseline"))
        duplicate = service.duplicate(original.id, ExperimentDuplicate(name="Baseline Copy"))

        assert duplicate.name == "Baseline Copy"
        assert duplicate.config_path == "configs/dashboard/experiments/baseline-copy.yaml"
        assert duplicate.config_snapshot["experiment"]["name"] == "Baseline Copy"
