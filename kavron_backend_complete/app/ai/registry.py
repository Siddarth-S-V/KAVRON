from __future__ import annotations
from pathlib import Path
from threading import Lock
from typing import Any

class ModelRegistry:
    """Thread-safe lazy model registry with per-model inference locks.

    Ultralytics models are expensive to load and are not guaranteed to be safe
    for concurrent forward passes. We therefore load once and serialize only
    the actual forward pass per model, while allowing camera capture, tracking,
    pose post-processing and different model families to progress concurrently.
    """
    def __init__(self, model_dir: str, device: str = "cpu") -> None:
        self.model_dir = Path(model_dir)
        self.device = device
        self._models: dict[str, Any] = {}
        self._meta: dict[str, dict] = {}
        self._locks: dict[str, Lock] = {}
        self._lock = Lock()

    def discover(self) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for path in sorted(self.model_dir.glob("*.pt")):
            result[path.stem] = {"path": str(path), "loaded": path.stem in self._models}
        return result

    def load(self, model_id: str, filename: str):
        path = self.model_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        with self._lock:
            if model_id in self._models:
                return self._models[model_id]
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError("Ultralytics is not installed. Run: pip install ultralytics") from exc
            model = YOLO(str(path))
            try:
                model.to(self.device)
            except Exception:
                pass
            names = getattr(model, "names", None) or getattr(getattr(model, "model", None), "names", {})
            task = getattr(model, "task", None) or getattr(getattr(model, "model", None), "task", "unknown")
            self._models[model_id] = model
            self._locks[model_id] = Lock()
            self._meta[model_id] = {
                "model_id": model_id, "filename": filename, "path": str(path),
                "task": str(task), "classes": names,
            }
            return model

    def get(self, model_id: str):
        return self._models.get(model_id)

    def inference_lock(self, model_id: str) -> Lock:
        with self._lock:
            return self._locks.setdefault(model_id, Lock())

    def metadata(self, model_id: str | None = None):
        return self._meta if model_id is None else self._meta.get(model_id)

    def loaded(self) -> list[str]:
        with self._lock:
            return list(self._models)
