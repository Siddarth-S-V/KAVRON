from __future__ import annotations

import time
from pathlib import Path
from threading import Lock
from typing import Any
from itertools import product

import cv2
import numpy as np


class FaceSpecialist:
    """YuNet face detection + optional SFace embedding."""
    def __init__(self, detector_path: str, recognizer_path: str | None = None, confidence: float = 0.70) -> None:
        self.detector_path = detector_path
        self.recognizer_path = recognizer_path
        self.confidence = confidence
        self._detector = None
        self._recognizer = None
        self._lock = Lock()

    def _load(self) -> None:
        if self._detector is None:
            if not Path(self.detector_path).exists():
                raise FileNotFoundError(self.detector_path)
            self._detector = cv2.FaceDetectorYN.create(self.detector_path, "", (320, 320), self.confidence, 0.3, 5000)
        if self._recognizer is None and self.recognizer_path and Path(self.recognizer_path).exists():
            self._recognizer = cv2.FaceRecognizerSF.create(self.recognizer_path, "")

    def detect(self, image: np.ndarray) -> list[dict[str, Any]]:
        with self._lock:
            self._load()
            h, w = image.shape[:2]
            self._detector.setInputSize((w, h))
            _, faces = self._detector.detect(image)
            if faces is None:
                return []
            output = []
            for row in faces:
                x, y, fw, fh = [float(v) for v in row[:4]]
                score = float(row[14]) if len(row) > 14 else 0.0
                if score < self.confidence:
                    continue
                landmarks = [[float(row[4 + 2 * i]), float(row[5 + 2 * i])] for i in range(5)]
                output.append({"bbox": [x, y, x + fw, y + fh], "confidence": score, "landmarks": landmarks})
            return output

    def embedding(self, image: np.ndarray, face: dict[str, Any]) -> list[float] | None:
        with self._lock:
            self._load()
            if self._recognizer is None:
                return None
            landmarks = face.get("landmarks")
            if not landmarks or len(landmarks) != 5:
                return None
            x1, y1, x2, y2 = face["bbox"]
            row = np.asarray([x1, y1, x2 - x1, y2 - y1, *[v for point in landmarks for v in point], face.get("confidence", 0.0)], dtype=np.float32)
            feature = self._recognizer.feature(self._recognizer.alignCrop(image, row))
            return np.asarray(feature).reshape(-1).astype(float).tolist()


class LPDYuNet:
    """OpenCV Zoo LPD-YuNet decoder."""
    def __init__(self, model_path: str, confidence: float = 0.45, nms_threshold: float = 0.30) -> None:
        self.model_path = model_path
        self.confidence = confidence
        self.nms_threshold = nms_threshold
        self.input_size = np.array([320, 240], dtype=np.float32)
        self._net = None
        self._lock = Lock()
        self._priors = self._make_priors()

    def _make_priors(self):
        w, h = self.input_size
        feature_map_2 = [int(int((h + 1) / 2) / 2), int(int((w + 1) / 2) / 2)]
        feature_maps = [feature_map_2]
        for _ in range(3):
            feature_maps.append([max(1, int(feature_maps[-1][0] / 2)), max(1, int(feature_maps[-1][1] / 2))])
        min_sizes = [[10, 16, 24], [32, 48], [64, 96], [128, 192, 256]]
        steps = [8, 16, 32, 64]
        priors = []
        for k, f in enumerate(feature_maps):
            for i, j in product(range(f[0]), range(f[1])):
                for size in min_sizes[k]:
                    priors.append([(j + 0.5) * steps[k] / w, (i + 0.5) * steps[k] / h, size / w, size / h])
        return np.asarray(priors, dtype=np.float32)

    def _load(self):
        if self._net is None:
            if not Path(self.model_path).exists():
                raise FileNotFoundError(self.model_path)
            self._net = cv2.dnn.readNet(self.model_path)

    def detect(self, vehicle_crop: np.ndarray) -> list[dict[str, Any]]:
        with self._lock:
            self._load()
            resized = cv2.resize(vehicle_crop, (320, 240), interpolation=cv2.INTER_LINEAR)
            self._net.setInput(cv2.dnn.blobFromImage(resized))
            loc, conf, iou = self._net.forward(["loc", "conf", "iou"])
            loc = loc.reshape(-1, 14)
            conf = conf.reshape(-1, 2)
            iou = np.clip(iou.reshape(-1), 0.0, 1.0)
            scores = np.sqrt(np.maximum(0.0, conf[:, 1] * iou))
            n = min(len(loc), len(self._priors))
            loc, scores, priors = loc[:n], scores[:n], self._priors[:n]
            scale = np.asarray([320.0, 240.0], dtype=np.float32)
            var0 = 0.1
            x1y1 = (priors[:, 0:2] + loc[:, 4:6] * var0 * priors[:, 2:4]) * scale
            x2y2 = (priors[:, 0:2] + loc[:, 6:8] * var0 * priors[:, 2:4]) * scale
            boxes = np.concatenate([x1y1, x2y2], axis=1)
            keep = np.where(scores >= self.confidence)[0]
            if not len(keep):
                return []
            boxes_keep, scores_keep = boxes[keep].tolist(), scores[keep].tolist()
            idxs = cv2.dnn.NMSBoxes(boxes_keep, scores_keep, self.confidence, self.nms_threshold)
            if len(idxs) == 0:
                return []
            h, w = vehicle_crop.shape[:2]
            sx, sy = w / 320.0, h / 240.0
            return [{"bbox": [max(0.0, b[0] * sx), max(0.0, b[1] * sy), min(float(w), b[2] * sx), min(float(h), b[3] * sy)], "confidence": float(scores_keep[int(i)])} for i in np.asarray(idxs).reshape(-1) for b in [boxes_keep[int(i)]]]


class OCRSpecialist:
    """PaddleOCR local model first, then network/default model, then EasyOCR."""
    def __init__(self, languages: list[str] | None = None, model_dir: str | None = None) -> None:
        self.languages = languages or ["en"]
        self.model_dir = model_dir
        self._engine = None
        self._kind = None
        self._lock = Lock()

    def _load(self):
        if self._engine is not None:
            return
        from pathlib import Path
        local = Path(self.model_dir) if self.model_dir else None
        try:
            from paddleocr import PaddleOCR
            if local and (local / "inference.pdiparams").exists():
                attempts = [
                    {"text_recognition_model_dir": str(local), "lang": "en", "use_doc_orientation_classify": False, "use_doc_unwarping": False, "use_textline_orientation": False},
                    {"rec_model_dir": str(local), "lang": "en", "use_angle_cls": False, "use_doc_orientation_classify": False, "use_doc_unwarping": False, "use_textline_orientation": False},
                ]
                for kwargs in attempts:
                    try:
                        self._engine = PaddleOCR(**kwargs)
                        self._kind = "paddle"
                        return
                    except TypeError:
                        continue
            self._engine = PaddleOCR(lang="en", use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)
            self._kind = "paddle"
            return
        except Exception:
            pass
        try:
            import easyocr
            self._engine = easyocr.Reader(self.languages, gpu=False, verbose=False)
            self._kind = "easyocr"
            return
        except Exception as exc:
            raise RuntimeError("Install paddleocr or easyocr for ANPR OCR") from exc

    @staticmethod
    def _clean(text: str) -> str:
        return "".join(ch for ch in text.upper() if ch.isalnum())

    def read(self, crop: np.ndarray) -> dict[str, Any] | None:
        with self._lock:
            self._load()
            if crop is None or crop.size == 0:
                return None
            up = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 7, 45, 45)
            texts: list[tuple[str, float]] = []
            for image in (up, gray):
                if self._kind == "paddle":
                    for page in self._engine.predict(image):
                        data = page.json() if hasattr(page, "json") else {}
                        payload = data.get("res", data) if isinstance(data, dict) else {}
                        rec_texts = payload.get("rec_texts", []) if isinstance(payload, dict) else []
                        rec_scores = payload.get("rec_scores", []) if isinstance(payload, dict) else []
                        for i, txt in enumerate(rec_texts):
                            score = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                            texts.append((self._clean(str(txt)), score))
                else:
                    for txt, score in self._engine.readtext(image, detail=1, paragraph=False):
                        texts.append((self._clean(str(txt)), float(score)))
            texts = [(t, s) for t, s in texts if 4 <= len(t) <= 12]
            if not texts:
                return None
            text, score = max(texts, key=lambda x: (x[1], len(x[0])))
            return {"text": text, "confidence": score, "timestamp": time.time()}
