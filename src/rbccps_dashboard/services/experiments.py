from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rbccps_dashboard.config import DashboardSettings, get_settings
from rbccps_dashboard.models import Experiment
from rbccps_dashboard.schemas import ExperimentCreate, ExperimentDuplicate, ExperimentUpdate
from rbccps_dashboard.services.yaml_store import YAMLStore


class ExperimentService:
    def __init__(self, session: Session, settings: DashboardSettings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.yaml_store = YAMLStore(self.settings)

    def list(self) -> list[Experiment]:
        experiments = list(self.session.scalars(select(Experiment).order_by(Experiment.updated_at.desc())))
        for experiment in experiments:
            self.refresh_snapshot(experiment)
        return experiments

    def get(self, experiment_id: int) -> Experiment:
        experiment = self.session.get(Experiment, experiment_id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {experiment_id}")
        self.refresh_snapshot(experiment)
        return experiment

    def create(self, payload: ExperimentCreate) -> Experiment:
        config_path, config_snapshot = self._prepare_config(
            name=payload.name,
            config_path=payload.config_path,
            config=None if payload.config_path and not payload.config else payload.config,
            dataset=payload.dataset,
            model_variant=payload.model_variant,
            training=payload.training,
        )
        experiment = Experiment(
            name=payload.name,
            description=payload.description,
            status=payload.status,
            config_path=config_path,
            config_snapshot=config_snapshot,
            tags=payload.tags,
        )
        self.session.add(experiment)
        self._commit()
        return experiment

    def update(self, experiment_id: int, payload: ExperimentUpdate) -> Experiment:
        experiment = self.get(experiment_id)
        changes = payload.model_dump(exclude_unset=True)
        for field in ("name", "description", "status", "tags"):
            if field in changes and changes[field] is not None:
                setattr(experiment, field, changes[field])

        config_related = {"config_path", "config", "dataset", "model_variant", "training"} & changes.keys()
        if config_related:
            config_path, config_snapshot = self._prepare_config(
                name=experiment.name,
                config_path=changes.get("config_path", experiment.config_path),
                config=changes.get("config"),
                dataset=changes.get("dataset"),
                model_variant=changes.get("model_variant") or "YOLO26m",
                training=changes.get("training") or {},
            )
            experiment.config_path = config_path
            experiment.config_snapshot = config_snapshot

        self._commit()
        return experiment

    def delete(self, experiment_id: int) -> None:
        experiment = self.get(experiment_id)
        self.session.delete(experiment)
        self.session.commit()

    def duplicate(self, experiment_id: int, payload: ExperimentDuplicate) -> Experiment:
        source = self.get(experiment_id)
        config = deepcopy(source.config_snapshot)
        config.setdefault("experiment", {})
        if isinstance(config["experiment"], dict):
            config["experiment"]["name"] = payload.name
            if payload.description is not None:
                config["experiment"]["description"] = payload.description
        target_path = self._new_config_path(payload.name)
        document = self.yaml_store.write_config(target_path, self.yaml_store.dump(config))
        experiment = Experiment(
            name=payload.name,
            description=payload.description if payload.description is not None else source.description,
            status="draft",
            config_path=document.path,
            config_snapshot=document.parsed if isinstance(document.parsed, dict) else {"value": document.parsed},
            tags=list(source.tags),
        )
        self.session.add(experiment)
        self._commit()
        return experiment

    def refresh_snapshot(self, experiment: Experiment) -> None:
        if not experiment.config_path:
            return
        try:
            document = self.yaml_store.read_config(experiment.config_path)
        except FileNotFoundError:
            return
        if isinstance(document.parsed, dict):
            experiment.config_snapshot = document.parsed
        else:
            experiment.config_snapshot = {"value": document.parsed}

    def _prepare_config(
        self,
        *,
        name: str,
        config_path: str | None,
        config: dict[str, Any] | None,
        dataset: str | None,
        model_variant: str,
        training: dict[str, Any],
    ) -> tuple[str | None, dict[str, Any]]:
        if config_path and config is None:
            document = self.yaml_store.read_config(config_path)
            parsed = document.parsed if isinstance(document.parsed, dict) else {"value": document.parsed}
            return document.path, parsed

        payload = config or self._default_config(
            name=name,
            dataset=dataset,
            model_variant=model_variant,
            training=training,
        )
        target_path = config_path or self._new_config_path(name)
        document = self.yaml_store.write_config(target_path, self.yaml_store.dump(payload))
        parsed = document.parsed if isinstance(document.parsed, dict) else {"value": document.parsed}
        return document.path, parsed

    def _default_config(
        self,
        *,
        name: str,
        dataset: str | None,
        model_variant: str,
        training: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "experiment": {
                "name": name,
                "description": "",
                "stage": "phase_1",
            },
            "dataset": {
                "config": dataset or "src/rbccps_od/config/original.yaml",
            },
            "model": {
                "variant": model_variant,
                "pretrained_weights": None,
            },
            "training": {
                "epochs": 100,
                "batch_size": 16,
                "image_size": 640,
                "learning_rate": 0.01,
                "weight_decay": 0.0005,
                "optimizer": "auto",
                "scheduler": "cosine",
                "workers": 8,
                "patience": 50,
                "seed": 42,
                "device": "auto",
                "mixed_precision": True,
                "gradient_accumulation": 1,
                **training,
            },
        }

    def _new_config_path(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "experiment"
        base = self.settings.generated_config_root
        candidate = base / f"{slug}.yaml"
        index = 2
        while candidate.exists():
            candidate = base / f"{slug}-{index}.yaml"
            index += 1
        return candidate.relative_to(self.settings.project_root).as_posix()

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise ValueError("Experiment name must be unique.") from error
