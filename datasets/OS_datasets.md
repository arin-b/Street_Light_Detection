# Open Night-Time Indian Driving Datasets and Proxies

Last updated: May 14, 2026

## Bottom line

I did **not** verify a widely used, dedicated, open **Indian night-only driving benchmark** comparable to `ACDC` or `Dark Zurich`.

What does exist is:

- at least one strong **open Indian driving dataset with explicit night content**
- several **Indian research-access proxies** with low-light, adverse-weather, temporal, multimodal, or night traffic-light relevance
- several strong **non-Indian nighttime driving proxies** that are standard for pretraining or benchmarking

For this project, the practical answer is: **use an Indian dataset for domain realism, then supplement with night-specific global proxies, and expect to curate your own streetlight-focused subset.**

## 1. Best direct Indian match

### 1.1 ThirdEye Labs Indian Road Driving Dataset

- Link: https://huggingface.co/datasets/thirdeyelabs/indian-road-dataset
- Why it matters: this is the strongest direct open match I found.
- Status: open dataset on Hugging Face
- License: `CC BY 4.0`
- Geography: Delhi NCR, India
- Conditions listed on the dataset card: `Day`, `Night`, `Dusk`, `Rain`
- Modalities / labels: image, annotations, scene metadata, GPS tracks
- Use for this project: best starting point for building an **Indian night subset** for roadway-lighting and streetlight-context modeling
- Caveat: not streetlight-specific and not night-only

## 2. Indian proxies

These are useful because they are Indian-road datasets, but they are not cleanly released as night-only street-scene benchmarks.

### 2.1 IDD-AW

- Link: https://insaan.iiit.ac.in/
- Why it matters: official Indian benchmark family entry that explicitly includes `lowlight`
- Host: INSAAN / IIIT Hyderabad
- Relevance: useful low-light proxy for scene visibility, glare, weather, and robustness
- Caveat: adverse-weather and low-light benchmark, not a dedicated night-driving streetlight dataset

### 2.2 IDD

- Links:
  - https://idd.insaan.iiit.ac.in/
  - https://insaan.iiit.ac.in/
- Why it matters: canonical Indian driving benchmark family
- Relevance: strong proxy for Indian road geometry, poles, sidewalks, occlusions, mixed traffic, and unstructured urban scenes
- Night relevance: the original IDD paper explicitly includes varying lighting conditions, but the dataset is not packaged as a night-only benchmark
- Caveat: useful for Indian domain transfer, less useful as a direct night benchmark

### 2.3 IDD Temporal

- Link: https://insaan.iiit.ac.in/
- Why it matters: temporal context helps with moving-camera nighttime perception
- Relevance: proxy for tracking, temporal smoothing, and persistence logic
- Caveat: not explicitly a night-focused release

### 2.4 IDD Multimodal

- Link: https://insaan.iiit.ac.in/
- Why it matters: adds geometry and sensor-fusion context
- Relevance: proxy for road-layout priors, depth cues, and structure-aware modeling
- Caveat: not night-specific

### 2.5 IDD-3D

- Links:
  - https://insaan.iiit.ac.in/
  - https://github.com/shubham1810/idd3d_kit
- Why it matters: Indian 3D driving scenes with camera and LiDAR support
- Relevance: geometry-heavy proxy for understanding pole height, object placement, and roadside structure
- Caveat: not a night benchmark

### 2.6 I2WDD

- Link: https://insaan.iiit.ac.in/
- Why it matters: Indian riding/driving data from a different motion profile
- Relevance: proxy for mobile-video behavior under Indian traffic dynamics
- Caveat: not streetlight-focused and not clearly night-first

### 2.7 TiAND / DriveIndia

- Links:
  - https://tihan.iith.ac.in/TiAND.html
  - https://arxiv.org/abs/2507.19912
- Why it matters: TiAND is presented by TiHAN IIT Hyderabad as `100% Open Source`, and the DriveIndia paper describes a large Indian object-detection dataset with illumination variation
- Relevance: useful Indian proxy if you want more recent Indian road footage and diverse driving conditions
- Caveat: this is broader autonomy data, not a dedicated night benchmark, and actual night coverage should be confirmed per subdataset before relying on it

### 2.8 Roadscapes / RoadscapesQA

- Links:
  - https://arxiv.org/abs/2602.12877
  - https://github.com/roadscapes/roadscapes_data
- Why it matters: recent Indian road dataset explicitly described as including both daytime and nighttime settings
- Relevance: useful monocular Indian proxy with urban, rural, and highway scenes
- Caveat: the paper is recent, and practical download/access details should be checked before depending on it in a pipeline

### 2.9 IRD: Indian Roads Dataset for Traffic Lights

- Links:
  - https://sites.google.com/view/ird-dataset/home
  - https://arxiv.org/abs/2209.04203
- Why it matters: this one is not a general driving dataset, but it is directly relevant to **light-source detection on Indian roads**
- Relevance: day and night traffic-light scenes from Indian cities; useful proxy for learning small bright light-source detection under Indian conditions
- Caveat: traffic lights are not streetlights, so this is a **task-adjacent proxy**, not a direct dataset for your target

## 3. Strong non-Indian nighttime proxies

These are the most useful if the goal is to pretrain or benchmark night-scene understanding before adapting to Indian data.

### 3.1 ACDC

- Links:
  - https://acdc.vision.ee.ethz.ch/
  - https://arxiv.org/abs/2104.13395
- Why it matters: one of the standard open nighttime/adverse-condition driving benchmarks
- Relevance: strong proxy for nighttime segmentation, road context, glare, and visibility degradation
- Caveat: not Indian

### 3.2 Dark Zurich

- Links:
  - https://www.trace.ethz.ch/publications/2019/GCMA_UIoU/
  - https://arxiv.org/abs/1908.05765
- Why it matters: classic dataset for day-to-night adaptation and nighttime urban driving perception
- Relevance: strong proxy for nighttime domain adaptation
- Caveat: not Indian

### 3.3 Nighttime Driving

- Link: https://arxiv.org/abs/1810.02575
- Why it matters: widely referenced benchmark in nighttime semantic adaptation work
- Relevance: useful classic night-driving proxy
- Caveat: small labeled nighttime evaluation subset

### 3.4 BDD100K night subset

- Links:
  - https://bdd-data.berkeley.edu/
  - https://github.com/bdd100k/bdd100k
- Why it matters: massive open driving dataset with time-of-day variation, commonly filtered into a night subset
- Relevance: useful for large-scale pretraining and baseline construction
- Caveat: night data is usually used as a filtered subset, not as a dedicated official night benchmark

### 3.5 ExDark

- Link: https://github.com/cs-chan/Exclusively-Dark-Image-Dataset
- Why it matters: standard low-light object-detection dataset
- Relevance: useful for low-light robustness and dark-scene feature learning
- Caveat: not driving-specific

## 4. Practical shortlist for this project

If the target is **phone-deployable night-time streetlight auditing on Indian roads**, the shortest useful shortlist is:

1. `thirdeyelabs/indian-road-dataset`
   - best direct open Indian dataset with explicit night content
2. `IDD-AW`
   - best official Indian low-light proxy
3. `IDD`, `IDD Temporal`, `IDD Multimodal`, `IDD-3D`
   - best Indian context and geometry proxies
4. `Roadscapes`
   - recent Indian monocular proxy with explicit daytime and nighttime coverage
5. `IRD`
   - task-adjacent Indian light-source proxy
6. `ACDC`, `Dark Zurich`, `Nighttime Driving`, `BDD100K night subset`
   - best global night-driving proxies

## 5. Recommendation

Recommended data strategy:

1. Start with `thirdeyelabs/indian-road-dataset` as the main Indian source.
2. Add `IDD-AW` and `Roadscapes` for harder low-light and Indian-context coverage.
3. Use `IRD` only as an auxiliary proxy for bright, small, road-related light sources.
4. Use `ACDC` or `Dark Zurich` for night-domain pretraining or evaluation baselines.
5. Build a **custom curated night streetlight subset** from your own Bengaluru cab videos, because none of the open datasets above directly solve the streetlight-auditing task.

## 6. Source notes

This note mixes:

- fully open datasets with explicit public dataset cards or repos
- official research-access benchmark pages
- dataset papers that point to public project pages or code

That distinction matters. Some entries are clearly open-download datasets, while others are best described as **public research datasets with download instructions or benchmark access**, not strictly permissive open-source software artifacts.
