from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stage4", tags=["stage4"])


class LiveCameraToggle(BaseModel):
    enabled: bool
    camera_id: str = Field(default="CAM-LIVE-01", min_length=1, max_length=64)
    source: str = Field(default="0", min_length=1, max_length=255)


@router.get("/status")
def stage4_status(request: Request):
    settings = request.app.state.settings
    registry = request.app.state.camera_registry
    scheduler = request.app.state.scheduler
    model_dir = Path(settings.model_dir)

    specs = {
        "yolo11n": ("yolo11n.pt", "object detection", True),
        "yolo11n_pose": ("yolo11n_pose.pt", "pose/posture", True),
        "yolo26n": ("yolo26n.pt", "object detection candidate", False),
        "yolo26s": ("yolo26s.pt", "object detection candidate", False),
        "yunet": (settings.face_detector_filename, "face detection", True),
        "sface": ("face_recognition_sface_2021dec.onnx", "face embedding", False),
        "sface_int8": ("face_recognition_sface_2021dec_int8bq.onnx", "face embedding CPU candidate", False),
        "lpd_yunet": (settings.plate_detector_filename, "license plate detection", True),
        "paddleocr": (str(Path(settings.paddleocr_model_dir) / "inference.pdiparams"), "ANPR OCR", True),
        "rtmpose": ("rtmpose/rtmpose-s_simcc-coco_pt-aic-coco_420e-256x192-8edcf0d7_20230127.pth", "pose benchmark candidate", False),
    }

    loaded = set(scheduler.registry.loaded()) if scheduler.registry else set()
    active_ids = {settings.general_model, settings.pose_model}
    models = []
    for model_id, (filename, task, active) in specs.items():
        path = Path(filename)
        if not path.is_absolute():
            path = model_dir / filename
        installed = path.exists() and path.stat().st_size > 0
        loaded_name = Path(filename).stem
        models.append({
            "id": model_id,
            "name": model_id,
            "task": task,
            "installed": installed,
            "loaded": loaded_name in loaded or model_id in loaded,
            "active": active and (filename in active_ids or model_id in {"yunet", "lpd_yunet", "paddleocr"}),
            "path": str(path),
            "size_bytes": path.stat().st_size if installed else 0,
        })

    dataset = model_dir.parent / "training" / "dataset.yaml"
    return {
        "stage": 4,
        "models": models,
        "training": {
            "dataset_ready": dataset.exists(),
            "dataset": str(dataset),
            "script": "training/train_yolo_stage4.py",
            "promotion_policy": "benchmark -> validate -> promote",
        },
        "live_camera": {
            "camera_id": "CAM-LIVE-01",
            "available": "CAM-LIVE-01" in registry.items,
        },
    }


@router.post("/live-camera/toggle")
def toggle_live_camera(payload: LiveCameraToggle, request: Request):
    registry = request.app.state.camera_registry
    state = request.app.state.runtime_state
    camera_id = payload.camera_id

    if payload.enabled:
        if camera_id not in registry.items:
            camera = registry.add({
                "camera_id": camera_id,
                "name": "Windows Live Camera",
                "source": payload.source,
                "protocol": "webcam",
                "location": "Local workstation",
                "sector": "LIVE",
                "enabled": True,
            })
            state.set_camera(camera_id, camera.__dict__.copy())
        try:
            started = registry.start(camera_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Live camera could not be registered") from exc
        return {"enabled": True, "camera": started.__dict__}

    if camera_id in registry.items:
        registry.stop(camera_id)
        camera = registry.items[camera_id]
        state.set_camera(camera_id, camera.__dict__.copy())
        return {"enabled": False, "camera": camera.__dict__}

    return {"enabled": False, "camera": None}
