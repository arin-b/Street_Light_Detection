# Estimating Useful Streetlight Illumination from Night-Time Phone Video

## Executive synthesis

The literature does support a meaningful research programme here, but not the naive version of it. A tracked lamp in night video is not itself the target. The defensible target is the lamp’s contribution to visibility in accessible public space near the lamp, conditioned on task, geometry, and confounders. Existing standards already separate driver-oriented quantities such as road-surface luminance, uniformity, threshold increment, and edge illuminance ratio from pedestrian-oriented quantities such as horizontal illuminance, vertical illuminance, and semi-cylindrical illuminance. Human-factor studies further show that obstacle detection, pedestrian recognition, and reassurance are related but not identical tasks, and that some standard recommendations rest on weaker empirical foundations than is often assumed. citeturn39view3turn39view1turn38view9turn38view10turn9search15turn27search9

The strongest conclusion is therefore negative before it is positive. Ordinary phone video, especially post-ISP SDR video with automatic exposure, white balance, tone mapping, HDR, compression, and model-specific processing, cannot be trusted as a direct lux meter. The photometric literature is explicit that camera digital values only become physically interpretable after response, exposure, vignetting, and often spectral calibration; smartphone studies show that even still-image luminance use is fragile and can undercapture real luminance severely if the device, field of view, and optics are not calibrated. What phone video can support well is a weakly calibrated or hybrid estimate: a lamp-attributed usefulness score, or a small set of physically inspired proxies, with uncertainty. citeturn38view6turn28search3turn38view7turn38view8turn29search0turn39view8

The most plausible first system is therefore not a full absolute photometric estimator. It is a hybrid on-device model that detects and tracks the lamp, segments the drivable and walkable ground plane, estimates the lamp’s likely footprint, suppresses confounding light sources, normalises brightness using exposure metadata as far as available, and predicts a usefulness score plus calibrated uncertainty. Absolute horizontal illuminance, vertical illuminance, or luminance can be a secondary output only when minimum calibration conditions are met. citeturn38view0turn38view5turn38view6turn38view9turn38view10

A precise formulation is this: given a tracked streetlight in a night-time phone video, estimate how much that specific lamp improves the visibility of the nearby road, footpath, crossing area, and adjacent public space for relevant users, after accounting for occlusion, directionality, glare, source confusion, and camera processing. The estimate should be localised in space, attributed to the lamp rather than to the whole scene, temporally stable across frames, and accompanied by uncertainty. That is genuinely different from lamp fault detection, global night-scene brightness estimation, low-light enhancement, or general night-time object detection. citeturn38view0turn21search2turn38view2turn33search0turn31search6

The direct answers to the core research questions are these. The most defensible definition of useful illumination is a hybrid metric anchored in standard lighting quantities but optimised for visibility tasks, not raw brightness. Ordinary phone video can support useful estimation without external calibration only as ranking, categorisation, or weakly calibrated scoring, not as trustworthy absolute lux. Minimum trustworthy calibration is per-frame exposure metadata, camera response or relative photometric calibration, vignetting handling, intrinsics, approximate camera pose over the ground plane, and at least some device-specific field calibration. Image-based proxies remain useful if they are explicitly validated against physical and task-based ground truth. Lamp contribution can be separated from confounders only through joint use of geometry, semantics, time, and attribution confidence, not by brightness alone. citeturn38view6turn38view7turn38view8turn39view1turn38view9turn38view10

## Evidence from urban-lighting monitoring, photometry and standards

### Taxonomy of prior work

The prior literature falls into six clusters. One cluster detects or monitors streetlights and urban lighting infrastructure using moving vehicles, fixed pole cameras, or smartphones. A second cluster estimates physical light from cameras through radiometric calibration, HDR, luminance-camera methods, or smartphone photometry. A third cluster defines what road and pedestrian lighting should achieve through standards and guidance. A fourth cluster studies human visual performance, reassurance, and safety under night lighting. A fifth cluster solves night-time perception tasks such as segmentation, detection, and depth under adverse visual conditions. A sixth cluster focuses on efficient mobile deployment, including light backbones, pruning, quantisation, and temporal aggregation. The proposed problem touches all six, but no single literature stream solves the lamp-attributed usefulness problem directly. citeturn38view0turn21search2turn38view2turn38view6turn39view3turn39view4turn38view10turn40view6turn35search1turn39view9turn39view10

### Streetlight and urban-lighting monitoring

The closest systems literature proves that moving-platform lighting assessment is feasible, but usually at coarser scope than this problem. “Urban Street Lighting Infrastructure Monitoring Using a Mobile Sensor Platform” developed a car-mounted night-time drive-by system for mapping illumination levels, identifying lamps, estimating lamp heights, and geotagging them. That is highly relevant because it demonstrates that lamp localisation, height estimation, and moving-platform illumination analysis are not speculative, but it uses a richer sensor platform than an ordinary phone. citeturn38view0

“LiSense” and “CityLightSense” move the problem toward smartphones, but mainly through participatory sensing of ambient light rather than lamp-attributed video inference. “NightLight” pushes this further for pedestrian routing by combining smartphone ambient light sensor readings with phone orientation and GPS while people walk. These systems are useful as evidence that crowdsensed urban-lighting maps are practical and safety-relevant, but they estimate local light exposure, not the contribution of a specific tracked streetlight in video. citeturn21search14turn21search2turn30search1turn38view2

The fixed-camera streetlight-monitoring literature is also helpful but limited. The UMBRELLA streetlight dataset contains roughly 350,000 upward-looking images from 140 lamppost-mounted nodes in South Gloucestershire, collected over six months. That is valuable for lamp state, aging, drift, and anomaly detection, but it does not observe the ground effect of the luminaire from a pedestrian or driver viewpoint. The same limitation applies to many fault-detection systems that infer whether the luminaire appears bright, dark, or anomalous while ignoring whether its light is actually usable on the ground. citeturn12search17turn31search5

Recent dashcam-based work is closer again. The 2025 YOLO-CSE street-lighting paper uses high-resolution dashcam footage under diverse night weather and builds a dataset of 4,260 annotated frames for streetlight pole and lamp detection. This is useful for mobile-video detection and tracking baselines, but it remains fundamentally a detection and condition-analysis pipeline, not a visibility-quality estimator. citeturn33search0

Finally, night-time mobile mapping work shows why lamp visible brightness is insufficient. Aalto’s mobile mapping and 3D luminance studies used a vehicle-mounted panoramic camera, laser scanner, IMU, and GNSS to assess the light-obstructing effect of roadside vegetation and to build georeferenced luminance point clouds. That is exactly the right cautionary lesson: a lamp may be working, yet its practical illumination can be degraded by vegetation or geometry. The limitation is obvious too: this level of sensing is much richer than commodity phone video. citeturn31search6turn31search17turn31search2

### Camera-based photometry and luminance or illuminance estimation

The photometric camera literature is clear about the image formation problem. Camera output is not illuminance. It is the result of scene radiance passing through optics, spatial fall-off, integration over exposure time, sensor gain, and a camera response function. Bergmann and colleagues show that auto-exposure video can be approximately photometrically calibrated by recovering relative exposure times, response function, and vignetting, but that is already a substantial calibration problem, even before tone mapping and phone ISP effects. citeturn38view6turn40view1

Older but still foundational work by Wüller and Gabele showed that digital still cameras can be used as luminance meters only after explicit calibration of the opto-electronic conversion function. That result matters because it is often misread in modern vision work. The claim is not that any consumer image measures light. The claim is that a calibrated camera can estimate luminance under known conditions. citeturn28search3

The newer smartphone-specific literature is even more cautionary. The 2024 smartphone pilot study asks directly whether modern high-resolution smartphone cameras are suitable for luminance measurements and concludes that specific technical requirements must be fulfilled. The 2022 smartphone luminance paper reports that one calibrated HDRI pipeline had about 7 percent error against a lux meter, but also that among six smartphones the best device captured only 17 percent of measured luminance, with strong vignetting limitations outside about 100 degrees. These are not small nuisances; they are strong evidence that uncalibrated phone imagery is an unstable basis for physical photometry. citeturn38view7turn38view8

The capture stack matters just as much as the calibration model. The consumer mobile-photography literature shows that modern phones operate through burst fusion, adaptive exposure choice, denoising, learned white balance, and tone mapping in very low light. Google’s Night Sight paper reaches about 0.3 lux by aligning and merging multiple frames, explicitly using perceptual tone mapping to avoid making the scene look like daylight. That is excellent for photography and often harmful for measurement, because the image becomes an aesthetically designed rendering rather than a radiometrically faithful sampling. citeturn29search0turn29search9

There is still a viable path on phones, but it requires tighter capture control. The official urlAndroid Camera2 APIturn26search4 exposes RAW_SENSOR and YUV_420_888 on devices that support them, and YUV output is documented as using a known YUV to RGB transform into sRGB by default. That means an instrumentation-grade app can, on at least some devices, avoid the worst of the consumer photo pipeline, log exposure metadata, and operate on YUV or RAW instead of compressed SDR presentation video. The same logic motivates an instrumentation mode on iOS via urlCore MLturn15search20 deployment, although the key issue is capture control rather than the inference framework itself. citeturn39view8turn15search20

The bottom line is strict. If the goal is absolute illuminance or luminance, then a defensible pipeline needs controlled capture, per-frame metadata, response or relative photometric calibration, device calibration, and geometry. If the goal is a usefulness score or risk ranking, weaker calibration is acceptable, but the output must be defined as such. citeturn38view6turn38view7turn38view8

### Standards and human visibility

The most relevant standards literature comes from entity["organization","CIE","lighting standards body"], European road-lighting standards, the entity["organization","Federal Highway Administration","US transport agency"], the IES road-lighting practice, and the entity["organization","Bureau of Indian Standards","India standards body"]. CIE 115:2010 is the main structured framework for selecting road-lighting classes for motor traffic, conflict areas, and pedestrian areas, and explicitly supports adaptive lighting. CIE 191:2010 provides the recommended mesopic photometry system based on visual performance, which matters because many street-lighting scenes are neither fully photopic nor fully scotopic. citeturn39view3turn39view4

EN 13201-2 is especially useful because it states the actual metric bundle: for motorised traffic, average road-surface luminance, overall uniformity, longitudinal uniformity, threshold increment, and edge illuminance ratio; and it also defines semi-cylindrical and vertical illuminance terms used in pedestrian contexts. These are immediately more informative than a single “brightness” score. citeturn39view1turn40view7

The FHWA pedestrian-lighting guidance is valuable because it translates standards into task language. It distinguishes horizontal illuminance, vertical illuminance, and semi-cylindrical illuminance, notes that vertical-to-horizontal ratio indicates potential glare, and uses 1.5 metres as a representative eye height for standing pedestrians. The companion research report explicitly designs experiments around child-sized pedestrian visibility to drivers, trip-hazard visibility to pedestrians, and crossing decisions. That is precisely the kind of task decomposition this project needs. citeturn38view9turn40view2turn38view10turn40view3

The Indian standard IS 1944 is older and more fragmented, but it is still important for Indian fieldwork. Its own foreword states that it covers the quantity and quality of lighting for public thoroughfares and that the revision drew from older CIE and British standards. For an India-specific dataset and evaluation protocol, this is the correct local compliance anchor, even if the most recent open public texts are dated and should be supplemented in practice with current municipal specifications where available. citeturn39view2turn40view8

The human-factors literature adds two important warnings. First, pedestrian and driver needs are not identical. entity["people","Steve Fotios","lighting researcher"] and colleagues show that trip-hazard detection, obstacle detection, facial recognition, interpersonal judgement, and reassurance do not collapse neatly into one metric. Second, even standard light-level recommendations are not uniformly based on strong empirical evidence; the 2018 review explicitly says many recommendations do not appear well founded in robust evidence. That makes a hybrid metric more defensible than claiming one standard quantity is the whole truth. citeturn40view4turn40view5turn38view13turn9search15turn27search9turn27search5

The semicylindrical story is particularly instructive. It is attractive because it better reflects three-dimensional pedestrian visibility and facial/body recognition, but empirical evidence that it consistently outperforms vertical illuminance is mixed. Fotios’s critique notes that prior conclusions favouring semi-cylindrical illuminance over vertical illuminance were not strongly statistically supported. So semi-cylindrical illuminance should influence the target design, but it should not be treated as settled doctrine. citeturn38view9turn38view13turn36search13

### Key papers and systems

| Work | Problem | Input and output | Calibration assumptions | Physical light, perceived visibility, or visual brightness | Night, phone video, on-device | Strengths and limits | Source |
|---|---|---|---|---|---|---|---|
| Kumar et al., Urban Street Lighting Infrastructure Monitoring Using a Mobile Sensor Platform | Mobile drive-by mapping of streetlights | Car-mounted sensors to illumination map, lamp ID, lamp height, geotag | Rich platform calibration | Closer to physical lighting than simple brightness | Night yes; phone video no; on-device no | Strong precedent for moving-platform lamp mapping; too sensor-rich for ordinary phone | citeturn38view0 |
| LiSense | Smartphone-based city street-light monitoring | Smartphone sensors to city-lighting assessment | Sensor and localisation assumptions | Ambient light mapping, not lamp attribution | Night yes; phone yes; on-device plausible | Useful crowdsensing idea; weak for lamp-specific usefulness | citeturn21search14 |
| Middya et al., CityLightSense | Participatory city illumination mapping | Smartphone illumination samples to city map | Sensor reliability and interpolation assumptions | Ambient illuminance mapping | Night yes; phone yes; on-device partly | Scalable map generation; not video, geometry, or lamp specific | citeturn21search2turn30search1 |
| Breda et al., NightLight | Sidewalk-light data for pedestrian routing | Ambient sensor, IMU, GPS to pedestrian lighting map | Phone orientation model and sensor availability | Exposure proxy for routing, not lamp contribution | Night yes; phone yes; on-device yes | Strong relevance to pedestrian utility; no lamp attribution | citeturn38view2 |
| Aiymbay et al., Applying Computer Vision for the Detection and Analysis of the Condition and Operation of Street Lighting | Dashcam streetlight detection and condition analysis | Dashcam frames to pole/lamp detections | Visual condition labels, not photometric calibration | Lamp condition and detection, not useful ground light | Night yes; phone video maybe adaptable; on-device partly | Good detection baseline and dataset; not a ground-usefulness model | citeturn33search0 |
| Mavromatis et al., UMBRELLA streetlight dataset | Fixed upward monitoring of streetlights | Pole camera images to condition monitoring | Fixed viewpoint per node | Apparent lamp state | Night yes; phone video no; on-device some | Large real dataset; wrong viewpoint for public-space usefulness | citeturn12search17turn31search5 |
| Maksimainen et al., Nighttime Mobile Laser Scanning and 3D Luminance Measurement | Vegetation obstruction and luminance mapping | Car-mounted camera plus LiDAR plus IMU plus GNSS to 3D luminance | Luminance calibration and georegistration | Physical luminance and obstruction analysis | Night yes; phone video no; on-device no | Crucial evidence that occlusion matters; too heavy for a phone-only system | citeturn31search6turn38view5 |
| Wüller and Gabele, The usage of digital cameras as luminance meters | Camera as luminance meter | Calibrated still camera to luminance | Explicit OECF calibration | Physical luminance after calibration | Night possible; phone video no; on-device not the point | Foundational calibration logic; does not justify uncalibrated video | citeturn28search3 |
| Bergmann et al., Online Photometric Calibration of Auto Exposure Video | Photometric calibration for moving video | Auto-exposure video to response, exposure, vignetting | Feature tracks and photometric model | Relative physical image formation, not scene illuminance directly | Night possible; phone video possible; on-device maybe reduced | Essential bridge from video to calibrated features; still not enough alone for lux | citeturn38view6turn40view1 |
| Zalewski et al., smartphone photometric pilot | Suitability of high-end smartphones for luminance | Smartphone cameras to luminance evaluation | Strict technical requirements | Physical luminance, cautiously | Night not central; phone yes; on-device n.a. | Strong caution against casual measurement | citeturn38view7 |
| Thounaojam et al., Luminance Measurements using Smartphone Cameras | HDRI luminance from phones | Smartphone HDRI to luminance estimate | Calibration to lux meter and optics limits | Physical luminance with caveats | Night not central; phone yes; on-device limited | Quantifies severe undercapture and vignetting limits | citeturn38view8 |

### Standards and lighting metrics

| Standard or guidance | Main scope | Most relevant metrics | Directly usable for this system | Not directly usable | Source |
|---|---|---|---|---|---|
| CIE 115:2010 | Roads for motor and pedestrian traffic; adaptive class selection | M, C, and P class logic; luminance or illuminance concept | As target definitions and class logic | Not as direct supervision from casual phone video | citeturn39view3 |
| CIE 191:2010 | Mesopic photometry based on visual performance | Mesopic spectral sensitivity and night-driving relevance | As justification that spectrum and adaptation matter at low light | Hard to estimate from RGB phone video without spectral calibration | citeturn39view4 |
| EN 13201-2:2015 | Performance requirements for road lighting | Average luminance, overall uniformity, longitudinal uniformity, threshold increment, edge illuminance ratio; definitions of vertical and semi-cylindrical illuminance | Very useful to define outputs and evaluation | Assumes standard grids, road reflectance conventions, and measurement procedures | citeturn39view1turn40view7 |
| FHWA Pedestrian Lighting Primer and Street Lighting for Pedestrian Safety | Pedestrian-oriented lighting design and experiments | Horizontal, vertical, and semi-cylindrical illuminance; glare ratio; visibility of pedestrians and trip hazards | Highly usable for task definitions and field protocols | US-specific guidance, not a phone-video algorithm | citeturn38view9turn38view10 |
| ANSI/IES RP-8 family | Roadway and parking lighting practice | Calculations, design, maintenance, planning | Useful as background and terminology | Mostly not open enough for detailed extraction here | citeturn23search0turn23search3 |
| IS 1944 | Indian code of practice for public thoroughfares | Quantity and quality of lighting for Indian public roads | Important local compliance and road-class context for Indian data collection | Open public versions are dated and should be supplemented by current local specifications | citeturn39view2turn40view8 |

## Evidence from night-time computer vision and embedded AI

### Night-time perception datasets and what they do not contain

The night-time perception literature provides strong building blocks, but not the final target. entity["organization","ETH Zurich","Switzerland university"]’s ACDC dataset contributes 4,006 adverse-condition images with high-quality annotation, equally distributed over fog, night, rain, and snow, and is explicitly designed for uncertainty-aware semantic segmentation. Dark Zurich contributes day, twilight, and night correspondences and a benchmark for night segmentation. NightCity provides 4,297 annotated real night-time images and was created specifically because existing scene-parsing datasets were too daytime-biased. Nighttime Driving provides 35,000 unlabeled and 50 densely labeled night and dusk images, and BDD100K contributes 100,000 diverse driving videos and ten tasks, albeit not focused on lamp usefulness. citeturn40view6turn11search9turn10search2turn34search13turn10search11

For scene context and pretraining, the official urlMapillary Vistas datasetturn32search1 is especially useful because it is street-level, globally diverse, and includes a street-light class in the extended taxonomy. Large autonomous-driving corpora such as urlnuScenesturn41search4 and urlWaymo Open Datasetturn41search9 are also valuable for pretraining geometry, detection, and adverse-condition robustness, even though they are not lamp-centric and do not provide lamp-attributed ground-illumination targets. citeturn32search1turn32search7turn32search3turn41search0turn41search1

For low-light enhancement and raw imaging, the dataset story is similar. SID contains 5,094 raw short-exposure images paired with long-exposure references; ExDark contains 7,363 low-light images across ten low-light conditions with object labels; and the 2025 Low-light Smartphone Dataset contains 6,425 smartphone low-light and reference pairs spanning about 0.1 to 200 lux. These are highly relevant for denoising, enhancement, and robustness, but they still do not provide lamp attribution, ground-plane footprint labels, or pedestrian-task lighting labels. citeturn22search1turn22search7turn22search15turn22search2turn29search12

### Low-light enhancement and intrinsic decomposition

Retinex-style methods and learned low-light enhancement are helpful and dangerous at the same time. RetinexNet explicitly decomposes reflectance and illumination to enhance images; Zero-DCE predicts intensity-mapping curves without reference images; recent surveys show that the field is focused on visual quality, contrast, denoising, and downstream task support. That is useful if enhancement is treated as a front-end for detection or segmentation. It is misleading if enhanced brightness is treated as physical evidence of illumination. citeturn16search2turn16search0turn16search1

This distinction must be explicit in the proposed project. Enhancement networks may improve streetlight detection, road or sidewalk segmentation, or confounder masking. They should not be the source of photometric targets. In fact, the newest diffusion-style enhancement papers already warn about hallucination risk in notably dark inputs. So the correct use of enhancement in this project is perceptual pre-processing or auxiliary training, never direct measurement. citeturn16search1turn41search14

### Ground region estimation, source separation, and multi-frame reasoning

The computer-vision literature gives a plausible recipe for the hard geometry subproblems. Night semantic segmentation can recover road, sidewalk, curb, pole, vegetation, vehicle, sign, and building masks using ACDC, Dark Zurich, NightCity, Nighttime Driving, BDD100K, and Mapillary-style taxonomies. Monocular depth can supply rough ground-plane geometry, and mobile or embedded depth work shows that real-time depth on constrained hardware is feasible in principle. Structure-from-motion, visual odometry, and SLAM can stabilise illumination estimates across frames, and Bergmann’s photometric calibration work shows that exposure-normalised temporal reasoning is possible in moving auto-exposure video. citeturn40view6turn11search9turn10search2turn34search13turn10search11turn32search1turn13search3turn13search11turn41search3turn38view6

This is also where source separation becomes realistic. A specific streetlight’s contribution should be estimated only on ground and public-space pixels that are both geometrically reachable from the lamp and not obviously dominated by other sources. Vehicle headlamps move relative to the tracked lamp and produce transient streaks and glare; shopfronts, signs, and traffic signals are semantically separable; reflections can be down-weighted by surface class and saturation behaviour; vegetation and pole geometry suggest an occlusion prior; and multi-frame tracking helps keep attribution stable under a moving camera. No single paper solves that full attribution problem, but the components exist. citeturn38view0turn31search6turn33search0turn40view6

Lamp flicker is a special case. The rolling-shutter and temporal-light-modulation literature shows that LED flicker can produce visible banding or other artefacts in camera sensors, and that rolling-shutter cameras can sense temporally modulated light under the right conditions. For a phone-video system, this means flicker is potentially detectable, but only opportunistically, because aliasing depends on unknown sensor readout and lamp PWM frequency. It should therefore be a confidence cue, not a required capability. citeturn18search13turn19search1turn18search10

### Efficient and on-device models

The efficient-model literature is mature enough for an on-device prototype. MobileNetV3 was explicitly tuned for mobile CPUs and includes LR-ASPP for fast segmentation. Fast-SCNN and BiSeNet are both strong real-time segmentation baselines for scene parsing with embedded constraints. EfficientDet is a robust one-stage detection family with a strong efficiency–accuracy trade-off. ByteTrack remains one of the simplest and strongest tracking-by-detection baselines, and FastDepth demonstrates that real-time monocular depth on embedded systems is practically attainable with aggressive architecture design and pruning. citeturn35search1turn14search0turn14search1turn14search2turn35search0turn41search3

For deployment, the most credible targets are urlTensorFlow Liteturn14search3 and urlCore MLturn15search20. The official optimisation documentation for Core ML describes post-training weight quantisation, activation quantisation with a calibration dataset, and quantisation-aware training; the TensorFlow optimisation toolkit documents pruning plus post-training quantisation and shows that sparse, smaller models can be produced for resource-constrained environments. These tools are sufficient for a staged deployment strategy in which only the essential heads run per frame and heavier modules trigger less frequently. citeturn39view9turn39view10

## Target variables and system formulations

### Critical comparison of possible target variables

| Candidate target | Scientific defensibility | What it captures | Why it is insufficient alone | Verdict |
|---|---|---|---|---|
| Lamp on or off | High, but trivial | Gross failure state | Says nothing about useful public-space visibility | Necessary but far from sufficient citeturn12search17turn33search0 |
| Raw or normalised image brightness | Low as a physical quantity | Sensor output after ISP and exposure | Not illuminance; unstable across devices and settings | Reject as final target citeturn38view6turn38view7turn38view8 |
| Horizontal illuminance on accessible ground | High for pedestrian walking and trip hazards | Ground light level | Ignores eye-level visibility, glare, and lamp attribution ambiguity | Strong component, not whole metric citeturn38view9turn38view10turn40view5 |
| Road-surface luminance | High for driver-oriented roadway visibility | What drivers see off the road surface | Depends on road reflectance and viewpoint; hard from phone video | Useful secondary component for roads only citeturn39view1turn38view10turn38view7 |
| Vertical illuminance at about 1.5 m | High for seeing people and obstacles at eye level | Pedestrian and driver-relevant face/body lighting | Still misses three-dimensional light field and glare | Strong pedestrian component citeturn38view9turn38view10 |
| Semi-cylindrical illuminance | Medium to high | Broader facial/body visibility in pedestrian contexts | Empirical superiority over vertical illuminance is not settled | Useful but should not dominate alone citeturn38view9turn38view13turn36search13 |
| Uniformity and illuminated-area coverage | High | Whether light is spread usefully on the ground | Needs geometry and attribution | Essential modifier citeturn39view1turn39view2 |
| Glare penalty or threshold increment proxy | High | Visibility losses caused by glare | Hard to estimate precisely from casual phone video | Essential modifier, likely approximate on phone citeturn39view1turn23search5 |
| Learned usefulness score | High if trained correctly | Fuses physical proxies with task outcomes | Risks becoming opaque and dataset-specific | Best final output if anchored to physical and task labels citeturn38view10turn40view5turn27search9 |

The most defensible target is therefore a hybrid. I recommend defining useful illumination as the lamp-attributed visibility utility of the affected public-space region, represented by a small vector rather than a single scalar during development. The vector should include lamp-attributed ground illuminance coverage, a pedestrian visibility term based on vertical or semi-cylindrical illuminance in key zones, a roadway luminance term where relevant, a uniformity term, a glare or saturation penalty, an occlusion penalty, and an attribution confidence. For deployment, that vector can be collapsed into a calibrated usefulness score or category with uncertainty. This is the only formulation that respects both standards and the actual observability limits of phone video. citeturn39view1turn38view9turn38view10turn9search15

### Proposed technical formulation for useful illumination

A practical definition is this. For each tracked lamp, estimate the region of road, footpath, crossing, verge, and adjacent public space that is plausibly illuminated by that lamp. Over that region, predict whether the lamp supplies enough attributable light for the dominant visual task, whether that light is spatially even enough to avoid dark holes, and whether glare, occlusion, or source confusion materially reduce the benefit. Then report one of three outputs. The first is a physical estimate where calibration permits it. The second is a task-aware usefulness score on a bounded scale. The third is an uncertainty flag when attribution or calibration is weak. citeturn38view0turn38view5turn38view6turn38view10

In engineering terms, the estimand should be local and attributed, not global. A bright luminaire with poor downward throw, a heavily backlit footpath, a heavily saturated lamp behind foliage, and a properly shielded lamp with strong ground uniformity are different cases even if the source blob has similar apparent intensity. This is exactly where current maintenance systems fail, because they mostly reason about lamps rather than illuminated space. citeturn31search6turn31search2turn33search0

### Candidate model architectures

A plausible architecture under phone constraints has five stages. The first stage is capture and metadata logging through a controlled-app mode, ideally YUV or RAW when available, plus exposure time, ISO or sensitivity, white-balance state, frame timing, and IMU. The second stage is lamp detection and short-term tracking using a mobile detector plus lightweight tracker. The third stage is scene parsing and rough geometry using real-time segmentation and lightweight depth or ground-plane estimation. The fourth stage is feature construction: exposure-aware lamp appearance, halo shape, saturation fraction, local ground brightness gradients, confounder masks, visibility-zone coverage, estimated occlusion, and temporal stability. The fifth stage is a tiny temporal head that produces physical proxies where allowed and a learned usefulness score plus uncertainty. citeturn39view8turn35search1turn14search0turn14search1turn14search2turn35search0turn41search3turn39view9turn39view10

The heavy design choice is whether depth should be explicit or implicit. My recommendation is explicit but coarse depth, because the affected-region problem is fundamentally geometric. Even a rough ground-plane estimate is more scientifically defensible than trying to infer usefulness from lamp halo appearance alone. The literature on mobile depth estimation is now good enough to justify this choice. citeturn13search3turn13search11turn41search3

### Formulation one

A standards-driven calibrated photometric estimator should take controlled-capture phone video, lamp tracks, IMU, intrinsics, and per-frame exposure metadata, with per-device response and vignetting calibration and a small field-calibration set. It should output estimated lamp-attributed horizontal illuminance on the accessible ground region, vertical illuminance in pedestrian zones, and where feasible roadway luminance proxies, plus uniformity and glare-related penalties. The required ground truth is lux-grid measurement on the ground plane, vertical or semi-cylindrical illuminance at pedestrian eye height in representative zones, and a luminance reference on a subset using a calibrated luminance camera or HDR reference rig. The supporting literature is the camera-photometry line, the mobile-sensor platform line, and the standards set. It may work because it aligns the model target with accepted lighting engineering quantities. It may fail because phone capture remains spectrally and radiometrically underconstrained, road-surface reflectance is unknown, and lamp attribution is difficult in mixed-light scenes. It should be evaluated with MAE or RMSE on physical quantities, spatial error on the illuminated footprint, uncertainty calibration, and agreement with standard class thresholds. On-device feasibility is moderate only if inference is sparse and the photometric model is simplified; it is the hardest formulation. citeturn38view6turn28search3turn38view7turn38view8turn39view1turn39view3turn38view9turn38view10

### Formulation two

A weakly calibrated visual-usefulness score should take ordinary phone video, lamp tracks, segmentation, and metadata when present, and output a continuous score or ordinal classes such as useless, weak, adequate, and strong, together with attribution confidence. The ground truth should combine measured lux or luminance where available with task labels from human studies or field panels, such as whether the area is good enough for obstacle detection, pedestrian recognition, or safe crossing. The supporting literature is stronger here than it first appears: NightLight and CityLightSense justify that partially calibrated light proxies can still be useful for safety-related routing and mapping, while FHWA and Fotios-style work define the visibility tasks that matter. It may work because it avoids overclaiming physical accuracy and instead learns a stable mapping from phone-observable cues to meaningful visibility outcomes. It may fail through dataset bias, phone-model leakage, and learned shortcuts based on scene context rather than lamp contribution. It should be evaluated by ranking metrics, macro F1, AUROC for underlit detection, temporal stability, uncertainty calibration, and correlations with physical measurements. On-device feasibility is high. This is the best first product formulation. citeturn38view2turn21search2turn38view9turn38view10turn40view5turn27search9

### Formulation three

A hybrid on-device model should combine controlled capture where possible, streetlight tracking, ground-plane segmentation, coarse depth, exposure-aware brightness normalisation, confounder detection, glare and saturation cues, temporal aggregation, and a learned usefulness head. It should output both a small proxy vector and a final usefulness score: lamp-attributed illuminated-area coverage, weakly calibrated ground-light strength, pedestrian visibility plausibility, uniformity proxy, glare penalty, and confidence. The ground truth should therefore be multi-layered: physical measurements on a subset, dense or semi-dense footprint annotations, confounder masks, lamp state labels, and human task labels. The supporting literature is broad and mutually reinforcing even though no single paper gives the full stack. It may work because it respects the causal structure of the problem. It may fail because attribution remains hard in dense urban scenes, and because the learned head may overfit to non-lighting context. It should be evaluated at physical, perceptual, and systems levels simultaneously. On-device feasibility is good if the model is event-driven, quantised, and uses asymmetric scheduling, with light detection every frame and heavier geometry every few frames. This is the most plausible research formulation and the most plausible paper-worthy contribution. citeturn38view0turn38view6turn38view9turn38view10turn14search0turn14search1turn14search2turn35search0turn41search3turn39view9turn39view10

## Datasets, ground truth and evaluation

### Relevant datasets

| Dataset or corpus | Modality | What it contains | Why it helps | Why it is not enough | Source |
|---|---|---|---|---|---|
| ACDC | Driving images in adverse conditions | 4,006 adverse-condition images with high-quality annotation; includes night | Night segmentation, uncertainty handling, adverse-condition robustness | No lamp attribution or ground-light targets | citeturn40view6 |
| Dark Zurich | Day, twilight, and night correspondences | Real scene correspondences and night benchmark | Domain adaptation and night consistency | Sparse benchmark; not lamp-centric | citeturn11search9turn11search1 |
| NightCity | Real night-time urban images | 4,297 annotated night images | Night semantic parsing | No lamp usefulness labels | citeturn10search2 |
| Nighttime Driving | Night and dusk scenes | 35,000 unlabeled and 50 densely labeled images | Nighttime segmentation benchmark | Very small dense-label set | citeturn34search13 |
| BDD100K | Diverse driving videos | 100,000 videos and ten tasks | Pretraining, tracking, scene context | Not focused on night lighting quality | citeturn10search11 |
| Mapillary Vistas | Street-level global imagery | 25,000 high-resolution images, 66 or 124 classes; includes street light class | Streetlight context, road and sidewalk parsing | Mostly not night-targeted and not temporal | citeturn32search1turn32search3 |
| nuScenes | Multimodal driving scenes | 1,000 scenes with full camera, radar, lidar suite | Geometry and adverse-context pretraining | Vehicle platform, not phone video, not lamp utility | citeturn41search0turn41search4 |
| Waymo Open Dataset | Multimodal driving scenes | 1,150 twenty-second scenes with calibrated camera and lidar | Detection, tracking, geometry pretraining | Again not phone-based and not lamp-attributed | citeturn41search1turn41search9 |
| SID | Raw low-light imaging | 5,094 raw short to long exposure pairs | Raw low-light denoising and enhancement | Static or still-image bias, not streetlight utility | citeturn22search1 |
| ExDark | Low-light object images | 7,363 images, 10 conditions, 12 classes | Low-light detection robustness | Not a street scene segmentation benchmark | citeturn22search7turn22search15 |
| Low-light Smartphone Dataset | Smartphone low-light pairs | 6,425 pairs, about 0.1 to 200 lux | Smartphone-specific low-light modelling | Not lamp-specific and mostly enhancement-oriented | citeturn22search2turn29search12 |
| UMBRELLA | Fixed upward streetlight monitoring | About 350,000 images from 140 nodes | Lamp condition, drift, anomalies | Wrong viewpoint for public-space illumination | citeturn12search17 |
| Dashcam streetlight 4,260-frame dataset | Dashcam lamp detection | Annotated poles and lamps in night weather | Detection and tracking baseline | No ground-usefulness output | citeturn33search0 |

### What new dataset is needed

A new dataset is unavoidable. No existing open dataset jointly provides hand-held or dashboard phone video, tracked streetlights, ground-plane or public-space regions affected by each lamp, physical light measurements in those regions, and user-task labels. The project therefore needs a purpose-built corpus. citeturn38view0turn38view10turn12search17turn33search0

The core data-collection design for Indian urban roads and public spaces should have four layers. The first layer is phone video from multiple devices in two capture modes: an instrumentation mode with controlled exposure and YUV or RAW when available, and a consumer mode with ordinary camera-app video. The second layer is physical reference: lux-meter ground grids, vertical illuminance at about 1.5 metres in pedestrian zones, and luminance reference photography on a smaller subset. The third layer is semantics and geometry: streetlight boxes and tracks, pole location, visible lamp head, road or sidewalk segmentation, crosswalks, vegetation occlusion, shopfronts, traffic lights, vehicle lights, and approximate pole height. The fourth layer is task labels: obstacle visibility, pedestrian visibility, crossing plausibility, and perceived reassurance. citeturn38view6turn38view7turn38view8turn38view9turn38view10

For Indian deployment, the route design should deliberately cover arterial roads, mixed-traffic corridors, residential lanes, market streets, bus stops, underpasses, flyovers, informal footpaths, and conflict areas around crossings. The local standard anchor should be IS 1944, but field protocol should also follow the clearer public guidance available from FHWA for pedestrian-zone measurements and task framing. citeturn39view2turn38view9turn38view10

The hardest annotation problem is lamp attribution. My recommendation is to avoid pretending to have perfect attribution. Instead, collect three grades of attribution label. “Certain attribution” is for isolated lamps with clear geometry and little confounding light. “Mixed attribution” is for scenes with plausible multiple contributors. “Uncertain attribution” is for heavily mixed or saturated scenes. Training and evaluation should preserve those confidence labels instead of collapsing them into noisy hard targets. That recommendation is an inference from the source-attribution difficulty shown across the monitoring, calibration, and night-perception literature. citeturn38view0turn38view6turn31search6turn40view6

### Evaluation protocol

I recommend five evaluation layers. The first is physical accuracy on the calibrated subset: error in horizontal illuminance, vertical illuminance, and any luminance estimate. The second is spatial attribution: IoU or boundary error for the estimated illuminated footprint on the accessible ground and adjacent public space. The third is task utility: agreement with obstacle visibility, child-sized or adult pedestrian visibility, and crossing-task labels. The fourth is reliability: temporal stability across a lamp track, confidence calibration, and graceful abstention in mixed-light scenes. The fifth is system performance: latency, energy, thermal load, memory footprint, and robustness across phone models. The physical and task layers are supported by the photometry and FHWA-style visibility literature; the reliability and systems layers are necessary additions for an on-device product. citeturn38view6turn38view9turn38view10

What should count as success depends on the formulation. For the calibrated estimator, success means useful physical error on held-out devices and sites, not just on the training route. For the weakly calibrated score, success means strong ranking and classification of underlit or non-useful lamps and good temporal stability, even when absolute lux is off. For the hybrid model, success means better task prediction and better maintenance prioritisation than simple baselines such as lamp brightness, lamp state, or scene average luminance alone. citeturn38view7turn38view8turn40view5turn27search9

## Failure modes, research gaps and recommendations

### Main failure modes and mitigation

The most important failure mode is source confusion. Headlamps, traffic signals, shop signs, windows, and reflections can dominate a scene while the tracked streetlight contributes little. This is mitigated only by explicit semantic masking, geometric reachability, temporal persistence, and attribution confidence. Brightness-only models will fail here. citeturn38view0turn31search6turn40view6

The second failure mode is photometric inconsistency from the phone itself. Auto-exposure, auto-white-balance, HDR, rolling shutter, and codec processing can change the apparent brightness of the same physical scene across frames and across devices. Mitigation requires metadata logging, controlled capture where possible, relative photometric calibration, device-specific normalisation, and a clear separation between physical and weakly calibrated outputs. citeturn38view6turn38view7turn38view8turn29search0turn39view8

The third failure mode is geometric misattribution. A high-mounted lamp may appear close to a footpath in the image but throw most of its light elsewhere; occlusion by foliage, banners, or infrastructure can reduce actual benefit; and a bright lamp may create glare without adequate ground coverage. Mitigation requires explicit pole and lamp geometry, a ground-plane model, vegetation and occluder masks, and footprint estimation rather than lamp-blob reasoning. citeturn31search6turn31search2turn38view5

The fourth failure mode is overclaiming from enhancement. Retinex or diffusion enhancement may produce visually pleasing scenes and better segmentation, but they are not measurements. The mitigation is simple and strict: enhancement can be used as an auxiliary representation only, never as a photometric label source. citeturn16search2turn16search0turn16search1turn41search14

The fifth failure mode is target mismatch. A road-lighting metric can miss pedestrian reassurance or facial visibility, while a pedestrian metric can miss roadway visibility for drivers and cyclists. Mitigation is a multi-output target during research, with task-conditioned reporting at deployment. citeturn39view1turn38view9turn38view10turn27search9

### Research gaps and novelty assessment

The main gap is not object detection. It is attribution plus usefulness. Existing work can already detect streetlights, map ambient illumination, enhance dark images, segment night scenes, estimate rough geometry, and even simulate standard lighting layouts. What is missing is a system that takes casual or instrumented phone video and asks, for this tracked lamp, how much useful illumination reaches the ground and public space that matter to human users. That gap is real. citeturn38view0turn21search2turn38view2turn33search0turn31search3

The second gap is dataset design. Existing night datasets are scene-centric. Existing lighting datasets are either fixed-view lamp-centric or ambient-sensor-centric. None combines lamp attribution, phone capture, physical measurements, visibility tasks, and on-device deployment constraints. A well-designed dataset here would itself be a substantial contribution. citeturn12search17turn33search0turn40view6turn10search2turn34search13turn22search2

The third gap is target formulation. The literature does not justify equating useful illumination with any one of lux, luminance, brightness, or enhancement quality. A hybrid target grounded in standards and human tasks would therefore be novel and scientifically preferable. citeturn39view1turn38view9turn38view10turn9search15

This means the novelty claim should be phrased narrowly and honestly. The novel contribution is not “night-time streetlight detection from dashcam video”, because that already exists. It is not “low-light enhancement on mobile”, because that already exists. It is not “night segmentation”, because that already exists. The genuine novelty is lamp-attributed, task-aware estimation of useful public-space illumination from phone video under realistic phone constraints, with uncertainty and validation against both physical and human-task ground truth. citeturn33search0turn16search1turn40view6turn14search0turn35search1

### Recommended first prototype

The recommended first prototype is Formulation three, but with the ambition level of Formulation two. Build a hybrid weakly calibrated usefulness estimator first. Use a custom capture app with exposure metadata and YUV wherever possible. Detect and track streetlights. Segment road, footpath, crosswalk, vegetation, vehicles, traffic lights, signage, and buildings. Estimate a coarse ground plane and rough lamp-to-ground footprint. Compute exposure-aware and geometry-aware features. Predict a four-class usefulness label and confidence, not lux. Train against a small but carefully calibrated field dataset. citeturn39view8turn14search0turn14search1turn14search2turn35search0turn41search3turn39view9turn39view10

The strongest baselines should be deliberately simple and sceptical. They should include lamp state only, saturated lamp-blob brightness, scene-average luminance proxy, ambient light sensor proxy, and a no-geometry learned score. Any proposed model should beat those baselines not only overall but specifically on confounded scenes, occluded lamps, and mixed-source scenes. That is where the causal structure of the problem should pay off. citeturn21search2turn38view2turn33search0turn31search6

### Recommended long-term direction

The long-term research direction is a standards-aware hybrid model trained on a new dataset with partial physical calibration and total uncertainty awareness. Synthetic augmentation should use lighting simulation, ideally via tools such as SALUSLux, to generate plausible footprints, occlusion scenarios, and standard-derived light patterns. Multi-frame reasoning should mature from simple tracking to exposure-consistent aggregation and local SLAM. Device adaptation should move from phone-specific calibration tables to learned phone embeddings with occasional field calibration. In the best case, the system could eventually output both a public-space usefulness score and approximate standard metrics, with clear confidence flags. citeturn31search3turn31search7turn38view6turn39view1turn39view3

### Open questions and limitations

Three important limitations remain. First, the open standard texts available publicly are incomplete; some detailed CIE, EN, and IES procedures remain behind paywalls, so this review relies partly on official summaries, previews, and public guidance. Second, the open Indian standards material is older than ideal, so any field deployment in India should verify the latest municipal and road-authority requirements before claiming compliance. Third, the literature still does not provide a direct empirical basis for a single universal usefulness metric across motorists, pedestrians, cyclists, and public-space reassurance. That is why I recommend a hybrid output vector during research rather than a premature single scalar. citeturn39view3turn39view1turn39view2turn9search15

## Bibliography

Kumar, S., Deshpande, A., Ho, S. S., Ku, J. S., and Sarma, S. E. Urban Street Lighting Infrastructure Monitoring Using a Mobile Sensor Platform. citeturn38view0

Middya, A. I., Roy, S., and Chattopadhyay, D. CityLightSense: A Participatory Sensing-based System for Monitoring and Mapping of Illumination Levels. citeturn21search2turn30search1

Breda, J., and colleagues. NightLight: Passively Mapping Nighttime Sidewalk Light Data for Improved Pedestrian Routing. citeturn38view2

Mavromatis, I., Tennina, S., and colleagues. A Dataset of Images of Public Streetlights with Operational Monitoring Using Computer Vision Techniques. citeturn12search17

Aiymbay, S., Zhumadillayeva, A., Matson, E. T., Matkarimov, B., and Mukhametzhanova, B. Applying Computer Vision for the Detection and Analysis of the Condition and Operation of Street Lighting. citeturn33search0

Maksimainen, M., Kukko, A., Hyyppä, J., and colleagues. Nighttime Mobile Laser Scanning and 3D Luminance Measurement: Verifying the Outcome of Roadside Tree Pruning with Mobile Measurement of the Road Environment. citeturn31search6turn38view5

Wüller, D., and Gabele, H. The Usage of Digital Cameras as Luminance Meters. citeturn28search3

Bergmann, P., Wang, R., Schindler, K., and Cremers, D. Online Photometric Calibration of Auto Exposure Video for Realtime Visual Odometry and SLAM. citeturn38view6turn40view1

Zalewski, S., and colleagues. The Photometric Testing of High-Resolution Digital Cameras from Smartphones: A Pilot Study. citeturn38view7

Thounaojam, A., and colleagues. Luminance Measurements using Smartphone Cameras. citeturn38view8

Liba, O., Murthy, K., Tsai, Y.-T., Brooks, T., Xue, T., Karnad, N., He, Q., Barron, J. T., Sharlet, D., Geiss, R., Hasinoff, S. W., Pritch, Y., and Levoy, M. Handheld Mobile Photography in Very Low Light. citeturn29search0

CIE 115:2010. Lighting of Roads for Motor and Pedestrian Traffic. citeturn39view3

CIE 191:2010. Recommended System for Mesopic Photometry based on Visual Performance. citeturn39view4

EN 13201-2:2015. Road Lighting Performance Requirements. citeturn39view1turn40view7

FHWA. Pedestrian Lighting Primer. citeturn38view9turn40view2

FHWA. Street Lighting for Pedestrian Safety. citeturn38view10turn40view3

IS 1944, Code of Practice for Lighting of Public Thoroughfares. citeturn39view2turn40view8

Fotios, S., Cheal, C. Using Obstacle Detection to Identify Appropriate Illuminances for Lighting in Residential Roads. citeturn40view5

Fotios, S., Mao, Y., Uttley, J., and Cheal, C. Road Lighting for Pedestrians: Effects of Luminaire Position on the Detection of Raised and Lowered Trip Hazards. citeturn40view4

Fotios, S. Measure for Measure: Semi-Cylindrical Illuminance: A Semi-Conceived Measure? citeturn38view13

Fotios, S., Unwin, J., and Farrall, S. Road Lighting and Pedestrian Reassurance after Dark: A Review. citeturn27search9

Fotios, S. The Basis of Luminance and Illuminance Recommendations. citeturn9search15

Sakaridis, C., Wang, H., Li, K., Zurbrügg, R., Jadon, A., Abbeloos, W., Reino, D. O., Van Gool, L., and Dai, D. ACDC: The Adverse Conditions Dataset with Correspondences for Semantic Driving Scene Understanding. citeturn40view6

Sakaridis, C., Dai, D., and Van Gool, L. Guided Curriculum Model Adaptation and Uncertainty-Aware Evaluation for Semantic Nighttime Image Segmentation. citeturn11search9

Tan, X., Xu, K., Cao, Y., Zhang, Y., Ma, L., and Lau, R. W. H. Night-time Scene Parsing with a Large Real Dataset. citeturn10search2

Dai, D., and Van Gool, L. Semantic Image Segmentation from Daytime to Nighttime and the Nighttime Driving Dataset. citeturn34search13

Yu, F., and colleagues. BDD100K: A Diverse Driving Dataset for Heterogeneous Multitask Learning. citeturn10search11

Neuhold, G., Ollmann, T., Rota Bulò, S., and Kontschieder, P. The Mapillary Vistas Dataset for Semantic Understanding of Street Scenes. citeturn32search1turn32search7

Caesar, H., Bankiti, V., Lang, A. H., Vora, S., Liong, V. E., Xu, Q., Krishnan, A., Pan, Y., Baldan, G., and Beijbom, O. nuScenes: A Multimodal Dataset for Autonomous Driving. citeturn41search0turn41search4

Sun, P., Kretzschmar, H., Dotiwalla, X., Chouard, A., Patnaik, V., Tsui, P., Guo, J., Zhou, Y., Chai, Y., Caine, B., Vasudevan, V., Han, W., Ngiam, J., Zhao, H., Timofeev, A., Ettinger, S., Krivokon, M., Gao, A., Joshi, A., Zhang, Y., Shlens, J., Chen, Z., and Anguelov, D. Scalability in Perception for Autonomous Driving: Waymo Open Dataset. citeturn41search1turn41search9

Loh, Y. P., and Chan, C. S. Getting to Know Low-light Images with the Exclusively Dark Dataset. citeturn22search7turn22search15

Chen, C., Chen, Q., Xu, J., and Koltun, V. Learning to See in the Dark. citeturn22search1

Sharif, S. M. A., Rehman, A., Abidin, Z. U., Naqvi, R. A., Dharejo, F. A., and Timofte, R. Illuminating Darkness: Enhancing Real-world Low-light Scenes with Smartphone Images. citeturn22search2turn29search12

Wei, C., Wang, W., Yang, W., and Liu, J. Deep Retinex Decomposition for Low-Light Enhancement. citeturn16search2

Guo, C., Li, C., Guo, J., Loy, C. C., Hou, J., Kwong, S., and Cong, R. Zero-Reference Deep Curve Estimation for Low-Light Image Enhancement. citeturn16search0

Howard, A., Sandler, M., Chu, G., Chen, L.-C., Chen, B., Tan, M., Wang, W., Zhu, Y., Pang, R., Vasudevan, V., Le, Q. V., and Adam, H. Searching for MobileNetV3. citeturn35search1

Poudel, R. P. K., Liwicki, S., and Cipolla, R. Fast-SCNN: Fast Semantic Segmentation Network. citeturn14search0

Yu, C., Wang, J., Peng, C., Gao, C., Yu, G., and Sang, N. BiSeNet: Bilateral Segmentation Network for Real-time Semantic Segmentation. citeturn14search1

Tan, M., Pang, R., and Le, Q. V. EfficientDet: Scalable and Efficient Object Detection. citeturn14search2

Zhang, Y., Sun, P., Jiang, Y., Yu, D., Yuan, Z., Luo, P., Liu, W., and Wang, X. ByteTrack: Multi-Object Tracking by Associating Every Detection Box. citeturn35search0

Wofk, D., Ma, F., Yang, T.-J., Karaman, S., and Sze, V. FastDepth: Fast Monocular Depth Estimation on Embedded Systems. citeturn41search3