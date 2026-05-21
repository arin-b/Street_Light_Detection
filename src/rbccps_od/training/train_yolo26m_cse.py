from ultralytics import YOLO
import torch

from rbccps_od.models.yolo_cse import CSEC2f


def replace_c2f_with_cse(model):

    for name, module in model.model.named_children():

        if module.__class__.__name__ == "C2f":

            new_module = CSEC2f(
                module.cv1.conv.in_channels,
                module.cv2.conv.out_channels,
                n=len(module.m)
            )

            model.model._modules[name] = new_module

        else:
            replace_c2f_with_cse(module)


def build_cse_model(weights_path="yolo26m.pt"):

    model = YOLO(weights_path)

    replace_c2f_with_cse(model.model)

    return model

def train():

    model = build_cse_model()

    model.train(
        data="configs/original.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        optimizer="AdamW",
        lr0=1e-3,
        weight_decay=5e-4,
        patience=20,
        workers=8,
        cache=True,
        project="outputs/cse_ablation",
        name="original_images"
    )


if __name__ == "__main__":
    train()