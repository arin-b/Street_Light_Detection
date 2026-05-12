# Estimating Useful Streetlight Illumination from Night-Time Phone Video

## Executive summary

The literature supports a clear conclusion: the scientifically defensible target is not "is the lamp bright in the image?" and not even "is the lamp on?" It is a task-based, region-aware estimate of how much that specific streetlight improves visibility in the public space it is supposed to serve, after accounting for geometry, camera pipeline, confounding light sources, glare, occlusion, and uncertainty. The strongest standards and human-factors evidence point to a hybrid target: lamp-attributable ground and face-height light on relevant regions, plus uniformity and glare penalties, mapped to a usefulness score for pedestrians, cyclists, and drivers. citeturn27view4turn27view1turn27view2turn27view3turn29view7turn35search0turn35search10

Existing mobile and vehicle-based street-lighting systems mostly measure network condition, illumination along a route, or global light maps. They do not solve the core problem here: attributing useful public-space illumination to one tracked lamp in uncontrolled night-time phone video. Car-mounted systems measure roadway illuminance or luminance with dedicated meters and calibrated cameras; smartphone crowdsourcing systems generate coarse heat maps or luminous indices; recent computer-vision papers detect lamps or faults, but they stop well short of estimating lamp-attributable utility on the ground. citeturn26view1turn29view0turn29view1turn26view2turn34search14turn29view3turn16search5

Ordinary phone video can produce useful proxies, rankings, and weakly calibrated estimates, but not trustworthy absolute lux or luminance in the general case without some calibration. The camera-calibration literature is unequivocal that consumer cameras vary strongly in linearity, gain normalisation, bias, dark current, spectral response, and field dependence, and recent smartphone photometry work warns that high-end smartphone cameras are not universally suitable for luminance measurement without restrictive calibration. Phone camera metadata help, but auto-exposure and downstream processing still break photometric consistency unless the capture stack is controlled. citeturn26view3turn15search9turn15search1turn33search8turn33search13turn29view5

The best near-term research direction is therefore a hybrid on-device model. It should combine streetlight detection and tracking, ground-region parsing, weak geometry, exposure-aware normalisation, confounder detection, multi-frame aggregation, and a learned usefulness head trained against sparse photometric ground truth and task-based labels. Its primary output should be a calibrated or weakly calibrated usefulness score with interpretable sub-metrics, not a single raw lux estimate from a lamp crop. citeturn26view1turn27view2turn29view7turn26view7turn7search20turn8search5turn11search4turn11search2turn12search10turn13search1

The most important false assumptions to reject are these. Raw pixel brightness is not illuminance. Low-light enhancement is not photometric measurement. A bright visible lamp does not imply useful ground illumination. A working lamp can still be practically useless because of height, occlusion, aiming, vegetation, glare, spacing, distance, or competition from other light sources. Night-time object detection accuracy is not evidence of lighting-quality accuracy. citeturn26view3turn33search13turn10search18turn21search12turn27view1turn27view2

### Direct answers to the core research questions

The most defensible definition of useful illumination is a task-based, lamp-attributable utility function over the road, footway, crossing, or adjacent public-space region, anchored to standard lighting concepts such as horizontal illuminance, vertical or semi-cylindrical illuminance, luminance, uniformity, surround ratio, and glare, but expressed in a way that remains measurable from video. For pedestrians, the most relevant tasks are obstacle detection, seeing route boundaries, and recognising people at roughly face height; for drivers, the relevant tasks are hazard detection, contrast, guidance, and glare control. citeturn27view4turn27view1turn27view2turn37view2turn37view3turn35search0turn35search10turn29view7

Ordinary phone video can estimate useful illumination well enough for ranking, maintenance triage, and risk screening, but not for universally trustworthy absolute photometry without at least partial calibration. The minimum trustworthy calibration is a device profile, access to exposure and sensitivity metadata, a linear or approximately linear image domain, camera pose and field of view, and sparse site- or device-specific reference measurements. RAW or at least locked manual capture is much more credible than ordinary auto video. citeturn26view3turn15search9turn15search1turn33search8turn33search13

Image-based proxies remain useful even when absolute lux is imperfect. Relative ranking of lamp usefulness, coverage fraction over the relevant ground region, visibility risk flags, glare penalties, and confidence-calibrated categorical ratings are all defensible if they are explicitly framed as proxies rather than direct photometric truth. citeturn27view2turn35search12turn35search0turn29view7

The main novelty of this problem is joint per-lamp attribution under uncontrolled mobile video. Streetlight literature mostly measures route-level lighting or faults; night-vision literature mostly improves recognition under night conditions; photometry literature mostly assumes calibration or static scenes. The intersection of these three is still largely open. citeturn26view1turn29view0turn29view1turn16search5turn26view3turn10search18turn21search12

## Problem formulation and target definition

### Precise problem formulation

Input: a detected and temporally tracked streetlight in night-time mobile-phone video, plus whatever phone metadata are available, such as timestamp, frame rate, exposure time, sensor sensitivity, lens intrinsics, IMU, and approximate location. Output: a per-lamp estimate of practical illumination utility on the ground and nearby public space, with uncertainty. The system may additionally output lamp state, condition flags, coverage masks, and weakly calibrated photometric quantities. citeturn26view1turn29view0turn15search9turn15search1

A good formulation must separate three levels that prior work often conflates. First, lamp condition: on, off, dim, flickering, occluded, saturated, or confused. Second, lamp contribution: what part of the visible ground or public space is plausibly illuminated by that lamp. Third, task utility: whether that contribution is sufficient, uniform enough, and not too glary for a relevant human task. The literature covers the first reasonably, touches the second indirectly, and barely addresses the third. citeturn16search5turn26view1turn29view0turn27view2turn29view7

### What “useful illumination” should mean

For roads and conflict areas, the standards literature is dominated by pavement luminance or roadway illuminance, their uniformity, and glare control. entity["organization","CIE","lighting standards body"] 115:2010 frames classes for motorised traffic, conflict areas, and pedestrian areas, and explicitly supports adaptive lighting. The publicly accessible summary makes clear that the relevant class depends on the visual task and whether a luminance or illuminance concept is appropriate. citeturn27view4

For pedestrian spaces, the evidence is more mixed. CIE 115 uses horizontal illuminance in the P classes because pedestrian gaze and viewed surfaces are varied, while road-luminance design is more straightforward for drivers. Yet entity["people","Steve Fotios","lighting researcher"] argues that metrics should be driven by credible empirical evidence and notes that the evidence for semi-cylindrical illuminance as a superior pedestrian-design metric is weaker than often assumed. He also shows that pedestrian reassurance may be better predicted by minimum or uniformity-related measures than by average illuminance alone. citeturn29view7turn29view6turn35search12

The most defensible definition for this project is therefore not a single physical scalar. It is a hybrid, task-specific output:

A lamp-attributable coverage mask over relevant task regions, such as carriageway, pavement, crossing, curb zone, or immediate public-space foreground.

A weakly calibrated estimate of maintained light level on those regions, preferably horizontal illuminance on the ground plus vertical or semi-cylindrical illuminance at about pedestrian face height where relevant.

Uniformity and coverage statistics over the affected region.

A glare penalty based on source visibility, saturation, and veiling effects.

A final usefulness score, continuous or categorical, that maps the above to “inadequate”, “marginal”, “adequate”, or “good” for a stated task class. citeturn27view4turn27view1turn27view2turn37view0turn37view1turn37view2turn37view3turn37view6turn37view8

### Critical comparison of target variables

A pure lux target is attractive because it sounds objective, but from uncontrolled phone video it is the hardest to trust. Illuminance is incident light on a surface; image brightness depends on exposure, gain, spectral sensitivity, reflectance, viewpoint, tone mapping, and compression. Even if average roadway illuminance or face-height vertical illuminance are the eventual reference metrics, they should not be the only learning target. citeturn26view3turn33search8turn27view1turn27view2

A pure luminance target is more standards-aligned for roads, but it still requires calibrated imaging and, for meaningful interpretation, knowledge of geometry and surface reflectance; even the road-lighting measurement literature typically relies on dedicated imaging sensors or correction functions when the camera is off the standard observer position. citeturn29view4turn34search0turn34search1

A pure visual-usefulness score is much easier to learn and deploy but risks becoming subjective and non-transferable if it is not anchored to standards and human tasks. It should therefore be standards-informed rather than purely perceptual. citeturn35search0turn35search8turn27view2

The strongest recommendation is a hybrid target:
physical-lite sub-targets where calibration is possible;
proxy sub-targets where it is not;
and a final decision-layer score that is explicitly task-conditioned. citeturn27view2turn27view1turn29view7

## Prior work, standards, and datasets

### Taxonomy of prior work

The literature splits into eight useful clusters.

Streetlight and urban-lighting monitoring systems use vehicle platforms, lux meters, cameras, GIS, or smartphone crowdsourcing to map route-level lighting, geotag assets, or prioritise maintenance. They are closest in application, but usually not per-lamp or phone-video first. citeturn26view1turn29view0turn29view1turn26view2turn34search14turn29view3

Camera-based photometry studies calibrate cameras for luminance or radiometry, often in controlled settings or with dedicated imaging sensors. These are crucial because they define what video can and cannot mean physically. citeturn26view3turn33search8turn33search13turn29view4turn29view5

Road-lighting standards and pedestrian-lighting guidance define the quantities that matter operationally: average luminance, uniformity, veiling luminance, vertical or semi-cylindrical illuminance, surround ratio, and mesopic adaptation. They tell us what outputs would be meaningful if we could estimate them. citeturn27view4turn27view1turn27view2turn27view3turn19search2turn19search5

Human-visibility and safety studies link light to obstacle detection, pedestrian detection, reassurance, facial recognition, and glare. These studies suggest that one score should not be shared across drivers, pedestrians, and crossings without conditioning on task. citeturn27view2turn35search0turn35search10turn35search8turn35search11turn36search2

Night-time computer vision provides the best available tools for segmentation, exposure handling, and adverse-condition learning, but its labels are about semantics, not lighting utility. citeturn8search5turn7search20turn26view7turn30view4turn30view5

Low-light enhancement and intrinsic decomposition help visibility and downstream recognition, but they are not direct measurements of scene illumination. Their objective functions are largely perceptual or task-oriented. citeturn10search18turn10search3turn9search12turn32search1turn32search2turn20search0

On-device vision gives plausible backbones for deployment, including mobile detection, segmentation, tracking, and model compression frameworks. citeturn11search4turn11search16turn11search2turn23search1turn23search0turn12search10turn13search1

Multi-frame reasoning is essential because a single frame cannot robustly infer while separating other moving lights, estimating coverage, or handling exposure jumps. Optical flow in the dark, rolling-shutter analysis, and tracking literature all support the need for temporal aggregation. citeturn23search6turn21search11turn17search8turn23search1turn23search0

### Table of key papers and systems

| Paper or system | Problem | Input and output | Calibration assumptions | Why it matters here |
|---|---|---|---|---|
| Kumar et al., *Urban Street Lighting Infrastructure Monitoring Using a Mobile Sensor Platform* | Car-mounted mapping of street illumination, lamp detection, lamp height, geotagging | Night drive-by sensors and video to route-level illumination and lamp inventory | Dedicated mobile sensing platform and EKF-style localisation | Closest application precursor, but it is platform-heavy and not phone-video first. citeturn26view1 |
| Middya et al., *CityLightSense* | Participatory sensing for illumination mapping | Citizen sensing to illumination map | Assumes noisy public sensing; focuses on mapping rather than per-lamp attribution | Shows crowdsourced urban-lighting monitoring is feasible, but output is global map, not lamp usefulness. citeturn29view0 |
| Kumar, *Street Light Monitoring Using Smartphones* | Smartphone crowd sensing of poor lighting | Phone sensing to luminous index and heat maps | Weak calibration; server-side aggregation | Useful as a low-cost baseline, but not a physical or task-calibrated measure. citeturn29view1 |
| Tomczuk et al., *Evaluation of Street Lighting Efficiency Using a Mobile Measurement System* | Rapid route-level energy and illuminance assessment | Vehicle lux meters to GNSS-localised road-lighting metrics | Physical meters on vehicle roof | Important evidence that serious lighting assessment usually adds external meters. citeturn26view2 |
| Gibbons et al., *Roadway Lighting Mobile Measurement System* | Mobile roadway lighting measurement | Five illuminance meters plus calibrated luminance camera | Explicit metrological instrumentation | Strong baseline for ground truth collection, not for consumer-video inference. citeturn34search14 |
| Chen et al., *Design of an Equipped Vehicle for In Situ Road Lighting Measurement* | Efficient field measurement of illuminance and luminance | Special vehicle with photometric sensors | Dedicated equipment and precise positioning | Reinforces that standard-compliant measurement is hardware-intensive. citeturn29view3 |
| Burggraaff et al., *SPECTACLE* | Spectral and radiometric calibration of consumer cameras | Consumer cameras to calibration database | RAW access and controlled calibration procedures | Fundamental for understanding phone-model variation and why ordinary sRGB video is unreliable for absolute light estimation. citeturn26view3 |
| Zalewski and Skarżyński, *The Photometric Testing of High-Resolution Digital Cameras from Smartphones* | Whether smartphone cameras can measure luminance | High-end smartphones to luminance suitability judgement | Restrictive laboratory calibration | Important negative evidence: phones are not universally suitable photometric instruments. citeturn33search8turn33search13 |
| Rusu et al., *Measuring Average Luminance for Road Lighting from Outside the Carriageway* | Camera-based roadway luminance estimation | Digital camera to average road luminance | Specific geometry; correction needed for some layouts | Useful for deriving weak photometric heads and showing observer-position sensitivity. citeturn29view4 |
| Chen et al., *Learning to See in the Dark* | RAW low-light reconstruction | RAW short exposure to long-exposure reference | Static scenes, RAW, paired supervision | Valuable for low-light modelling, but objective is image reconstruction, not physical light measurement. citeturn26view5 |
| Guo et al., *Zero-DCE* | Zero-reference low-light enhancement | RGB image to enhanced image | No physical calibration; perceptual non-reference losses | Good cautionary example: enhancement can help downstream tasks but should not be mistaken for photometry. citeturn10search18turn10search2 |
| Sharma and Tan, *Nighttime Visibility Enhancement by Increasing the Dynamic Range and Suppression of Light Effects* | Remove glare and improve visibility | Single night image to enhanced image | Semi-supervised image enhancement, not physical measurement | Useful as a pre-processing ablation, not as a measurement oracle. citeturn32search2 |
| Sakaridis et al., *Dark Zurich* | Night-time semantic adaptation and uncertainty-aware evaluation | Day-night correspondences to night segmentation | Semantic, not photometric | Critical for scene parsing and uncertainty handling under night ambiguity. citeturn8search5turn30view6 |
| Sakaridis et al., *ACDC* | Adverse-condition semantic driving benchmark | Driving images to segmentation under night, rain, fog, snow | Semantic labels and invalid regions | Important for robust parsing and handling unrecognisable regions. citeturn28view2 |
| Tan et al., *NightCity* | Large real night-time semantic segmentation dataset | Real night RGB to segmentation; exposure-aware network | Semantic and exposure-aware, not physical light | Especially relevant because it explicitly models mixed under- and over-exposure around lights. citeturn28view3 |
| Howard et al., *MobileNetV3* and Poudel et al., *Fast-SCNN* | Mobile classification and real-time segmentation | RGB to classes or semantic masks | Standard deep-learning deployment assumptions | Strong candidates for on-device detector and parser backbones. citeturn11search4turn11search2 |

### Table of relevant datasets

| Dataset | What it contains | Night relevance | Main use here | Main limitation |
|---|---|---|---|---|
| Dark Zurich | 2,416 night, 2,920 twilight, 3,041 day images with coarse day-night correspondences, plus labelled night benchmark | High | Night semantic parsing, domain adaptation, uncertainty-aware evaluation | No lamp-attributable illumination labels. citeturn8search5turn31search23 |
| ACDC | 4,006 pixel-level annotated adverse-condition images equally distributed across fog, night, rain, snow | High | Robust scene parsing and invalid-region handling | Not phone capture; no lighting utility labels. citeturn28view2 |
| NightCity | 4,297 real night-time images with pixel-wise annotations; exposure-aware benchmark | High | Night segmentation and exposure handling | No per-lamp attribution or photometric truth. citeturn28view3 |
| urlBDD100Kturn7search7 | 100K driving videos and ten tasks | Moderate, with night subset | Detection, drivable area, tracking, temporal learning | Night labels are not designed for lighting analysis. citeturn30view4turn7search1 |
| ExDark | 7,363 low-light images, 12 object classes, ten low-light conditions | High for low-light objects | Low-light object and confounder detection | Not street-scene specific and no illumination ground truth. citeturn30view5 |
| urlMapillary Vistasturn24search2 | 25,000 street-level images from varied daytime and weather conditions | Some night coverage, but not night-first | Extra segmentation pre-training for road, pavement, building, sign classes | Lighting labels absent; night share unclear. citeturn31search2turn31search14 |
| urlnuScenesturn24search0 | Large AV dataset with multi-camera, lidar, radar, GPS, IMU | Has night scenes | Geometry priors and confounder examples | Not designed for streetlight usefulness; access and preprocessing overhead. citeturn31search0turn31search4turn31search20 |
| urlWaymo Open Datasetturn24search5 | Large perception, motion, and end-to-end driving datasets | Some night and diverse urban driving conditions | Cross-domain detector and parser pre-training | Again, no lamp-attribution or photometric labels. citeturn31search13turn31search17 |
| SDSD | Paired low- and normal-light dynamic videos | High for enhancement studies | Video enhancement ablations and temporal denoising | Enhancement target, not lighting truth. citeturn9search12turn9search3 |
| SID | RAW short-exposure low-light images with long-exposure references | Outdoor night and very low illuminance | Sensor-level low-light modelling | Static scenes, not mobile video or streetlight attribution. citeturn26view5 |

The most important dataset fact is negative: there is no standard dataset that jointly provides tracked streetlights, affected-region masks, confounder annotations, phone-camera metadata, and per-lamp usefulness ground truth. That dataset will need to be created. citeturn26view1turn29view0turn28view2turn28view3turn8search5

### Table of standards and lighting metrics

| Standard or guidance | Metrics emphasised | Direct usability for this system | Key warning |
|---|---|---|---|
| CIE 115:2010 | M, C, P classes; luminance or illuminance concepts depending on task | Very useful as the conceptual backbone for target design | It is an installation-design standard, not a lamp-crop video standard. citeturn27view4 |
| CIE TN 007:2017 | Mesopic adaptation coefficient and mesopic quantities for outdoor lighting | Useful for low-luminance road and pedestrian scenes | Requires adaptation luminance and source S/P information that ordinary phone video does not directly observe. citeturn27view3turn28view6 |
| EN 13201 family | Class selection, calculation, measurement methods, energy indicators | Useful for field protocol, grids, and energy reporting | Much of the detailed text is not openly accessible; public summaries must be used carefully. citeturn27view5turn26view2 |
| IES RP-8-18 as summarised by the FHWA primer | Average luminance, uniformity ratios, veiling luminance ratio, trespass limits | Useful for roadway-oriented sub-metrics | Needs road class and proper geometry. citeturn37view3turn37view5 |
| FHWA Pedestrian Lighting Primer | Vertical illuminance, semi-cylindrical illuminance at 2 m, surround ratio, glare, luminance examples | Highly useful for pedestrian/public-space formulation | It is guidance, not universal truth, and not all criteria are mandatory. citeturn37view0turn37view1turn37view2turn28view4 |
| FHWA Street Lighting for Pedestrian Safety | Face-height semi-cylindrical and vertical illuminance recommendations tied to driver detection | Highly useful for crossings and child-sized pedestrian visibility | Context-specific; should not be over-generalised to every public space. citeturn27view2turn37view6turn37view7turn37view8 |
| BIS IS 1944 parts 1 and 2, and part 5 | Indian public-thoroughfare lighting, visual guidance, glare, grade-separated junctions | Useful for local practice in entity["country","India","south asia"] and road categorisation | The documents are dated and less aligned with current pedestrian-focused evidence than recent CIE and FHWA guidance. citeturn19search2turn19search5turn19search15 |

## Proposed technical direction

### Proposed technical formulation for useful illumination

The recommended research target is:

**Usefulness(lamp, task, region, time)**  
= expected visibility benefit on the region served by the tracked lamp  
minus penalties for non-uniformity, glare, occlusion, misdirection, and confounding sources,  
with an uncertainty estimate.

In practice, the model should expose six interpretable outputs.

A lamp-state head: off, on, dim, flickering, saturated, occluded, or ambiguous. Rolling-shutter and temporal-light-modulation literature suggest that some LED flicker information may be recoverable from video artefacts, but this is device- and frame-rate-dependent. citeturn16search5turn21search11turn17search8

A contribution-footprint head: a soft mask over road, pavement, crossing, curb, or plaza pixels plausibly attributable to the lamp. This should be inferred jointly from geometry, scene parsing, apparent lamp position, pole height priors, and temporal consistency. It is the least explored subproblem in prior work and one of the most novel pieces. citeturn26view1turn29view0turn28view3turn28view2

A weak-photometry head: estimated ground-region and face-height light quantities in a device-normalised domain. If RAW or manual-capture metadata are available, this head can be more physical. If not, it should explicitly degrade to weak calibration. citeturn26view3turn15search9turn33search8

A confounder head: tags for vehicle headlights, brake lights, shopfronts, signage, traffic signals, house windows, reflections, wet road specularity, and sky glow. This head is essential because public-space utility is about lamp contribution, not total scene brightness. citeturn21search6turn20search16turn21search12

A glare head: source prominence, saturation halo, and veiling-luminance proxy near the line of sight. Standards treat glare as a first-class design variable, and enhancement literature shows that strong lights can dominate night images without improving visibility behind them. citeturn37view3turn28view4turn32search2

A final usefulness head: a continuous score and a categorical rating, confidence-calibrated, standards-anchored, and task-conditioned. citeturn27view2turn29view7

### Candidate model architectures

The most plausible on-device architecture is a multi-head, two-stage pipeline. Stage one is efficient perception. Use a light detector and tracker to keep the target lamp identity stable over time, and a compact parser to segment road, footway, curb, marking, vegetation, building facade, and dynamic objects. Mobile backbones such as MobileNetV3 and Fast-SCNN are the right design family, not large night-time transformers. citeturn11search4turn11search2turn23search1turn23search0

Stage two is exposure-aware reasoning. Feed the lamp track, scene masks, metadata, and a small temporal window into a lightweight temporal model. A Gated Recurrent Unit or shallow temporal transformer is plausible, but the key is not the sequence model itself; it is the explicit side information: exposure time, sensitivity, frame interval, rolling-shutter status if known, and whether the lamp core is clipped. citeturn15search9turn15search1turn21search11

Weak geometry can be estimated in one of three ways. The lightest option is planar homography plus horizon or vanishing-point cues. The middle option is monocular mobile depth. The strongest option is visual-inertial pose plus coarse map priors, if GNSS and IMU are available. For mobile deployment, a coarse ground-plane model is likely more robust than dense metric depth in night video. citeturn14search5turn14search21turn23search6

For deployment, the most realistic software targets are urlTensorFlow Liteturn12search19 with post-training quantisation or quantisation-aware training, and urlCore MLturn13search1 with the device-local Vision stack for detection or tracking integration. Both toolchains explicitly support model optimisation for edge execution. citeturn12search1turn12search4turn12search10turn13search6

### Three concrete formulations

**Formulation 1: standards-driven calibrated photometric estimator.**  
Input: phone video with locked capture if possible, device calibration, camera intrinsics, metadata, and sparse site calibration. Output: per-lamp affected-region mask plus calibrated illuminance or luminance proxies and a standards-threshold pass/fail judgement. Ground truth: lux meters, luminance camera or HDR reference, survey geometry, lamp metadata. Why it may work: it is the cleanest scientifically and aligns best with CIE, EN, IES, and FHWA concepts. Why it may fail: ordinary phone video often lacks the control and linearity needed; reflectance and confounders remain hard. Evaluation: physical MAE and task-threshold accuracy. On-device feasibility: limited unless the capture app controls the camera pipeline tightly. citeturn26view3turn29view4turn27view1turn27view2turn27view3

**Formulation 2: weakly calibrated visual-usefulness score.**  
Input: ordinary phone video, metadata when available, scene parsing, lamp tracking. Output: score or rating for useful illumination, plus uncertainty and confounder flags. Ground truth: sparse lux or luminance measurements, human annotation of adequacy, and task-based labels such as pedestrian visibility or crossing adequacy. Why it may work: it matches what phones can reliably sense and absorbs device variation statistically. Why it may fail: risk of learning dataset-specific brightness shortcuts unless calibration and confounder controls are explicit. Evaluation: ranking correlation, calibration error, macro F1, and task transfer across devices. On-device feasibility: high. citeturn29view1turn35search0turn35search12turn27view2turn11search4turn11search2

**Formulation 3: hybrid on-device model.**  
Input: tracked lamp, parsed scene, weak geometry, capture metadata, short video window. Output: lamp state, coverage mask, weak photometric estimates, glare penalty, and final usefulness score. Ground truth: all of the above, but not at dense scale; sparse photometric calibration and dense semantic labels are enough initially. Why it may work: it combines the strongest ideas from standards, mobile sensing, and night vision while staying deployable. Why it may fail: attribution errors may dominate; one lamp’s footprint can overlap with another’s, and bright dynamic lights can overwhelm the signal. Evaluation: multi-task benchmark with physical, semantic, ranking, temporal, and latency metrics. On-device feasibility: best overall trade-off. citeturn26view1turn29view0turn27view2turn28view3turn28view2turn12search10turn13search1

### Strongest baselines

The strongest baselines are not all deep. A simple lamp-state classifier is the minimum baseline. A lamp-crop brightness regressor normalised by exposure metadata is the next baseline. A scene-level night-brightness score, without attribution, is a useful negative control because it will often fail precisely where the problem is hard. A standards-naive geometric baseline can project a cone from the lamp to the ground and average normalised brightness on the segmented road or pavement. Finally, external-meter baselines from route-level vehicle systems should be used for upper-bound comparison on the same sites. citeturn29view1turn26view1turn26view2turn34search14

### Main failure modes and mitigation strategies

The first failure mode is camera inconsistency. Different phones, lenses, codecs, and pipelines can turn the same scene into very different pixel values. Mitigation: device-aware training, metadata conditioning, per-device calibration cards or sparse site calibration, and preferably RAW or locked manual capture during dataset collection. citeturn26view3turn33search13turn15search9

The second failure mode is confounding light. Shopfronts, signs, vehicle lamps, and reflections can dominate the apparent brightness of the area that the streetlight nominally serves. Mitigation: semantic confounder labels, temporal suppression of moving lights, and contribution modelling that conditions on lamp geometry and scene surfaces rather than raw local brightness. citeturn21search6turn20search16turn21search12

The third failure mode is saturation and glare. A lamp can bloom in the image and still provide poor visibility where it matters. Mitigation: clip detection, source-mask features, adjacent-region analysis, and explicit glare penalty heads. citeturn28view4turn37view3turn32search2

The fourth failure mode is wrong affected-region inference, especially when the lamp is far away, mounted high, partially hidden by trees, or competing with adjacent poles. Mitigation: ground-plane priors, pole-height estimation, multi-frame consistency, and supervision on coverage masks rather than only final scores. citeturn26view1turn29view0

The fifth failure mode is target mismatch. A roadway-lighting metric can declare success while pedestrians still cannot see faces or obstacles on the footway. Mitigation: separate task classes and separate sub-metrics for carriageway, crossing, and pedestrian space. citeturn27view2turn29view7turn35search10turn35search0

## Dataset, ground truth, and evaluation

### Dataset and ground-truth collection plan for India

A practical dataset for entity["organization","Bureau of Indian Standards","india standards body"]-style public-thoroughfare settings and contemporary urban streets should be structured in tiers.

Tier one should be scalable phone capture. Collect night-time video from handheld walking, bicycle, scooter, car, and slow-drive dashboard viewpoints across arterial roads, lane streets, bus stops, footpaths, parks, underpasses, and crossings. Record frame timestamps, GPS, IMU, focal length, exposure time, and sensitivity when the device exposes them. Repeat the same corridors on multiple nights and from multiple phone models. citeturn15search9turn15search1turn19search2turn19search5

Tier two should be sparse physical reference. At representative sites only, capture standard-ish measurement grids using lux meters over road and footway, face-height vertical or semi-cylindrical measurements at crossings and pedestrian zones, and where possible a calibrated luminance camera or HDR still camera. Vehicle-mounted systems from the road-lighting literature are excellent templates for this tier. citeturn26view2turn34search14turn29view3turn29view4turn27view2

Tier three should be scene annotations. Label lamp tracks, pole centre, lamp head, visible occluders, confounder categories, saturation, glare, road and footway masks, crossing masks, and most importantly the region plausibly served by the tracked lamp. Because that final label is subjective if done by hand, it should be bootstrapped from geometry and then corrected by annotators. citeturn26view1turn28view2turn28view3

Tier four should be maintenance and metadata linkage. Where municipalities can provide pole GIS, mounting height, lamp type, installed wattage, CCT, arm length, and outage logs, link them. This is especially valuable for Indian roads, where one-sided mounting, median lighting, vegetation, and informal shop lighting create frequent mismatches between nominal design and actual usefulness. The literature and standards both imply that installation geometry and obstacles materially affect real lighting quality. citeturn26view2turn29view3turn19search2turn19search15

### Evaluation protocol

Evaluation should be multi-level.

For lamp detection and tracking, use precision, recall, tracking accuracy, identity stability, and failure under saturation or occlusion. Night-time detection benchmarks alone are not enough; the target object is small, bright, and often clipped. citeturn16search5turn23search1turn23search0

For affected-region estimation, use mask IoU and boundary F-score on the lamp-attributable coverage mask, stratified by road class, pole spacing, single-sided versus staggered layouts, and confounder density. No existing public benchmark currently provides this target, so a custom benchmark is required. citeturn29view4turn26view1

For physical-lite estimates, use MAE, RMSE, and ranking correlation against lux and luminance references, separately for ground horizontal, face-height vertical or semi-cylindrical, and roadway luminance. Report device-conditioned and device-held-out splits. citeturn29view4turn27view2turn33search13

For final usefulness, use macro F1 for categorical adequacy, Spearman or Kendall correlation for ranking, expected calibration error for confidence, and temporal stability over tracks. Success should mean not only good average accuracy but stable decisions over adjacent frames and across devices. citeturn8search5turn27view2turn35search12

For deployment, report model size, average latency, and battery-aware runtime on a representative Android phone under urlTensorFlow Liteturn12search19 and on an iPhone under urlCore MLturn13search1. Qualitative “real-time” claims are too weak. citeturn12search10turn12search1turn13search1

### Recommended first prototype

The most sensible first prototype is not the fully calibrated estimator. It is a hybrid weakly calibrated model.

Build a phone app that captures short night clips with exposure metadata. Detect and track lamp heads. Segment road, footway, and crossing regions. Estimate a coarse ground plane. Compute a manually designed baseline score using exposure-normalised local brightness on the served region, a saturation penalty, a confounder penalty, and a uniformity proxy. Then train a lightweight learned head on top of those features using sparse lux or luminance reference and categorical adequacy labels. This prototype is scientifically honest, operationally useful, and achievable on-device. citeturn26view1turn29view1turn29view4turn11search4turn11search2turn12search10

### Recommended long-term research direction

The long-term direction should move towards a standards-aware digital twin of per-lamp utility. That means learning lamp contribution fields under mobile video, using GIS or map priors when available, explicitly modelling mesopic adaptation and source spectrum where deployment permits, and incorporating human-task simulators rather than only photometric labels. The end goal should be a confidence-aware maintenance and safety tool that says not only whether a lamp is faulty, but whether it is failing the space and users it is meant to serve. citeturn27view4turn27view3turn27view2turn35search0turn35search11

### Research gaps, novelty, and open questions

The decisive gap is per-lamp attribution. Existing systems assess roads, routes, or networks; they do not isolate one tracked streetlight’s useful spatial contribution from phone video. The second gap is standards translation: the field knows what to measure in installations, but not how to estimate equivalent task-relevant quantities from uncontrolled mobile imaging. The third gap is dataset design: current night datasets are semantic, not photometric or utility-based. citeturn26view1turn29view0turn29view1turn28view2turn28view3

What remains incomplete is equally important. Full EN 13201 and IES details are not fully open, so some metric interpretations necessarily rely on authoritative summaries rather than the full standards text. Evidence for semi-cylindrical illuminance as a universally superior pedestrian-design metric remains contested. And there is still no high-confidence public literature on estimating per-lamp useful public-space illumination directly from ordinary phone video, which means the core proposed system is genuinely novel but also high-risk. citeturn27view5turn29view6turn29view7

## Bibliography

Burggraaff, O., Schmidt, N., Zamorano, J., Pauly, K., Pascual, S., Tapia, C., Spyakos, E., and Snik, F. 2019. *Standardized spectral and radiometric calibration of consumer cameras*. Chen, C., Chen, Q., Xu, J., and Koltun, V. 2018. *Learning to See in the Dark*. Guo, C., Li, C., Guo, J., Loy, C. C., Hou, J., Kwong, S., and Cong, R. 2020. *Zero-Reference Deep Curve Estimation for Low-Light Image Enhancement*. citeturn26view3turn10search3turn10search18

Kumar, S., Deshpande, A., Ho, S. S., Ku, J. S., and Sarma, S. E. 2016. *Urban Street Lighting Infrastructure Monitoring Using a Mobile Sensor Platform*. Middya, A. I., et al. 2021. *CityLightSense: A Participatory Sensing-based System for Monitoring and Mapping of Illumination Levels*. Kumar, R. 2021. *Street Light Monitoring Using Smartphones*. Tomczuk, P., et al. 2021. *Evaluation of Street Lighting Efficiency Using a Mobile Measurement System*. Chen, C.-H., et al. 2023. *Design of an Equipped Vehicle for In Situ Road Lighting Measurement*. Rusu, A. V., et al. 2021. *Measuring Average Luminance for Road Lighting from Outside the Carriageway with Imaging Sensor*. citeturn26view1turn29view0turn29view1turn26view2turn29view3turn29view4

Sakaridis, C., Dai, D., and Van Gool, L. 2019. *Guided Curriculum Model Adaptation and Uncertainty-Aware Evaluation for Semantic Nighttime Image Segmentation*. Sakaridis, C., Dai, D., and Van Gool, L. 2021. *ACDC: The Adverse Conditions Dataset with Correspondences for Semantic Driving Scene Understanding*. Tan, X., Xu, K., Cao, Y., Zhang, Y., Ma, L., and Lau, R. W. H. 2020. *Night-time Scene Parsing with a Large Real Dataset*. Yu, F., et al. 2020. *BDD100K: A Diverse Driving Dataset for Heterogeneous Multitask Learning*. Loh, Y. P., and Chan, C. S. 2019. *Getting to Know Low-light Images with the Exclusively Dark Dataset*. citeturn30view6turn28view2turn28view3turn30view4turn30view5

entity["organization","Federal Highway Administration","us transport agency"]. 2022. *Pedestrian Lighting Primer*. Federal Highway Administration. 2021. *Street Lighting for Pedestrian Safety*. entity["organization","Illuminating Engineering Society","lighting standards society"]. 2018. *RP-8-18* as summarised in FHWA guidance. entity["organization","CIE","lighting standards body"]. 2010. *CIE 115: Lighting of Roads for Motor and Pedestrian Traffic*. CIE. 2017. *TN 007: Recommendations for Practical Application of Mesopic Photometry in Outdoor Lighting*. Bureau of Indian Standards. 1970. *IS 1944 Parts 1 and 2*. Bureau of Indian Standards. 1981. *IS 1944 Part 5*. citeturn27view1turn27view2turn27view4turn27view3turn19search2turn19search5

Fotios, S. 2015. *Road lighting and pedestrian reassurance after dark*. Fotios, S. 2017. *Semi-cylindrical illuminance: a semi-conceived measure?* Fotios, S. 2018. *Illuminance required to detect a pavement obstacle of critical size*. Fotios, S. 2019. *Which metrics are needed to specify good lighting for pedestrians?* Welsh, B. C., and Farrington, D. P. 2022 and 2024 updates on street lighting and crime prevention. Zele, A. J., and Cao, D. 2015. *Vision under mesopic and scotopic illumination*. citeturn35search0turn29view6turn35search10turn29view7turn35search11turn36search2

Howard, A., et al. 2019. *Searching for MobileNetV3*. Tan, M., et al. 2020. *EfficientDet*. Poudel, R. P. K., Liwicki, S., and Cipolla, R. 2019. *Fast-SCNN*. Wojke, N., Bewley, A., and Paulus, D. 2017. *Simple Online and Realtime Tracking with a Deep Association Metric*. Zhang, Y., et al. 2022. *ByteTrack*. Zhou, Y., et al. 2024. *Real-time low-light video enhancement on smartphones*. Sharma, A., and Tan, R. T. 2021. *Nighttime Visibility Enhancement by Increasing the Dynamic Range and Suppression of Light Effects*. citeturn11search4turn11search16turn11search2turn23search1turn23search0turn32search1turn32search2