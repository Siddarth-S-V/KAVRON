from __future__ import annotations
import time
from typing import Any
from app.core.types import Detection

class YOLODetector:
    def __init__(self, registry, model_id: str, filename: str, conf: float, iou: float, device: str) -> None:
        self.registry = registry
        self.model_id = model_id
        self.filename = filename
        self.conf = conf
        self.iou = iou
        self.device = device

    def ensure_loaded(self):
        return self.registry.load(self.model_id, self.filename)

    def predict(self, frame, camera_id: str, frame_id: int, timestamp: float | None = None) -> list[Detection]:
        ts = timestamp or time.time()
        model = self.ensure_loaded()
        # Serialize a model's forward pass, not the rest of the pipeline.
        with self.registry.inference_lock(self.model_id):
            results = model.predict(
                source=frame, conf=self.conf, iou=self.iou, verbose=False,
                device=self.device, stream=False, max_det=100,
            )
        output: list[Detection] = []
        if not results:
            return output
        result = results[0]
        names = result.names if hasattr(result, "names") else {}
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return output
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].detach().cpu().tolist()
            conf = float(boxes.conf[i].detach().cpu().item())
            cls_id = int(boxes.cls[i].detach().cpu().item())
            output.append(Detection(
                camera_id, frame_id, cls_id, str(names.get(cls_id, cls_id)), conf,
                tuple(map(float, xyxy)), ts, [self.model_id]
            ))
        return output

class PoseDetector(YOLODetector):
    """Pose-specialist adapter. Returns the same detection contract plus keypoints."""
    def predict(self, frame, camera_id: str, frame_id: int, timestamp: float | None = None) -> list[Detection]:
        ts = timestamp or time.time()
        model = self.ensure_loaded()
        with self.registry.inference_lock(self.model_id):
            results = model.predict(
                source=frame, conf=self.conf, iou=self.iou, verbose=False,
                device=self.device, stream=False, max_det=64,
            )
        output: list[Detection] = []
        if not results:
            return output
        result = results[0]
        names = result.names if hasattr(result, "names") else {}
        boxes = getattr(result, "boxes", None)
        keypoints = getattr(result, "keypoints", None)
        if boxes is None:
            return output
        xy = getattr(keypoints, "xy", None) if keypoints is not None else None
        kc = getattr(keypoints, "conf", None) if keypoints is not None else None
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].detach().cpu().tolist()
            conf = float(boxes.conf[i].detach().cpu().item())
            cls_id = int(boxes.cls[i].detach().cpu().item())
            points: list[list[float]] = []
            if xy is not None and i < len(xy):
                coords = xy[i].detach().cpu().tolist()
                scores = kc[i].detach().cpu().tolist() if kc is not None and i < len(kc) else [1.0] * len(coords)
                points = [[float(pt[0]), float(pt[1]), float(scores[j])] for j, pt in enumerate(coords)]
            d = Detection(camera_id, frame_id, cls_id, str(names.get(cls_id, "person")), conf, tuple(map(float, xyxy)), ts, [self.model_id])
            d.pose = points or None
            output.append(d)
        return output

class ModelDetector:
    """Small adapter for on-demand specialist YOLO models."""
    def __init__(self, registry, specs: dict[str, dict], conf: float, iou: float, device: str) -> None:
        self.registry = registry; self.specs = specs; self.conf = conf; self.iou = iou; self.device = device

    def predict(self, model_id: str, frame, camera_id: str, frame_id: int, ts: float) -> list[Detection]:
        spec = self.specs[model_id]
        return YOLODetector(self.registry, model_id, spec["filename"], self.conf, self.iou, self.device).predict(frame, camera_id, frame_id, ts)
