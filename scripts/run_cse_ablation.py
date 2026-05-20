from rbccps_od.training.train_yolo26m_cse import build_cse_model


EXPERIMENTS = [

    {
        "name": "original",
        "data": "configs/original_images.yaml"
    },

    {
        "name": "zerodce",
        "data": "configs/zerodce.yaml"
    },

    {
        "name": "retinex",
        "data": "configs/retinex.yaml"
    },

    {
        "name": "retinex_zerodce",
        "data": "configs/retinex_zerodce.yaml"
    }
]


for exp in EXPERIMENTS:

    model = build_cse_model()

    model.train(
        data=exp["data"],
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        optimizer="AdamW",
        lr0=1e-3,
        project="outputs/cse_ablation",
        name=exp["name"]
    )