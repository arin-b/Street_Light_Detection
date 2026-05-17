# Detector Run 2: Training and Architecture Review

This note reviews the first YOLOv26 detector run and defines the next experiment before any major architecture change.

## What run 1 showed

From the `streetlight_detector_v1-2` artifacts:

- best `mAP50`: `0.49029`
- best `mAP50-95`: `0.29247`
- best checkpoint occurred at epoch `24`
- validation metrics oscillated strongly after the first 10 epochs

Interpretation:

- the model learned meaningful signal
- the detector did not collapse
- the main bottleneck is still dataset policy, especially validation and negatives
- architecture change is not yet justified as the first response

## Main run-1 bottlenecks

1. Validation was too small.
   - `48` validation images
   - `58` validation instances

2. Negative pressure was too weak.
   - only `30` background images in the train split during run 1

3. The model saw many small, vertically narrow targets with strong positional bias.
   - this encourages shortcut learning around location and shape

## Run-2 policy

Run 2 should keep the detector family fixed and change the data policy first.

Use:

- [annotation_automation_v2](F:\RBCCPS_Directory\datasets\derived\annotation_automation_v2)
- [validation_policy_v2.md](F:\RBCCPS_Directory\datasets\derived\annotation_automation_v2\reports\validation_policy_v2.md)
- [validation_and_labeling_protocol_v2.md](F:\RBCCPS_Directory\documentation\system_design\new_design\validation_and_labeling_protocol_v2.md)

## Recommended run-2 training parameters

For the next serious baseline on a `12 GB` class GPU:

- model: `yolo26m.pt`
- image size: `1280`
- batch: `4`
- epochs: `60`
- patience: `20`
- close mosaic: `10`
- workers: `8`
- cache: optional, only if storage is fast and stable

Why:

- run 1 already hit automatic OOM reduction from `8` to `4`
- fixing batch at `4` removes hidden mid-run changes
- the best checkpoint happened around epoch `24`, so `60` epochs with lower patience is enough for the next comparison
- high resolution should stay because the targets are small

## Recommended run-2 command

On Linux:

```bash
python -m rbccps_od train \
  --model datasets/yolov26_weights/yolo26m.pt \
  --data /absolute/path/to/annotation_automation_v2/yolo_dataset/dataset.yaml \
  --imgsz 1280 \
  --epochs 60 \
  --batch 4 \
  --device 0 \
  --project runs \
  --name streetlight_detector_v2 \
  --patience 20 \
  --workers 8 \
  --close-mosaic 10
```

## Architecture review

### What should not change yet

Do not change all of these before run 2:

- detector family
- backbone size
- multi-stage system design
- temporal logic
- custom heads

Reason:

- run 1 did not fail in a way that isolates architecture as the main bottleneck
- changing architecture now would mix data-policy failure with model-choice failure

### What architecture questions are worth asking after run 2

Only if run 2 still remains weak after the split fix:

1. Should training move to crop- or tile-based small-object training?
2. Should streetlight detection become a two-stage system:
   - candidate lamp detector
   - context classifier for streetlight vs distractor
3. Should temporal consistency be added after frame detection?
4. Should a larger detector be tested if compute allows?

### Most likely useful change after run 2

The first architecture change worth trying is not a bigger YOLO by default.

It is:

- high-resolution crop or tile training for small bright objects

Reason:

- the labels are tiny and spatially concentrated
- the detector likely loses detail on distant lamps

## Decision rule after run 2

If run 2 reaches roughly:

- `mAP50 >= 0.60` with improved stability:
  - keep the architecture and move to candidate export plus reliability-gate development

If run 2 remains around:

- `mAP50 <= 0.50` with unstable validation:
  - first mine more negatives
  - then test small-object tiling or crop-based training

If run 2 becomes:

- stable but recall-limited:
  - prioritize small-object and context improvements

If run 2 becomes:

- precision-limited:
  - prioritize harder negatives and distractor-specific evaluation
