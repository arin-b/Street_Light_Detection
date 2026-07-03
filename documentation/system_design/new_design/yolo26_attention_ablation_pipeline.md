# YOLO26 Attention Ablation Pipeline

This pipeline implements the first two executive-summary modifications only:

- Negative Attention Mask: a learned suppression branch predicts distractor/background attention maps and adds `Ldet + lambda * Lmask` during training.
- Geometry-Aware Attention: a lightweight vertical/horizontal spatial attention block reweights YOLO detect-head features.

Dual-task segmentation and symmetry consistency loss are intentionally not implemented here. The measurement pipeline is unchanged.

## Modules

The ablation switches are independent:

- `baseline`: no added modules.
- `geometry`: adds geometry-aware attention.
- `cse`: adds the existing channel squeeze excitation module.
- `geometry_cse`: combines geometry attention and CSE.
- `negative`: adds learned negative attention and mask BCE.
- `negative_cse`: combines negative attention and CSE.
- `negative_geometry`: combines negative attention and geometry attention.
- `all_modules`: combines negative attention, geometry attention, and CSE.

## Negative Mask Targets

Use `--negative-mask-root` for manually annotated distractor masks. Each mask should be binary or grayscale, with positive pixels marking regions the detector should suppress: road, vehicles, building windows, interfering lights, and other known non-streetlight distractors.

Supported formats are `.png`, `.jpg`, `.jpeg`, `.npy`, and `.pt`.

Mask lookup supports either:

- Same-stem files: `masks/frame_001.png` for `images/train/frame_001.jpg`.
- Split-mirrored files: `masks/train/frame_001.png` for `images/train/frame_001.jpg`.

By default, negative-mask runs disable YOLO geometric augmentations because external mask files cannot receive the same random mosaic, flip, scale, and crop transforms as the image. Pass `--allow-mask-unsafe-augmentations` only if your custom dataset already supplies transformed `negative_mask` tensors.

## Training

Run the default stage-1 grid:

```bash
streetlight-env/bin/python scripts/train_yolo26m_ablation.py original --cases stage1
```

Run the negative-mask grid:

```bash
streetlight-env/bin/python scripts/train_yolo26m_ablation.py original \
  --cases stage2 \
  --negative-mask-root datasets/negative_masks \
  --negative-mask-loss-weight 1.0
```

Run one custom ablation:

```bash
streetlight-env/bin/python scripts/train_yolo26m_ablation.py original \
  --single-run \
  --use-negative \
  --use-geometry \
  --use-cse \
  --negative-mask-root datasets/negative_masks \
  --negative-mask-loss-weight 0.5
```

Generate the full W&B sweep grid:

```bash
streetlight-env/bin/python scripts/train_yolo26m_ablation.py --print-wandb-sweep
```

Each run saves `best.pt`, `last.pt`, and metadata under `models/fine_tuned/yolo26m_ablation/<data_variant>__<case>/`.

## Inference And Audit

Use the same module flags at audit time that were used for training the checkpoint:

```bash
streetlight-env/bin/python -m audit_pipeline.run_audit \
  --video /path/to/video.mp4 \
  --model models/fine_tuned/yolo26m_ablation/original__negative-geometry-cse/best.pt \
  --use-negative-attention \
  --use-geometry-attention \
  --use-cse
```

For a geometry-only checkpoint:

```bash
streetlight-env/bin/python -m audit_pipeline.run_audit \
  --video /path/to/video.mp4 \
  --model models/fine_tuned/yolo26m_ablation/original__geometry/best.pt \
  --use-geometry-attention
```

Negative attention does not require masks at inference. The suppression branch predicts its own attention map and suppresses feature activations before YOLO detection. The existing tracking, multi-cue filtering, measurement, aggregation, evaluation, and report generation stages run after detection without measurement-code changes.
