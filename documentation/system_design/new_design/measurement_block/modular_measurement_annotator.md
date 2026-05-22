# Modular Measurement Annotator

The active human-interface annotator is now the modular RBCCPS annotator:

```powershell
python -m rbccps_annotator <command>
```

The previous streetlight click-review app is no longer the active product. The parking-violation annotator has been removed.

## Main Commands

Create a workspace from extracted raw frames:

```powershell
python -m rbccps_annotator ingest-frames --frames F:\path\to\frames --workspace F:\path\to\measurement_annotation_workspace
```

Create a workspace from an object-detector or measurement clip manifest:

```powershell
python -m rbccps_annotator ingest-detector-run --manifest F:\path\to\clip_manifest.json --workspace F:\path\to\measurement_annotation_workspace
```

Launch the browser UI:

```powershell
python -m rbccps_annotator serve --workspace F:\path\to\measurement_annotation_workspace
```

One-command raw-frame ingest plus launch:

```powershell
python -m rbccps_annotator launch --frames F:\path\to\frames
```

Export reviewed one-class streetlight boxes:

```powershell
python -m rbccps_annotator export-yolo --workspace F:\path\to\measurement_annotation_workspace
```

Export measurement-block supervision:

```powershell
python -m rbccps_annotator export-measurement --workspace F:\path\to\measurement_annotation_workspace
```

Generate derived confounder augmentation views:

```powershell
python -m rbccps_annotator generate-confounder-augmentations --workspace F:\path\to\measurement_annotation_workspace --probability 0.2 --variant dim
```

## Supported Modes

The browser UI is organized as a guided task flow:

- `Lamp Boxes`: streetlight box review without confounder labels.
- `Confounders`: Smart Surface and manual polygon annotation for facades, shopfronts, windows, signs, glare, and reflections.
- `Public Space`: road, footpath, crossing, and other public-space polygons.
- `Affected Region`: target-lamp affected public-space polygons.
- `Visibility`: lamp status, task visibility, and attribution labels.
- `Lux + QA`: sparse lux points and uncertainty/signoff flags.

## Magic Surface

Magic Surface is the fast polygon tool for surface/confounder annotation.

1. Choose `Mark Other Lights`.
2. Select `Magic Surface`.
3. Drag a rectangle around the building wall, shop light/front, window light, bright sign, wet-road reflection, vehicle headlights, or other bright thing.
4. Review the highlighted shape.
5. Use `Keep Shape` to convert it into a normal editable polygon, or `Try Again` to redraw.

The endpoint is:

```text
POST /api/auto-polygon
```

The backend checks for local promptable segmentation assets under:

```text
models/annotator/prompt_segmenter/
```

Install the local prompt segmenter with:

```powershell
python -m rbccps_annotator download-segmenter
```

The first installed model is `FastSAM-s.pt`, because it works with the existing Ultralytics environment and supports box prompts. If the model is not installed, the endpoint remains usable through deterministic fallback proposals and returns a simple warning in the UI. Accepted fallback polygons are marked by their `source` field, so they remain auditable.

Magic Surface proposals are checked against streetlight boxes plus the configured safety margin. If a proposal overlaps a protected streetlight box, the UI warns the reviewer before acceptance.

Manual drawing stores only simple polygons. A new line that crosses the shape is rejected, and a polygon cannot be finished if the closing line intersects the existing shape.

## Field Lux / Notes

Human reviewers must not guess lux from an image. Enter lux only if it came from a field measurement, synced metadata sheet, calibrated phone protocol, or other reference log. If there is no measured value, leave lux empty and use notes such as:

- `no_lux_reference`
- `proxy_only`
- `glare`
- `headlight_confounder`
- `shopfront_confounder`
- `wet_reflection`
- `tree_occlusion`
- `exposure_problem`

## Workspace Layout

```text
measurement_annotation_workspace/
  manifest.json
  frames.csv
  reviews/
    items/
  exports/
    yolo_standard/
    measurement_annotations/
    confounder_aug_dim/
```

The original image is always canonical. Confounder-masked images are generated views only and are linked back to the original frame through augmentation metadata.
