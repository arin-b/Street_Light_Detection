from argparse import Namespace
from pathlib import Path

from rbccps_od.training.ablation import EXPERIMENT_BY_NAME, _config_for, selected_experiments


def test_selected_experiments_defaults_to_all():
    assert [experiment.name for experiment in selected_experiments(["all"])] == [
        "original",
        "zerodce_enhanced",
        "zero_dce_retinex_reflectance",
        "retinex_decomposition",
    ]


def test_selected_experiments_accepts_aliases_and_typo():
    assert [experiment.name for experiment in selected_experiments(["zerodce", "retinex-deocmposition"])] == [
        "zerodce_enhanced",
        "retinex_decomposition",
    ]


def test_config_for_adds_wandb_ablation_metadata(tmp_path: Path):
    args = Namespace(
        imgsz=1280,
        epochs=60,
        batch=4,
        device="0",
        project=str(tmp_path / "runs"),
        patience=20,
        workers=8,
        cache=False,
        close_mosaic=10,
        exist_ok=False,
        wandb=True,
        wandb_mode="offline",
        wandb_project="streetlight-tests",
        wandb_entity=None,
        wandb_group="ablation-tests",
        wandb_tags=["streetlight", "yolo26m"],
        no_wandb_artifacts=False,
    )

    config = _config_for(
        EXPERIMENT_BY_NAME["zerodce_enhanced"],
        tmp_path / "dataset.yaml",
        args,
        "yolo26m.pt",
    )

    assert config.wandb is not None
    assert config.wandb.enabled is True
    assert config.wandb.project == "streetlight-tests"
    assert "zerodce_enhanced" in config.wandb.tags
    assert config.wandb.config["ablation_experiment"] == "zerodce_enhanced"
    assert config.wandb.config["model_parameters"] == 20_000_000
