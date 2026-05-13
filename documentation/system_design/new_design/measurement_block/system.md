# Verbatim System-Solution Extracts for Measurement Block

This file contains **word-for-word extracts** from the literature reviews in:

- `litreview_claude.md`
- `litreview_gemini.md`
- `litreview_gpt5.4.md`
- `litreview_gpt5.5.md`

The excerpts below were selected specifically for **potential system solutions**, including suggestions that were **buried inside the reviews** and not only those listed as explicit recommendations.

---

## 1. Extracts from `litreview_claude.md`

### 1.1 Proposed Technical Formulation for "Useful Illumination"

## 9. Proposed Technical Formulation for "Useful Illumination"

### 9.1 Definition

Let **S(l, t)** denote the useful illumination score for lamp *l* at time *t* (averaged over a video clip). S âˆˆ [0, 1].

$$S(l, t) = w_1 \cdot C(l,t) + w_2 \cdot A(l,t) + w_3 \cdot U(l,t) - w_4 \cdot G(l,t) + w_5 \cdot F(l,t)$$

Where:

- **C(l,t)** = Coverage: fraction of the inferred ground-plane footprint of lamp *l* with estimated relative brightness â‰¥ minimum threshold. âˆˆ [0,1].
- **A(l,t)** = Adequacy: a soft indicator that estimated absolute illuminance in the footprint exceeds the applicable BIS IS 1944 / CIE threshold. âˆˆ [0,1].
- **U(l,t)** = Uniformity proxy: 1 âˆ’ normalized variance of brightness across the footprint. âˆˆ [0,1].
- **G(l,t)** = Glare penalty: proportion of lamp pixels that are saturated above the exposure-normalized ceiling (proxy for disability glare). âˆˆ [0,1].
- **F(l,t)** = Functional score: 1 if working, 0.5 if dim/flickering, 0 if off/occluded. âˆˆ {0, 0.5, 1}.
- **w_1, ..., w_5** = weights learned from ground-truth lux data and human ratings (initial defaults: 0.25, 0.30, 0.15, 0.10, 0.20).

### 9.2 Operationalization

**C(l,t):** Define the footprint by projecting the lamp bounding box onto the ground plane using estimated homography or monocular depth. Segment the ground-plane region. Count the fraction of pixels with relative brightness (after exposure normalization) above a learnable threshold Ï„_C.

**A(l,t):** Using exposure normalization from EXIF (when available) or from temporal self-calibration (across frames with different exposures), estimate an absolute brightness proxy. Map this to a soft probability that E_avg â‰¥ E_standard (2 lux for footpath, 4 lux for local road, etc.). The mapping is learned from calibration data.

**U(l,t):** For the footprint pixels, compute the normalized standard deviation of exposure-normalized brightness: 1 âˆ’ Ïƒ(brightness) / mean(brightness). Clip to [0,1].

**G(l,t):** Count the fraction of pixels in the lamp bounding box that are saturated (value â‰¥ 0.95 Ã— max after exposure normalization). This is a proxy for luminous intensity at the observer's eye.

**F(l,t):** From the lamp status classification sub-network.

### 9.3 Justification

- **C and A together** approximate the CIE definition of minimum illuminance compliance.
- **U** approximates overall uniformity U_0.
- **G** approximates a simple glare penalty.
- **F** accounts for lamp failure modes.
- The weighted sum collapses these to a single score for simplicity, but the components can be reported separately for diagnostic purposes.

### 1.2 Candidate Model Architecture

## 10. Candidate Model Architectures

### 10.1 Architecture Overview

The full pipeline consists of five sequential and partially parallel modules:

```
Video Frames
    â”‚
    â”œâ”€â”€[Module 1: Lamp Detection & Tracking]
    â”‚      MobileNetV3 + YOLOv8n + ByteTrack
    â”‚      Output: lamp bounding boxes + track IDs
    â”‚
    â”œâ”€â”€[Module 2: Lamp Status Classification]
    â”‚      Temporal CNN on lamp crop (flicker, dim, off)
    â”‚      Input: lamp crop sequence (10 frames)
    â”‚
    â”œâ”€â”€[Module 3: Ground-Plane Segmentation]
    â”‚      BiSeNet / Fast-SCNN (night-adapted)
    â”‚      Output: road/sidewalk/curb pixel mask
    â”‚
    â”œâ”€â”€[Module 4: Illumination Footprint Estimation]
    â”‚      Homography + depth estimate â†’ project lamp to ground
    â”‚      Compute brightness gradient in footprint region
    â”‚
    â”œâ”€â”€[Module 5: Exposure Normalization]
    â”‚      EXIF-based or self-calibrating temporal normalizer
    â”‚      Exposure-normalized radiance proxy
    â”‚
    â””â”€â”€[Module 6: Score Fusion]
           Learned MLP (small)
           Inputs: C, A, U, G, F + context features
```

### 1.3 Recommended First Prototype

## 16. Recommended First Prototype

### 16.1 Scope

A minimal viable system addressing the core problem, deployable within 6 months on a single research team.

### 16.2 Specifications

- **Input:** Night-time video from a smartphone (Android) mounted on a vehicle at 10â€“20 km/h.
- **Output:** Per-lamp JSON report: {lamp_id, timestamp, GPS, status, brightness_proxy, coverage_proxy, useful_illumination_category: ["Good", "Adequate", "Poor", "Dark"]}.
- **Platform:** Android app with TFLite backend.

### 16.3 Model

1. **Lamp Detection:** YOLOv8n, fine-tuned on 2,000 manually annotated night images from 3 Indian cities.
2. **Lamp Status:** Simple temporal classifier (5-frame flicker detection + brightness threshold for dim classification).
3. **Ground-Plane Segmentation:** Fast-SCNN pre-trained on Cityscapes + fine-tuned on Dark Zurich + 500 Indian night images.
4. **Exposure Normalization:** EXIF-based (Android Camera2 API; capture_request.get(CaptureResult.SENSOR_EXPOSURE_TIME) and SENSOR_SENSITIVITY).
5. **Footprint:** Approximate: project lower 1/3 of lamp bounding box downward to image bottom using vanishing point; define footprint as horizontal strip below lamp.
6. **Score:** Logistic regression on [coverage_proxy, status, brightness_proxy, uniformity_proxy]; trained on 200 clip-lamp pairs with manual lux ground truth.

### 16.4 Ground Truth for Prototype

- Collect 20 road segments in Bengaluru (Karnataka), 3â€“4 phone models.
- Lux measurements at lamp base, midpoint, and inter-lamp points using Sekonic L-308X.
- 500 lamp-clip pairs, 100 with ground-truth lux.

### 16.5 Expected Performance

- Lamp status classification: F1 ~0.82 (based on Yau 2020 baseline).
- Binary adequacy classification (good vs. poor): Accuracy ~0.72 (conservative estimate given limited calibration).
- Coverage proxy mIoU: ~0.52 (large uncertainty due to simplified footprint model).
- On-device latency: ~120 ms/frame on Snapdragon 695.

### 1.4 Recommended Long-Term Research Direction

## 17. Recommended Long-Term Research Direction

### 17.1 Phase 1 (Year 1): Data and Baseline

- Build the proposed dataset (Section 11) across 5 Indian cities.
- Establish baselines (Section 12.5).
- Validate exposure normalization methodology.

### 17.2 Phase 2 (Year 2): Full Model

- Train all 6 modules end-to-end on the full dataset.
- Introduce synthetic augmentation (DIALux â†’ Blender rendering pipeline).
- Add camera-to-camera calibration transfer mechanism (few-shot per-device adaptation with a 30-second calibration clip using a gray card).

### 17.3 Phase 3 (Year 3): Generalization

- Extend to crowdsourced deployment: passive monitoring from commuters' phones.
- Connect to GIS (OpenStreetMap lamp locations) for prior-informed footprint estimation.
- Validate against EN 13201 Part 4 compliance measurements on a subset of roads.
- Extend to lamp-health analytics: predict maintenance priority from illumination degradation trajectory.

### 17.4 Ultimate Goal

A crowdsourced, city-scale, real-time road-lighting quality map derived from ordinary phone video collected passively by commuters, vehicles, and safety walkers â€” without any dedicated sensors. Updated nightly, covering every street, prioritizing maintenance by predicted safety impact.

### 1.5 Three System Formulations

### Formulation 1: Standards-Driven Calibrated Photometric Estimator

#### 1. Input
- Smartphone video with EXIF per-frame metadata (exposure time t_e, ISO g, focal length f).
- One-time per-device calibration sequence: 30-second clip of a gray reference card under a known light source (lux meter verified).
- Optional: GPS + heading + lamp type metadata from OSM.

#### 2. Output
- Per-lamp physical estimates: ÃŠ_avg (lux), LÌ‚_avg (cdÂ·mâ»Â², if qD table available), Ã›_0 (uniformity), Äœ (glare index proxy).
- Comparison against BIS IS 1944 / CIE 115 thresholds.
- Compliance report: Pass/Fail per metric.

#### 3. Ground Truth Needed
- Per-lamp lux measurements (Sekonic or equivalent) at 5+ points in footprint.
- Full EN 13201 Part 4 compliance measurements on a validation subset.
- Per-device CRF and vignetting calibration from controlled lab setup.

#### 4. Literature Support
- Ishida et al. (2021): Proof of concept for calibrated camera photometry.
- Sarkar et al. (2018): Smartphone luminance from EXIF.
- Debevec & Malik (1997): CRF estimation from multiple exposures.
- BIS IS 1944, CIE 115, EN 13201: Standard targets.

#### 5. Why It May Work
In the best case â€” a phone with reliable EXIF, locked exposure, consistent CRF, and a one-time calibration â€” the system can achieve within 20â€“30% MAPE of true illuminance. This is borderline acceptable for a compliance screening tool (not for precise audit, but for identifying clear failures).

#### 6. Why It May Fail
Auto-exposure: if the phone automatically adjusts exposure between frames (common in Android default video mode), EXIF metadata changes every frame, and the CRF assumption breaks down. ISP HDR tone mapping is applied after the claimed exposure settings, making the effective CRF state-dependent. Most commercial phones do not provide RAW video output. Night mode processing renders all radiometric models invalid.

**Assessment: Very high risk of failure with standard phone video. Feasible only with manual exposure lock and RAW output â€” options not available on most users' phones.**

#### 7. How to Evaluate
- MAPE of ÃŠ_avg vs. Sekonic reference over held-out road segments.
- Compliance classification accuracy (Pass/Fail vs. EN 13201 reference).
- Cross-device MAPE difference.

#### 8. On-Device Feasibility
Partial. EXIF reading, exposure normalization, and simplified CRF inversion are computationally trivial. The geometric footprint projection and illuminance integration are fast. The challenge is software: obtaining reliable per-frame EXIF in Android video is non-trivial (requires Camera2 API with manual capture session, not the standard video recording API). Not feasible for a passive monitoring app; feasible for a dedicated research-grade app with user-guided setup.

### Formulation 2: Weakly Calibrated Visual-Usefulness Score

#### 1. Input
- Uncalibrated night-time video from any smartphone.
- No EXIF required (but used if available).
- A small weakly supervised training set: phone video clips with corresponding mean lux measurements at approximately known ground points (does not require precise point-by-point ground truth).

#### 2. Output
- Ordinal usefulness label per lamp per clip: {5: Excellent (>15 lux), 4: Good (8â€“15 lux), 3: Adequate (3â€“8 lux), 2: Poor (1â€“3 lux), 1: Dark (<1 lux)}.
- Continuous score S âˆˆ [0,1] mapped from ordinal label.
- Lamp status (working/dim/flickering/off/occluded).

#### 3. Ground Truth Needed
- ~500 clip-lamp pairs with mean lux measurements (not full spatial maps).
- Manual ordinal usefulness labels from trained annotators (backed by lux reading).
- Phone model metadata for cross-device generalization.

#### 4. Literature Support
- Yau et al. (2020): CNN-based lamp status from phone images.
- NightCity, Dark Zurich: Night-time feature representations.
- Fotios et al. (2019): Empirical thresholds for pedestrian visibility.
- PeÃ±a-GarcÃ­a et al. (2015): Perceived safety vs. illuminance.
- BIS IS 1944: Indian lux thresholds for ordinal scale anchoring.

#### 5. Why It May Work
The ordinal classification task is significantly easier than physical regression. A CNN trained on phone video features can learn to distinguish "very bright road" from "dark road" from "moderate road" even without absolute calibration, because relative brightness differences between classes are large enough to be distinguished visually despite auto-exposure variation. The auto-exposure, in fact, may partially help here: very bright lamps will saturate the image (clipped pixels at maximum value); very dark roads will have high noise. These visual patterns are real class signatures that a classifier can learn. Weak supervision (approximate lux means, not point-by-point maps) is sufficient for ordinal label assignment.

#### 6. Why It May Fail
Cross-device generalization: if training data covers only 3 phone models, a 4th phone with a different ISP may produce images that look different enough to degrade accuracy. The ordinal boundaries (especially the Adequate/Poor boundary at ~3 lux) are close to the auto-exposure decision boundary â€” phones will try to expose the 3-lux scene to look "well-exposed," making it indistinguishable from the 10-lux scene. This is the hardest failure mode to mitigate without some form of exposure information.

**Assessment: Most feasible formulation. High probability of achieving useful accuracy for gross discrimination (Good vs. Dark) with moderate effort. Fine discrimination (Adequate vs. Poor) requires more care.**

#### 7. How to Evaluate
- Macro-F1 on 5-class ordinal prediction.
- Rank correlation Ï with true lux measurements.
- Binary Adequate/Inadequate accuracy (primary safety-relevant metric).
- Cross-city and cross-device generalization tests.

#### 8. On-Device Feasibility
Yes. A single CNN of ~5M parameters for combined lamp detection, status classification, and usefulness scoring is feasible at 10â€“15 FPS on mid-range Android phones (Snapdragon 695, 4 GB RAM) with INT8 quantization.

### Formulation 3: Hybrid On-Device Model

#### 1. Input
- Night-time video from any smartphone (EXIF read if available, optional).
- 5â€“30 second clip per lamp observation.
- Optional: GPS, compass heading, phone model string.

#### 2. Output
Per lamp per clip, a structured report:
```json
{
  "lamp_id": "L_042",
  "timestamp": "2025-11-14T21:32:10",
  "gps": [12.9716, 77.5946],
  "status": "dim",
  "useful_illumination_score": 0.41,
  "components": {
    "coverage": 0.55,
    "adequacy": 0.30,
    "uniformity": 0.68,
    "glare_penalty": 0.05,
    "functional": 0.50
  },
  "illuminated_area_fraction": 0.55,
  "estimated_lux_category": "Poor (1-3 lux)",
  "standard_comparison": "Below BIS IS 1944 Category III minimum (4 lux)",
  "confidence": 0.72,
  "flags": ["dim_lamp", "partial_vegetation_occlusion"]
}
```

---

## 2. Extracts from `litreview_gemini.md`

### 2.1 Proposed Technical Formulation for "Useful Illumination"

## **9\. Proposed Technical Formulation for "Useful Illumination"**

The concept of "Useful Illumination" (![][image8]) for a tracked streetlight is formulated not as a physical unit, but as a calibrated, continuous scalar index ranging from 0 to 1\. It is optimized to represent structural visibility and pedestrian reassurance. Given a tracked luminaire ![][image9], the metric is computed over the semantically segmented public space region ![][image10] (e.g., road, sidewalk) projected onto a Structure-from-Motion estimated ground plane.

The usefulness index ![][image8] is a function of three normalized, mathematically decoupled components: Effective Coverage (![][image11]), Spatial Uniformity (![][image12]), and a Glare Penalty (![][image13]).

1. **Effective Coverage (![][image11]):** To bypass unknown absolute exposure, the algorithm computes an exposure-invariant pseudo-luminance profile using localized temporal aggregation. ![][image11] represents the proportion of the region ![][image10] where the relative pixel intensity (extracted from the HSV V-channel) exceeds a dynamically calculated local noise floor, strictly omitting any transient components classified as moving vehicle headlights through optical flow masking.  
2. **Spatial Uniformity (![][image12]):** Drawing directly from Fotios's findings that spatial uniformity predicts perceived safety better than average illuminance, ![][image12] is calculated as the ratio of the 10th percentile intensity (![][image14]) to the median intensity (![][image15]) within the illuminated footprint of ![][image10].  
3. **Glare Penalty (![][image13]):** Inspired by the Threshold Increment (TI), this penalty is proportional to the integrated intensity of the saturated, overexposed pixels at the source of the luminaire, weighted inversely by its angular distance to the primary visual task area (e.g., the vanishing point of the road).

The final formulation is expressed as:

![][image16]

where the weights ![][image17] are learned via weak supervision against a dataset containing ground-truth lux mappings and human subjective visibility scores. This target is scientifically defensible because it utilizes the uncalibrated digital camera purely as a relative contrast, geometric distribution, and spatial uniformity sensorâ€”tasks for which uncalibrated sensors are highly suitedâ€”while eschewing fraudulent claims of absolute radiometric accuracy.

### 2.2 Candidate Model Architectures

## **10\. Candidate Model Architectures**

Deploying this multi-stage inference pipeline on-device necessitates an extremely efficient architecture that bypasses memory bandwidth bottlenecks. A two-stream, dual-branch networkâ€”adapted from the principles of BiSeNetV2 and Fast-SCNNâ€”is the most plausible paradigm for real-time mobile execution.

The architecture, designated here as the *Light-Utility Extraction Network (LUENet)*, accepts a short temporal buffer of frames (e.g., ![][image18]) and pre-computed optical flow. A shared lightweight backbone (such as MobileNetV3 or EfficientNet-Lite) extracts foundational features. The network then bifurcates:

* **The Semantic Branch:** Utilizes deep, narrow convolutions with aggressive downsampling to achieve high-level scene parsing. It segments the image into drivable areas, sidewalks, structures, and dynamic objects. This branch provides the spatial boundaries for region ![][image10] and estimates the vanishing point for perspective correction.  
* **The Illumination Branch:** Utilizes shallow, wide convolutions to preserve high-resolution spatial intensity gradients. Crucially, it incorporates an Attention-based Decoupling Module to actively suppress and mask regions identified by the optical flow as containing transient light from headlights.

The outputs of both branches are fused using a bilateral aggregation layer. An auxiliary tracking head utilizes a Kalman filter to maintain the bounding box of the luminaire across frames, while a lightweight regression head computes the final ![][image8] score based on the fused semantic-illumination tensor. To conform to strict mobile constraints, the model must be quantized to INT8 using frameworks like TensorFlow Lite or Apple Core ML, leveraging dedicated NPU circuitry to achieve sub-50ms inference latency.

### 2.3 Dataset / Ground Truth / Buried System Suggestions

## **11\. Dataset and Ground-Truth Collection Plan**

The creation of a novel, specialized dataset is imperative. Existing datasets like NightCity and IDD lack localized ground-truth photometric data mapped to specific streetlights, rendering them insufficient for end-to-end training of the ![][image8] score. The proposed *Indian Night-time Illumination and Reassurance Dataset (INIRD)* must capture the unstructured nature of Indian urban roads while establishing rigorous psychophysical and physical ground truth.

**Collection Protocol:**

1. **Hardware Matrix:** Data collection vehicles and pedestrian surveyors will be equipped with diverse consumer smartphones (representing Apple, Samsung, and budget Android ISP profiles) mounted alongside a calibrated reference luminance camera (ILMD) and a lux meter array.  
2. **Physical Ground Truth:** Technicians will utilize a grid-based sampling protocol conforming to IS 1944 standards to record physical horizontal and semi-cylindrical illuminance at 5-meter intervals around selected representative streetlights.  
3. **Subjective Ground Truth:** To capture the crucial reassurance metric, a demographically diverse cohort will evaluate the sampled locations using the day-dark differential method, scoring the perceived safety, visibility, and disability glare on a 5-point Likert scale.  
4. **Data Synchronization:** GPS timestamps will sync the mobile video frames with the physical grid measurements and subjective scores.  
5. **Annotation:** The dataset will feature bounding boxes for luminaires, precise polygon masks for transient light cones (headlights), and pixel-wise semantic masks for public spaces.

### 2.4 Recommended First Prototype

## **16\. Recommended First Prototype**

The initial prototype should constrain the problem space to maximize the probability of success. It should be a localized application operating on a controlled set of devices (e.g., fixed hardware profiles like specific iPhone models). It will utilize a Fast-SCNN backbone to segment the road and sidewalk. A classical optical flow module (e.g., Lucas-Kanade) will mask out moving light blobs. The system will track a single user-tapped streetlight and calculate a simplified Uniformity Index based strictly on the variance of the V-channel intensity within the segmented, unmasked road area over a 30-frame temporal window. This avoids complex 3D ground plane estimation while proving the viability of on-device transient light rejection and spatial uniformity calculation.

### 2.5 Recommended Long-Term Research Direction

## **17\. Recommended Long-Term Research Direction**

The long-term trajectory must move towards foundational vision models adapted for inverse rendering. The ultimate goal is to process the video stream not merely as a 2D canvas, but as a dynamic physics simulation. Future research should leverage lightweight, on-device Neural Radiance Fields (NeRFs) or 3D Gaussian Splatting optimized for mobile hardware, allowing the network to explicitly model the position, orientation, and emission profile of the light source, and simulate how that light interacts with the explicitly decoupled physical geometry of the urban environment.

### 2.6 Final System Formulations

#### **Formulation 1: A Standards-Driven Calibrated Photometric Estimator**

1. **What input it requires:** Monocular night-time video, strict fixed-exposure metadata (ISO, shutter speed, aperture), camera intrinsic matrices, and pre-calibrated Camera Response Functions (CRF) specific to the smartphone model.  
2. **What output it gives:** An absolute mapping of horizontal illuminance (lux) and luminance (![][image1]) overlaid onto a top-down projected ground-plane grid, directly comparable to IS 1944 / EN 13201 standards.  
3. **What ground truth it needs:** High-density measurements utilizing certified ILMDs and lux meters across calibrated test tracks.  
4. **What literature supports it:** Derived from traditional photometric mapping systems 1 and reconstruction-based calibration paradigms.8  
5. **Why it may work:** If the hardware variables are rigorously controlled, the physics of light transport dictates that image irradiance can be mathematically mapped back to scene radiance.  
6. **Why it may fail:** It demands total control over the smartphone's ISP, disabling auto-exposure and tone-mapping. Such control is often restricted by mobile operating systems, making it highly fragile and unsuitable for unconstrained crowdsourcing.  
7. **How it can be evaluated:** Mean Absolute Error (MAE) of the estimated lux values against the physical lux meter grid.  
8. **Whether it is feasible on-device:** High processing feasibility, but practically impossible to deploy at scale due to the rigid calibration prerequisites.

#### **Formulation 2: A Weakly Calibrated Visual-Usefulness Score**

1. **What input it requires:** Uncalibrated, auto-exposure night-time mobile video without any requirement for physical hardware metadata.  
2. **What output it gives:** A categorical or ordinal "Usefulness Rating" (e.g., 1 to 5 stars) assessing how well the lamp illuminates the target area for pedestrian safety and visibility.  
3. **What ground truth it needs:** Human subjective scores collected via the day-dark differential method combined with sparse anchor points of physical lux data to ensure extreme cases anchor the scale.  
4. **What literature supports it:** Grounded in Fotios's pedestrian reassurance research 37 and exposure-aware semantic segmentation.42  
5. **Why it may work:** Deep neural networks are exceptional at learning complex, non-linear mappings from degraded inputs to subjective human annotations without requiring the intermediate step of physical physics simulations.  
6. **Why it may fail:** The model acts as a "black box," making it difficult to debug if the network starts correlating usefulness with confounding variables (e.g., rating a street highly just because an illuminated billboard is present).  
7. **How it can be evaluated:** Spearman's rank correlation coefficient and classification accuracy against the hold-out dataset of human subjective ratings.  
8. **Whether it is feasible on-device:** Highly feasible. A lightweight CNN, heavily quantized, can perform this end-to-end regression efficiently on modern NPUs.

#### **Formulation 3: A Hybrid On-Device Multi-Stage Pipeline**

1. **What input it requires:** Uncalibrated mobile video and associated IMU sensor data.  
2. **What output it gives:** A composite, continuous ![][image8] metric that mathematically balances effective area coverage, spatial uniformity, and a glare/TI penalty.  
3. **What ground truth it needs:** Multi-modal datasets containing pixel-wise semantic masks, bounding boxes for transient light sources, and physical 3D point clouds to validate the ground-plane projection.  
4. **What literature supports it:** Synthesizes SfM ground-plane estimation (GHOST) 64, active light decoupling (AutoWeather4D concepts) 52, and dual-branch mobile segmentation (BiSeNetV2).59  
5. **Why it may work:** It deconstructs the problem into verifiable sub-tasks. By projecting the relative intensity onto a mathematically estimated ground plane and explicitly masking out transient headlights via optical flow, it constructs an exposure-invariant physical proxy of the scene.  
6. **Why it may fail:** The pipeline is computationally complex. Cascading errors can occur; if the semantic branch fails to find the road boundaries accurately, the uniformity calculation over that erroneous area becomes meaningless.  
7. **How it can be evaluated:** Multi-faceted metric evaluation: Intersection over Union (IoU) for the transient light masking, reprojection error for the ground-plane estimation, and a correlation metric for the final composite score.  
8. **Whether it is feasible on-device:** Challenging but feasible. Requires sophisticated model optimization, pipeline pipelining, and strict latency budgeting to operate within the constraints of edge hardware.

---

## 3. Extracts from `litreview_gpt5.4.md`

### 3.1 Proposed Technical Formulation for Useful Illumination

### Proposed technical formulation for useful illumination

The recommended research target is:

**Usefulness(lamp, task, region, time)**  
= expected visibility benefit on the region served by the tracked lamp  
minus penalties for non-uniformity, glare, occlusion, misdirection, and confounding sources,  
with an uncertainty estimate.

In practice, the model should expose six interpretable outputs.

A lamp-state head: off, on, dim, flickering, saturated, occluded, or ambiguous. Rolling-shutter and temporal-light-modulation literature suggest that some LED flicker information may be recoverable from video artefacts, but this is device- and frame-rate-dependent. îˆ€citeîˆ‚turn16search5îˆ‚turn21search11îˆ‚turn17search8îˆ

A contribution-footprint head: a soft mask over road, pavement, crossing, curb, or plaza pixels plausibly attributable to the lamp. This should be inferred jointly from geometry, scene parsing, apparent lamp position, pole height priors, and temporal consistency. It is the least explored subproblem in prior work and one of the most novel pieces. îˆ€citeîˆ‚turn26view1îˆ‚turn29view0îˆ‚turn28view3îˆ‚turn28view2îˆ

A weak-photometry head: estimated ground-region and face-height light quantities in a device-normalised domain. If RAW or manual-capture metadata are available, this head can be more physical. If not, it should explicitly degrade to weak calibration. îˆ€citeîˆ‚turn26view3îˆ‚turn15search9îˆ‚turn33search8îˆ

A confounder head: tags for vehicle headlights, brake lights, shopfronts, signage, traffic signals, house windows, reflections, wet road specularity, and sky glow. This head is essential because public-space utility is about lamp contribution, not total scene brightness. îˆ€citeîˆ‚turn21search6îˆ‚turn20search16îˆ‚turn21search12îˆ

A glare head: source prominence, saturation halo, and veiling-luminance proxy near the line of sight. Standards treat glare as a first-class design variable, and enhancement literature shows that strong lights can dominate night images without improving visibility behind them. îˆ€citeîˆ‚turn37view3îˆ‚turn28view4îˆ‚turn32search2îˆ

A final usefulness head: a continuous score and a categorical rating, confidence-calibrated, standards-anchored, and task-conditioned. îˆ€citeîˆ‚turn27view2îˆ‚turn29view7îˆ

### 3.2 Candidate Model Architectures

### Candidate model architectures

The most plausible on-device architecture is a multi-head, two-stage pipeline. Stage one is efficient perception. Use a light detector and tracker to keep the target lamp identity stable over time, and a compact parser to segment road, footway, curb, marking, vegetation, building facade, and dynamic objects. Mobile backbones such as MobileNetV3 and Fast-SCNN are the right design family, not large night-time transformers. îˆ€citeîˆ‚turn11search4îˆ‚turn11search2îˆ‚turn23search1îˆ‚turn23search0îˆ

Stage two is exposure-aware reasoning. Feed the lamp track, scene masks, metadata, and a small temporal window into a lightweight temporal model. A Gated Recurrent Unit or shallow temporal transformer is plausible, but the key is not the sequence model itself; it is the explicit side information: exposure time, sensitivity, frame interval, rolling-shutter status if known, and whether the lamp core is clipped. îˆ€citeîˆ‚turn15search9îˆ‚turn15search1îˆ‚turn21search11îˆ

Weak geometry can be estimated in one of three ways. The lightest option is planar homography plus horizon or vanishing-point cues. The middle option is monocular mobile depth. The strongest option is visual-inertial pose plus coarse map priors, if GNSS and IMU are available. For mobile deployment, a coarse ground-plane model is likely more robust than dense metric depth in night video. îˆ€citeîˆ‚turn14search5îˆ‚turn14search21îˆ‚turn23search6îˆ

For deployment, the most realistic software targets are îˆ€urlîˆ‚TensorFlow Liteîˆ‚turn12search19îˆ with post-training quantisation or quantisation-aware training, and îˆ€urlîˆ‚Core MLîˆ‚turn13search1îˆ with the device-local Vision stack for detection or tracking integration. Both toolchains explicitly support model optimisation for edge execution. îˆ€citeîˆ‚turn12search1îˆ‚turn12search4îˆ‚turn12search10îˆ‚turn13search6îˆ

### 3.3 Three Concrete Formulations

### Three concrete formulations

**Formulation 1: standards-driven calibrated photometric estimator.**  
Input: phone video with locked capture if possible, device calibration, camera intrinsics, metadata, and sparse site calibration. Output: per-lamp affected-region mask plus calibrated illuminance or luminance proxies and a standards-threshold pass/fail judgement. Ground truth: lux meters, luminance camera or HDR reference, survey geometry, lamp metadata. Why it may work: it is the cleanest scientifically and aligns best with CIE, EN, IES, and FHWA concepts. Why it may fail: ordinary phone video often lacks the control and linearity needed; reflectance and confounders remain hard. Evaluation: physical MAE and task-threshold accuracy. On-device feasibility: limited unless the capture app controls the camera pipeline tightly. îˆ€citeîˆ‚turn26view3îˆ‚turn29view4îˆ‚turn27view1îˆ‚turn27view2îˆ‚turn27view3îˆ

**Formulation 2: weakly calibrated visual-usefulness score.**  
Input: ordinary phone video, metadata when available, scene parsing, lamp tracking. Output: score or rating for useful illumination, plus uncertainty and confounder flags. Ground truth: sparse lux or luminance measurements, human annotation of adequacy, and task-based labels such as pedestrian visibility or crossing adequacy. Why it may work: it matches what phones can reliably sense and absorbs device variation statistically. Why it may fail: risk of learning dataset-specific brightness shortcuts unless calibration and confounder controls are explicit. Evaluation: ranking correlation, calibration error, macro F1, and task transfer across devices. On-device feasibility: high. îˆ€citeîˆ‚turn29view1îˆ‚turn35search0îˆ‚turn35search12îˆ‚turn27view2îˆ‚turn11search4îˆ‚turn11search2îˆ

**Formulation 3: hybrid on-device model.**  
Input: tracked lamp, parsed scene, weak geometry, capture metadata, short video window. Output: lamp state, coverage mask, weak photometric estimates, glare penalty, and final usefulness score. Ground truth: all of the above, but not at dense scale; sparse photometric calibration and dense semantic labels are enough initially. Why it may work: it combines the strongest ideas from standards, mobile sensing, and night vision while staying deployable. Why it may fail: attribution errors may dominate; one lampâ€™s footprint can overlap with anotherâ€™s, and bright dynamic lights can overwhelm the signal. Evaluation: multi-task benchmark with physical, semantic, ranking, temporal, and latency metrics. On-device feasibility: best overall trade-off. îˆ€citeîˆ‚turn26view1îˆ‚turn29view0îˆ‚turn27view2îˆ‚turn28view3îˆ‚turn28view2îˆ‚turn12search10îˆ‚turn13search1îˆ

### 3.4 Strongest Baselines and Buried Mitigations

### Strongest baselines

The strongest baselines are not all deep. A simple lamp-state classifier is the minimum baseline. A lamp-crop brightness regressor normalised by exposure metadata is the next baseline. A scene-level night-brightness score, without attribution, is a useful negative control because it will often fail precisely where the problem is hard. A standards-naive geometric baseline can project a cone from the lamp to the ground and average normalised brightness on the segmented road or pavement. Finally, external-meter baselines from route-level vehicle systems should be used for upper-bound comparison on the same sites. îˆ€citeîˆ‚turn29view1îˆ‚turn26view1îˆ‚turn26view2îˆ‚turn34search14îˆ

### Main failure modes and mitigation strategies

The first failure mode is camera inconsistency. Different phones, lenses, codecs, and pipelines can turn the same scene into very different pixel values. Mitigation: device-aware training, metadata conditioning, per-device calibration cards or sparse site calibration, and preferably RAW or locked manual capture during dataset collection. îˆ€citeîˆ‚turn26view3îˆ‚turn33search13îˆ‚turn15search9îˆ

The second failure mode is confounding light. Shopfronts, signs, vehicle lamps, and reflections can dominate the apparent brightness of the area that the streetlight nominally serves. Mitigation: semantic confounder labels, temporal suppression of moving lights, and contribution modelling that conditions on lamp geometry and scene surfaces rather than raw local brightness. îˆ€citeîˆ‚turn21search6îˆ‚turn20search16îˆ‚turn21search12îˆ

The third failure mode is saturation and glare. A lamp can bloom in the image and still provide poor visibility where it matters. Mitigation: clip detection, source-mask features, adjacent-region analysis, and explicit glare penalty heads. îˆ€citeîˆ‚turn28view4îˆ‚turn37view3îˆ‚turn32search2îˆ

The fourth failure mode is wrong affected-region inference, especially when the lamp is far away, mounted high, partially hidden by trees, or competing with adjacent poles. Mitigation: ground-plane priors, pole-height estimation, multi-frame consistency, and supervision on coverage masks rather than only final scores. îˆ€citeîˆ‚turn26view1îˆ‚turn29view0îˆ

The fifth failure mode is target mismatch. A roadway-lighting metric can declare success while pedestrians still cannot see faces or obstacles on the footway. Mitigation: separate task classes and separate sub-metrics for carriageway, crossing, and pedestrian space. îˆ€citeîˆ‚turn27view2îˆ‚turn29view7îˆ‚turn35search10îˆ‚turn35search0îˆ

### 3.5 Recommended First Prototype

### Recommended first prototype

The most sensible first prototype is not the fully calibrated estimator. It is a hybrid weakly calibrated model.

Build a phone app that captures short night clips with exposure metadata. Detect and track lamp heads. Segment road, footway, and crossing regions. Estimate a coarse ground plane. Compute a manually designed baseline score using exposure-normalised local brightness on the served region, a saturation penalty, a confounder penalty, and a uniformity proxy. Then train a lightweight learned head on top of those features using sparse lux or luminance reference and categorical adequacy labels. This prototype is scientifically honest, operationally useful, and achievable on-device. îˆ€citeîˆ‚turn26view1îˆ‚turn29view1îˆ‚turn29view4îˆ‚turn11search4îˆ‚turn11search2îˆ‚turn12search10îˆ

### 3.6 Recommended Long-Term Research Direction

### Recommended long-term research direction

The long-term direction should move towards a standards-aware digital twin of per-lamp utility. That means learning lamp contribution fields under mobile video, using GIS or map priors when available, explicitly modelling mesopic adaptation and source spectrum where deployment permits, and incorporating human-task simulators rather than only photometric labels. The end goal should be a confidence-aware maintenance and safety tool that says not only whether a lamp is faulty, but whether it is failing the space and users it is meant to serve. îˆ€citeîˆ‚turn27view4îˆ‚turn27view3îˆ‚turn27view2îˆ‚turn35search0îˆ‚turn35search11îˆ

---

## 4. Extracts from `litreview_gpt5.5.md`

### 4.1 Proposed Technical Formulation for Useful Illumination

### Proposed technical formulation for useful illumination

A practical definition is this. For each tracked lamp, estimate the region of road, footpath, crossing, verge, and adjacent public space that is plausibly illuminated by that lamp. Over that region, predict whether the lamp supplies enough attributable light for the dominant visual task, whether that light is spatially even enough to avoid dark holes, and whether glare, occlusion, or source confusion materially reduce the benefit. Then report one of three outputs. The first is a physical estimate where calibration permits it. The second is a task-aware usefulness score on a bounded scale. The third is an uncertainty flag when attribution or calibration is weak. îˆ€citeîˆ‚turn38view0îˆ‚turn38view5îˆ‚turn38view6îˆ‚turn38view10îˆ

In engineering terms, the estimand should be local and attributed, not global. A bright luminaire with poor downward throw, a heavily backlit footpath, a heavily saturated lamp behind foliage, and a properly shielded lamp with strong ground uniformity are different cases even if the source blob has similar apparent intensity. This is exactly where current maintenance systems fail, because they mostly reason about lamps rather than illuminated space. îˆ€citeîˆ‚turn31search6îˆ‚turn31search2îˆ‚turn33search0îˆ

### 4.2 Candidate Model Architectures

### Candidate model architectures

A plausible architecture under phone constraints has five stages. The first stage is capture and metadata logging through a controlled-app mode, ideally YUV or RAW when available, plus exposure time, ISO or sensitivity, white-balance state, frame timing, and IMU. The second stage is lamp detection and short-term tracking using a mobile detector plus lightweight tracker. The third stage is scene parsing and rough geometry using real-time segmentation and lightweight depth or ground-plane estimation. The fourth stage is feature construction: exposure-aware lamp appearance, halo shape, saturation fraction, local ground brightness gradients, confounder masks, visibility-zone coverage, estimated occlusion, and temporal stability. The fifth stage is a tiny temporal head that produces physical proxies where allowed and a learned usefulness score plus uncertainty. îˆ€citeîˆ‚turn39view8îˆ‚turn35search1îˆ‚turn14search0îˆ‚turn14search1îˆ‚turn14search2îˆ‚turn35search0îˆ‚turn41search3îˆ‚turn39view9îˆ‚turn39view10îˆ

The heavy design choice is whether depth should be explicit or implicit. My recommendation is explicit but coarse depth, because the affected-region problem is fundamentally geometric. Even a rough ground-plane estimate is more scientifically defensible than trying to infer usefulness from lamp halo appearance alone. The literature on mobile depth estimation is now good enough to justify this choice. îˆ€citeîˆ‚turn13search3îˆ‚turn13search11îˆ‚turn41search3îˆ

### 4.3 Three System Formulations

### Formulation one

A standards-driven calibrated photometric estimator should take controlled-capture phone video, lamp tracks, IMU, intrinsics, and per-frame exposure metadata, with per-device response and vignetting calibration and a small field-calibration set. It should output estimated lamp-attributed horizontal illuminance on the accessible ground region, vertical illuminance in pedestrian zones, and where feasible roadway luminance proxies, plus uniformity and glare-related penalties. The required ground truth is lux-grid measurement on the ground plane, vertical or semi-cylindrical illuminance at pedestrian eye height in representative zones, and a luminance reference on a subset using a calibrated luminance camera or HDR reference rig. The supporting literature is the camera-photometry line, the mobile-sensor platform line, and the standards set. It may work because it aligns the model target with accepted lighting engineering quantities. It may fail because phone capture remains spectrally and radiometrically underconstrained, road-surface reflectance is unknown, and lamp attribution is difficult in mixed-light scenes. It should be evaluated with MAE or RMSE on physical quantities, spatial error on the illuminated footprint, uncertainty calibration, and agreement with standard class thresholds. On-device feasibility is moderate only if inference is sparse and the photometric model is simplified; it is the hardest formulation. îˆ€citeîˆ‚turn38view6îˆ‚turn28search3îˆ‚turn38view7îˆ‚turn38view8îˆ‚turn39view1îˆ‚turn39view3îˆ‚turn38view9îˆ‚turn38view10îˆ

### Formulation two

A weakly calibrated visual-usefulness score should take ordinary phone video, lamp tracks, segmentation, and metadata when present, and output a continuous score or ordinal classes such as useless, weak, adequate, and strong, together with attribution confidence. The ground truth should combine measured lux or luminance where available with task labels from human studies or field panels, such as whether the area is good enough for obstacle detection, pedestrian recognition, or safe crossing. The supporting literature is stronger here than it first appears: NightLight and CityLightSense justify that partially calibrated light proxies can still be useful for safety-related routing and mapping, while FHWA and Fotios-style work define the visibility tasks that matter. It may work because it avoids overclaiming physical accuracy and instead learns a stable mapping from phone-observable cues to meaningful visibility outcomes. It may fail through dataset bias, phone-model leakage, and learned shortcuts based on scene context rather than lamp contribution. It should be evaluated by ranking metrics, macro F1, AUROC for underlit detection, temporal stability, uncertainty calibration, and correlations with physical measurements. On-device feasibility is high. This is the best first product formulation. îˆ€citeîˆ‚turn38view2îˆ‚turn21search2îˆ‚turn38view9îˆ‚turn38view10îˆ‚turn40view5îˆ‚turn27search9îˆ

### Formulation three

A hybrid on-device model should combine controlled capture where possible, streetlight tracking, ground-plane segmentation, coarse depth, exposure-aware brightness normalisation, confounder detection, glare and saturation cues, temporal aggregation, and a learned usefulness head. It should output both a small proxy vector and a final usefulness score: lamp-attributed illuminated-area coverage, weakly calibrated ground-light strength, pedestrian visibility plausibility, uniformity proxy, glare penalty, and confidence. The ground truth should therefore be multi-layered: physical measurements on a subset, dense or semi-dense footprint annotations, confounder masks, lamp state labels, and human task labels. The supporting literature is broad and mutually reinforcing even though no single paper gives the full stack. It may work because it respects the causal structure of the problem. It may fail because attribution remains hard in dense urban scenes, and because the learned head may overfit to non-lighting context. It should be evaluated at physical, perceptual, and systems levels simultaneously. On-device feasibility is good if the model is event-driven, quantised, and uses asymmetric scheduling, with light detection every frame and heavier geometry every few frames. This is the most plausible research formulation and the most plausible paper-worthy contribution. îˆ€citeîˆ‚turn38view0îˆ‚turn38view6îˆ‚turn38view9îˆ‚turn38view10îˆ‚turn14search0îˆ‚turn14search1îˆ‚turn14search2îˆ‚turn35search0îˆ‚turn41search3îˆ‚turn39view9îˆ‚turn39view10îˆ

### 4.4 Buried Dataset / Evaluation / Failure-Mode Suggestions

The core data-collection design for Indian urban roads and public spaces should have four layers. The first layer is phone video from multiple devices in two capture modes: an instrumentation mode with controlled exposure and YUV or RAW when available, and a consumer mode with ordinary camera-app video. The second layer is physical reference: lux-meter ground grids, vertical illuminance at about 1.5 metres in pedestrian zones, and luminance reference photography on a smaller subset. The third layer is semantics and geometry: streetlight boxes and tracks, pole location, visible lamp head, road and sidewalk segmentation, crosswalks, vegetation occlusion, shopfronts, traffic lights, vehicle lights, and approximate pole height. The fourth layer is task labels: obstacle visibility, pedestrian visibility, crossing plausibility, and perceived reassurance. îˆ€citeîˆ‚turn38view6îˆ‚turn38view7îˆ‚turn38view8îˆ‚turn38view9îˆ‚turn38view10îˆ

The hardest annotation problem is lamp attribution. My recommendation is to avoid pretending to have perfect attribution. Instead, collect three grades of attribution label. â€œCertain attributionâ€ is for isolated lamps with clear geometry and little confounding light. â€œMixed attributionâ€ is for scenes with plausible multiple contributors. â€œUncertain attributionâ€ is for heavily mixed or saturated scenes. Training and evaluation should preserve those confidence labels instead of collapsing them into noisy hard targets. That recommendation is an inference from the source-attribution difficulty shown across the monitoring, calibration, and night-perception literature. îˆ€citeîˆ‚turn38view0îˆ‚turn38view6îˆ‚turn31search6îˆ‚turn40view6îˆ

I recommend five evaluation layers. The first is physical accuracy on the calibrated subset: error in horizontal illuminance, vertical illuminance, and any luminance estimate. The second is spatial attribution: IoU or boundary error for the estimated illuminated footprint on the accessible ground and adjacent public space. The third is task utility: agreement with obstacle visibility, child-sized or adult pedestrian visibility, and crossing-task labels. The fourth is reliability: temporal stability across a lamp track, confidence calibration, and graceful abstention in mixed-light scenes. The fifth is system performance: latency, energy, thermal load, memory footprint, and robustness across phone models. The physical and task layers are supported by the photometry and FHWA-style visibility literature; the reliability and systems layers are necessary additions for an on-device product. îˆ€citeîˆ‚turn38view6îˆ‚turn38view9îˆ‚turn38view10îˆ

### 4.5 Recommended First Prototype

### Recommended first prototype

The recommended first prototype is Formulation three, but with the ambition level of Formulation two. Build a hybrid weakly calibrated usefulness estimator first. Use a custom capture app with exposure metadata and YUV wherever possible. Detect and track streetlights. Segment road, footpath, crosswalk, vegetation, vehicles, traffic lights, signage, and buildings. Estimate a coarse ground plane and rough lamp-to-ground footprint. Compute exposure-aware and geometry-aware features. Predict a four-class usefulness label and confidence, not lux. Train against a small but carefully calibrated field dataset. îˆ€citeîˆ‚turn39view8îˆ‚turn14search0îˆ‚turn14search1îˆ‚turn14search2îˆ‚turn35search0îˆ‚turn41search3îˆ‚turn39view9îˆ‚turn39view10îˆ

The strongest baselines should be deliberately simple and sceptical. They should include lamp state only, saturated lamp-blob brightness, scene-average luminance proxy, ambient light sensor proxy, and a no-geometry learned score. Any proposed model should beat those baselines not only overall but specifically on confounded scenes, occluded lamps, and mixed-source scenes. That is where the causal structure of the problem should pay off. îˆ€citeîˆ‚turn21search2îˆ‚turn38view2îˆ‚turn33search0îˆ‚turn31search6îˆ

### 4.6 Recommended Long-Term Direction

### Recommended long-term direction

The long-term research direction is a standards-aware hybrid model trained on a new dataset with partial physical calibration and total uncertainty awareness. Synthetic augmentation should use lighting simulation, ideally via tools such as SALUSLux, to generate plausible footprints, occlusion scenarios, and standard-derived light patterns. Multi-frame reasoning should mature from simple tracking to exposure-consistent aggregation and local SLAM. Device adaptation should move from phone-specific calibration tables to learned phone embeddings with occasional field calibration. In the best case, the system could eventually output both a public-space usefulness score and approximate standard metrics, with clear confidence flags. îˆ€citeîˆ‚turn31search3îˆ‚turn31search7îˆ‚turn38view6îˆ‚turn39view1îˆ‚turn39view3îˆ
