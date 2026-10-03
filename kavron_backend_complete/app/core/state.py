from __future__ import annotations
from collections import deque
from threading import RLock
from typing import Any

class RuntimeState:
    def __init__(self) -> None:
        self._lock = RLock()
        self.cameras: dict[str, dict[str, Any]] = {}
        self.latest_frames: dict[str, Any] = {}
        self.latest_jpeg: dict[str, bytes] = {}
        self.latest_frame_seq: dict[str, int] = {}
        self.latest_detections: dict[str, list[dict[str, Any]]] = {}
        self.latest_tracks: dict[str, list[dict[str, Any]]] = {}
        self.alerts: deque[dict[str, Any]] = deque(maxlen=500)
        self.incidents: deque[dict[str, Any]] = deque(maxlen=500)
        self.metrics: dict[str, Any] = {"detections_total": 0, "alerts_total": 0}

    def set_camera(self, camera_id: str, value: dict[str, Any]) -> None:
        with self._lock:
            self.cameras[camera_id] = value

    def set_frame(self, camera_id: str, frame: Any) -> None:
        with self._lock:
            self.latest_frames[camera_id] = frame
            self.latest_frame_seq[camera_id] = self.latest_frame_seq.get(camera_id, 0) + 1

    def set_jpeg(self, camera_id: str, jpeg: bytes) -> None:
        with self._lock:
            self.latest_jpeg[camera_id] = jpeg

    def get_stream_snapshot(self, camera_id: str):
        with self._lock:
            return self.latest_jpeg.get(camera_id), self.latest_frame_seq.get(camera_id, 0)

    def set_detections(self, camera_id: str, detections: list[dict[str, Any]]) -> None:
        with self._lock:
            self.latest_detections[camera_id] = detections
            self.metrics["detections_total"] = self.metrics.get("detections_total", 0) + len(detections)

    def set_tracks(self, camera_id: str, tracks: list[dict[str, Any]]) -> None:
        with self._lock:
            self.latest_tracks[camera_id] = tracks

    def add_alert(self, alert: dict[str, Any]) -> None:
        with self._lock:
            self.alerts.appendleft(alert)
            self.metrics["alerts_total"] = self.metrics.get("alerts_total", 0) + 1

    def add_incident(self, incident: dict[str, Any]) -> None:
        with self._lock:
            self.incidents.appendleft(incident)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "cameras": list(self.cameras.values()),
                "detections": {k: list(v) for k, v in self.latest_detections.items()},
                "tracks": {k: list(v) for k, v in self.latest_tracks.items()},
                "alerts": list(self.alerts)[:100],
                "incidents": list(self.incidents)[:100],
                "metrics": dict(self.metrics),
            }
