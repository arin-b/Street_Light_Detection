from __future__ import annotations

import argparse
import json
from pathlib import Path

from rbccps_measurement.training.readiness import check_dataset_readiness


KNOWN_MODULES = {
    "normalization",
    "status",
    "segmentation",
    "footprint",
    "source_decomposition",
    "features",
    "attribution",
    "fusion",
    "conformal",
    "photometry",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a module-training run manifest for the stronger research model.")
    parser.add_argument("--module", required=True, choices=sorted(KNOWN_MODULES))
    parser.add_argument("--dataset", required=True, help="Prepared measurement dataset root.")
    parser.add_argument("--out", required=True, help="Output training run directory.")
    parser.add_argument("--config", default=None, help="Optional training config path.")
    parser.add_argument("--dry-run", action="store_true", help="Only write the training plan manifest.")
    parser.add_argument("--skip-readiness", action="store_true", help="Do not validate dataset/model readiness before writing the plan.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    readiness = None
    if not args.skip_readiness:
        require_annotations = args.module not in {"normalization"}
        readiness = check_dataset_readiness(args.dataset, require_annotations=require_annotations, ensure_models=True)
    manifest = {
        "run_type": "module_training",
        "module": args.module,
        "dataset": str(Path(args.dataset)),
        "config": args.config,
        "status": "ready" if readiness is None or readiness.ready else "blocked",
        "dry_run": bool(args.dry_run),
        "readiness": readiness.to_dict() if readiness else None,
        "note": "This scaffold records a reproducible training run. Install PyTorch models and data-specific trainers before launching real optimization.",
    }
    (out / "training_plan.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if readiness is not None and not readiness.ready:
        print(json.dumps(manifest, indent=2))
        raise SystemExit("Training readiness failed. See training_plan.json for issues.")
    if not args.dry_run:
        checkpoint = {
            "checkpoint_type": "initialized_module_checkpoint",
            "module": args.module,
            "dataset": str(Path(args.dataset)),
            "config": args.config,
            "pretrained_assets": readiness.model_assets if readiness else {},
            "status": "initialized_not_optimized",
            "next_step": "attach module-specific PyTorch optimizer/trainer for supervised fine-tuning on collected annotations",
        }
        (out / f"{args.module}_checkpoint.json").write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        manifest["status"] = "initialized"
        manifest["checkpoint"] = f"{args.module}_checkpoint.json"
        (out / "training_plan.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
