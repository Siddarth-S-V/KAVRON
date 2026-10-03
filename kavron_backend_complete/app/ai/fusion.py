from __future__ import annotations
# from math import max
from app.core.types import Detection

def iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a; bx1, by1, bx2, by2 = b
    x1, y1 = max(ax1, bx1), max(ay1, by1)
    x2, y2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, x2-x1) * max(0.0, y2-y1)
    if inter <= 0: return 0.0
    aa = max(0.0, ax2-ax1) * max(0.0, ay2-ay1)
    bb = max(0.0, bx2-bx1) * max(0.0, by2-by1)
    return inter / (aa + bb - inter + 1e-9)

class DetectionFusion:
    def __init__(self, iou_threshold: float = 0.55): self.iou_threshold = iou_threshold
    def fuse(self, detections: list[Detection]) -> list[Detection]:
        merged: list[Detection] = []
        for det in sorted(detections, key=lambda d: d.confidence, reverse=True):
            match = next((m for m in merged if m.class_name == det.class_name and iou(m.bbox, det.bbox) >= self.iou_threshold), None)
            if match is None:
                merged.append(det)
            else:
                if det.confidence > match.confidence:
                    match.bbox = det.bbox
                    match.confidence = det.confidence
                match.source_models = sorted(set(match.source_models + det.source_models))
        return merged
