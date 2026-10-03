from __future__ import annotations

from pathlib import Path
import cv2
from fastapi import APIRouter, Request

router = APIRouter(prefix="/stage5", tags=["stage5"])

CAPABILITIES = [
    ("Human detection and tracking", ["yolo11n", "tracking"]),
    ("Vehicle detection and classification", ["yolo11n"]),
    ("Face detection", ["yunet"]),
    ("Automatic Number Plate Recognition (ANPR)", ["lpd_yunet", "paddleocr"]),
    ("Virtual fence intrusion detection", ["virtual_fence"]),
    ("Suspicious activity detection", ["behavior"]),
    ("Night-time movement detection", ["behavior_night"]),
    ("Real-time alert generation and event logging", ["event_bus", "anomaly_api"]),
    ("Real maps and camera geolocation", ["osm", "geolocation"]),
]

def _model_file(model_dir: Path, name: str) -> Path:
    mapping = {
        "yolo11n": "yolo11n.pt",
        "tracking": "yolo11n.pt",
        "yunet": "face_detection_yunet_2023mar.onnx",
        "lpd_yunet": "license_plate_detection_lpd_yunet_2023mar.onnx",
        "paddleocr": "paddleocr/en_PP-OCRv5_mobile_rec/inference.pdiparams",
    }
    return model_dir / mapping[name]

@router.get("/status")
def stage5_status(request: Request):
    settings = request.app.state.settings
    model_dir = Path(settings.model_dir)
    models = {}
    for key in ["yolo11n", "yolo26n", "yolo26s", "yunet", "sface", "sface_int8", "lpd_yunet", "paddleocr", "rtmpose", "yolo11n_pose"]:
        mapping = {
            "yolo11n":"yolo11n.pt", "yolo26n":"yolo26n.pt", "yolo26s":"yolo26s.pt",
            "yunet":"face_detection_yunet_2023mar.onnx",
            "sface":"face_recognition_sface_2021dec.onnx",
            "sface_int8":"face_recognition_sface_2021dec_int8bq.onnx",
            "lpd_yunet":"license_plate_detection_lpd_yunet_2023mar.onnx",
            "paddleocr":"paddleocr/en_PP-OCRv5_mobile_rec/inference.pdiparams",
            "rtmpose":"rtmpose/rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth",
            "yolo11n_pose":"yolo11n_pose.pt",
        }
        p = model_dir / mapping[key]
        item = {"installed": p.exists() and p.stat().st_size > 0, "size_bytes": p.stat().st_size if p.exists() else 0}
        if p.suffix == ".onnx" and item["installed"]:
            try:
                cv2.dnn.readNetFromONNX(str(p))
                item["runtime_valid"] = True
            except Exception as exc:
                item["runtime_valid"] = False
                item["runtime_error"] = str(exc)
        else:
            item["runtime_valid"] = None
        models[key] = item

    return {
        "stage": 5,
        "problem_statement_id": "26187",
        "problem_statement_title": "AI-Based Intelligent Video Analytics Platform for Border Surveillance using existing CCTV Infrastructure",
        "capabilities": [
            {"name": name, "implemented": True, "components": components}
            for name, components in CAPABILITIES
        ],
        "models": models,
        "fine_tuning": {
             "labels_present": any(
            any((model_dir.parent / "training" / "dataset" / sub).glob("*"))
            for sub in ["images/train", "labels/train"]
        ),
            "status": "labels_required_for_true_supervised_finetuning",
        },
        "map": {
            "provider": "OpenStreetMap",
            "geolocation": "browser permission based",
            "camera_coordinates_persisted": True,
        },
    }
