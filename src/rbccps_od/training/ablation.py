from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from rbccps_od.training.original_dataset import PreparedOriginalDataset, prepare_original_yolo_dataset
from rbccps_od.training.yolo26m_finetune import (
    FineTuneConfig,
    WandbConfig,
    resolve_repo_path,
    resolve_yolo26m_model,
    run_yolo26m_finetune,
    save_trained_weights,
    training_kwargs,
)


@dataclass(frozen=True)
class AblationExperiment:
    name: str
    run_name: str
    artifact_name: str
    dataset_yaml: str | None = None
    uses_original_view: bool = False


EXPERIMENTS: tuple[AblationExperiment, ...] = (
    AblationExperiment(
        name="original",
        run_name="streetlight_yolo26m_original",
        artifact_name="original",
        uses_original_view=True,
    ),
    AblationExperiment(
        name="zerodce_enhanced",
        run_name="streetlight_yolo26m_zerodce_enhanced",
        artifact_name="zerodce-enhanced",
        dataset_yaml="datasets/processed/zerodce-enhanced/dataset.yaml",
    ),
    AblationExperiment(
        name="zero_dce_retinex_reflectance",
        run_name="streetlight_yolo26m_zero_dce_retinex_reflectance",
        artifact_name="zero-dce-retinex-reflectance",
        dataset_yaml="datasets/processed/zero_dce_retinex_reflectance/dataset.yaml",
    ),
    AblationExperiment(
        name="retinex_decomposition",
        run_name="streetlight_yolo26m_retinex_decomposition",
        artifact_name="retinex-decomposition",
        dataset_yaml="datasets/processed/retinex-decomposition/dataset.yaml",
    ),
)

EXPERIMENT_BY_NAME = {experiment.name: experiment for experiment in EXPERIMENTS}
EXPERIMENT_ALIASES = {
    "original": "original",
    "baseline": "original",
    "zerodce": "zerodce_enhanced",
    "zero-dce": "zerodce_enhanced",
    "zerodce-enhanced": "zerodce_enhanced",
    "zerodce_enhanced": "zerodce_enhanced",
    "zero-dce-enhanced": "zerodce_enhanced",
    "zero_dce_enhanced": "zerodce_enhanced",
    "zero-dce-retinex": "zero_dce_retinex_reflectance",
    "zero_dce_retinex": "zero_dce_retinex_reflectance",
    "zero-dce-retinex-reflectance": "zero_dce_retinex_reflectance",
    "zero_dce_retinex_reflectance": "zero_dce_retinex_reflectance",
    "retinex": "retinex_decomposition",
    "retinex-decomposition": "retinex_decomposition",
    "retinex_decomposition": "retinex_decomposition",
    "retinex-deocmposition": "retinex_decomposition",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLO26m fine-tuning ablation studies.")
    parser.add_argument(
        "experiments",
        nargs="*",
        default=["all"],
        help="Experiments to run. Use all, original, zerodce, zero-dce-retinex, or retinex.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Pretrained YOLO26m weights. Defaults to local yolo26m.pt if available, otherwise yolo26m.pt.",
    )
    parser.add_argument("--imgsz", type=int, default=1280, help="Training image size.")
    parser.add_argument("--epochs", type=int, default=60, help="Training epochs.")
    parser.add_argument("--batch", type=int, default=4, help="Batch size.")
    parser.add_argument("--device", default="0", help="Training device, e.g. 0 or cpu.")
    parser.add_argument("--project", default="runs/yolo26m_ablation", help="Ultralytics project output directory.")
    parser.add_argument(
        "--artifact-root",
        default="models/fine_tuned/yolo26m_ablation",
        help="Root where each experiment gets its own best.pt, last.pt, and metadata.json.",
    )
    parser.add_argument("--patience", type=int, default=20, help="Early-stopping patience in epochs.")
    parser.add_argument("--workers", type=int, default=8, help="Dataloader workers.")
    parser.add_argument("--cache", action="store_true", help="Enable Ultralytics dataset caching.")
    parser.add_argument("--close-mosaic", type=int, default=10, help="Disable mosaic augmentation in late epochs.")
    parser.add_argument("--exist-ok", action="store_true", help="Allow Ultralytics to reuse existing run names.")
    parser.add_argument("--wandb", action="store_true", help="Log each ablation run to Weights & Biases.")
    parser.add_argument("--wandb-project", default="rbccps-yolo26m-ablation", help="W&B project name.")
    parser.add_argument("--wandb-entity", default=None, help="Optional W&B entity/team.")
    parser.add_argument("--wandb-group", default="yolo26m-training-ablation", help="W&B group for these runs.")
    parser.add_argument(
        "--wandb-mode",
        choices=("online", "offline", "disabled"),
        default="online",
        help="W&B logging mode. Use offline on restricted networks.",
    )
    parser.add_argument(
        "--wandb-tags",
        nargs="*",
        default=["streetlight", "yolo26m", "training-ablation"],
        help="Extra W&B tags applied to every ablation run.",
    )
    parser.add_argument("--no-wandb-artifacts", action="store_true", help="Do not upload best.pt/last.pt to W&B.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip an experiment when its artifact best.pt already exists.",
    )
    parser.add_argument(
        "--original-image-dir",
        default="datasets/processed/original/images",
        help="Flat source image directory for the original baseline ablation.",
    )
    parser.add_argument(
        "--original-label-dir",
        default=None,
        help="Flat source label directory for the original baseline. Defaults to sibling labels.",
    )
    parser.add_argument(
        "--original-dataset-root",
        default="datasets/processed/original-yolo26m",
        help="Generated YOLO training view for the original baseline.",
    )
    parser.add_argument(
        "--link-mode",
        choices=("auto", "hardlink", "copy", "symlink"),
        default="auto",
        help="How to materialize the generated original dataset view.",
    )
    parser.add_argument(
        "--overwrite-original-view",
        action="store_true",
        help="Overwrite files in the generated original dataset view.",
    )
    parser.add_argument("--prepare-only", action="store_true", help="Prepare and print configs without training.")
    parser.add_argument("--dry-run", action="store_true", help="Print configs without training.")
    return parser.parse_args()


def selected_experiments(values: list[str]) -> list[AblationExperiment]:
    if not values or any(value.lower() == "all" for value in values):
        return list(EXPERIMENTS)

    selected: list[AblationExperiment] = []
    seen: set[str] = set()
    for value in values:
        key = EXPERIMENT_ALIASES.get(value.lower())
        if key is None:
            valid = ", ".join(experiment.name for experiment in EXPERIMENTS)
            raise SystemExit(f"Unknown ablation experiment '{value}'. Valid experiments: {valid}")
        if key not in seen:
            selected.append(EXPERIMENT_BY_NAME[key])
            seen.add(key)
    return selected


def _print_original_summary(prepared: PreparedOriginalDataset) -> None:
    print(f"dataset_yaml={prepared.dataset_yaml}")
    print(f"manifest={prepared.manifest}")
    for split in ("train", "valid", "test"):
        stats = prepared.stats[split]
        print(
            f"{split}: images={stats.images}, positives={stats.positives}, "
            f"negatives={stats.negatives}, boxes={stats.boxes}"
        )


def _dataset_yaml_for(experiment: AblationExperiment, args: argparse.Namespace) -> Path:
    if not experiment.uses_original_view:
        assert experiment.dataset_yaml is not None
        dataset_yaml = resolve_repo_path(experiment.dataset_yaml)
        if not dataset_yaml.exists():
            raise FileNotFoundError(f"Dataset YAML not found for {experiment.name}: {dataset_yaml}")
        print(f"dataset_yaml={dataset_yaml}")
        return dataset_yaml

    image_dir = resolve_repo_path(args.original_image_dir)
    label_dir = resolve_repo_path(args.original_label_dir) if args.original_label_dir else image_dir.parent / "labels"
    prepared = prepare_original_yolo_dataset(
        image_dir=image_dir,
        label_dir=label_dir,
        output_root=resolve_repo_path(args.original_dataset_root),
        link_mode=args.link_mode,
        overwrite=args.overwrite_original_view,
    )
    _print_original_summary(prepared)
    return prepared.dataset_yaml


def _config_for(
    experiment: AblationExperiment,
    data: Path,
    args: argparse.Namespace,
    model: str,
) -> FineTuneConfig:
    wandb_tags = tuple(dict.fromkeys([*args.wandb_tags, experiment.name, experiment.artifact_name]))
    return FineTuneConfig(
        model=model,
        data=data,
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        device=args.device,
        project=resolve_repo_path(args.project),
        name=experiment.run_name,
        patience=args.patience,
        workers=args.workers,
        cache=args.cache,
        close_mosaic=args.close_mosaic,
        exist_ok=args.exist_ok,
        wandb=WandbConfig(
            enabled=args.wandb and args.wandb_mode != "disabled",
            project=args.wandb_project,
            entity=args.wandb_entity,
            group=args.wandb_group,
            tags=wandb_tags,
            mode=args.wandb_mode if args.wandb_mode != "disabled" else None,
            log_artifacts=not args.no_wandb_artifacts,
            config={
                "ablation_experiment": experiment.name,
                "ablation_artifact_name": experiment.artifact_name,
                "dataset_yaml": str(data),
                "model_family": "YOLO26m",
                "model_parameters": 20_000_000,
            },
        ),
    )


def main() -> None:
    args = parse_args()
    experiments = selected_experiments(args.experiments)
    model = resolve_yolo26m_model(args.model)
    artifact_root = resolve_repo_path(args.artifact_root)

    for index, experiment in enumerate(experiments, start=1):
        print(f"\n[{index}/{len(experiments)}] experiment={experiment.name}")
        artifact_dir = artifact_root / experiment.artifact_name
        if args.skip_existing and (artifact_dir / "best.pt").exists():
            print(f"skipped_existing={artifact_dir / 'best.pt'}")
            continue

        data = _dataset_yaml_for(experiment, args)
        config = _config_for(experiment, data, args, model)

        print(f"model={config.model}")
        for key, value in training_kwargs(config).items():
            print(f"{key}={value}")
        print(f"artifact_dir={artifact_dir}")
        if config.wandb and config.wandb.enabled:
            print(f"wandb_project={config.wandb.project}")
            print(f"wandb_group={config.wandb.group}")
            print(f"wandb_tags={','.join(config.wandb.tags)}")
            print(f"wandb_mode={config.wandb.mode}")

        if args.prepare_only or args.dry_run:
            continue

        run = run_yolo26m_finetune(config)
        saved = save_trained_weights(run, artifact_dir)
        for key, value in saved.items():
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
