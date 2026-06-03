from ultralytics import YOLO

model = YOLO("/media/arindamb/NewVolume/Street_Light_Detection/runs/detect/outputs/cse_ablation/original-8/weights/best.pt")
image_path = "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/images/val/annotations_LLM\\batch_001\\image_batch\\chatgpt_streetlight_measurement_batch_001_100\\images\\040_seed_streetlight_dataset_valid_train_set_2_frame_35_jpg.rf.syRHiKL9aEiGVyktIEWz.jpg"

results = model.predict(
    source=image_path,
    conf=0.25,
    save=True
)

print(results)