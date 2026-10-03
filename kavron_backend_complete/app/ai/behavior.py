from __future__ import annotations

import math
import time
from collections import defaultdict, deque


class BehaviorEngine:
    """Cheap temporal behavior layer built on Stage 2 tracks/pose.

    It deliberately avoids a second heavy neural network. The engine uses a
    short per-track history to confirm events such as loitering, running and
    falling before publishing them.
    """

    def __init__(self, loiter_seconds: float = 12.0, running_speed_px_s: float = 350.0):
        self.loiter_seconds = loiter_seconds
        self.running_speed_px_s = running_speed_px_s
        self.history = defaultdict(lambda: deque(maxlen=60))
        self.cooldowns: dict[tuple[str, str], float] = {}

    def update(self, camera_id: str, track: dict, timestamp: float | None = None, night: bool = False) -> list[dict]:
        now = timestamp or time.time()
        tid = str(track.get("track_id", ""))
        if not tid:
            return []
        bbox = track.get("bbox") or [0, 0, 0, 0]
        center = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        posture = track.get("posture")
        speed = math.hypot(*(track.get("velocity") or [0.0, 0.0]))
        self.history[(camera_id, tid)].append((now, center, posture, speed))
        hist = self.history[(camera_id, tid)]
        events = []

        if posture == "lying" and self._was_recently_upright(hist):
            events.append(self._event(camera_id, track, "FALL_DETECTED", 0.90, now))

        if speed >= self.running_speed_px_s and posture == "standing":
            events.append(self._event(camera_id, track, "SUSPICIOUS_ACTIVITY", min(0.99, 0.65 + speed / 2000.0), now, reason="RAPID_MOVEMENT"))

        # Low-light movement detection requested by the problem statement.
        # This is a conservative temporal rule, not a claim of night-vision accuracy.
        if night and speed >= max(80.0, self.running_speed_px_s * 0.45):
            events.append(self._event(camera_id, track, "NIGHT_MOVEMENT", 0.78, now, reason="LOW_LIGHT_MOVEMENT"))

        if self._loitering(hist, now):
            events.append(self._event(camera_id, track, "SUSPICIOUS_ACTIVITY", 0.82, now, reason="LOITERING"))

        return [e for e in events if self._cool(e["camera_id"], tid, e["event_type"], now)]

    def _was_recently_upright(self, hist) -> bool:
        return any(p in {"standing", "sitting"} for _, _, p, _ in list(hist)[-8:-1])

    def _loitering(self, hist, now: float) -> bool:
        if len(hist) < 8:
            return False
        window = [x for x in hist if now - x[0] <= self.loiter_seconds]
        if len(window) < 8:
            return False
        x0, y0 = window[0][1]
        max_distance = max(math.hypot(x - x0, y - y0) for _, (x, y), _, _ in window)
        avg_speed = sum(v for _, _, _, v in window) / len(window)
        return max_distance < 80.0 and avg_speed < 80.0 and (now - window[0][0]) >= self.loiter_seconds

    def _cool(self, camera_id: str, track_id: str, event_type: str, now: float) -> bool:
        key = (f"{camera_id}:{track_id}", event_type)
        if now - self.cooldowns.get(key, 0.0) < 10.0:
            return False
        self.cooldowns[key] = now
        return True

    @staticmethod
    def _event(camera_id: str, track: dict, event_type: str, confidence: float, timestamp: float, reason: str | None = None) -> dict:
        return {
            "type": "behavior",
            "event_type": event_type,
            "camera_id": camera_id,
            "track_id": track.get("track_id"),
            "class_name": track.get("class_name"),
            "bbox": track.get("bbox"),
            "confidence": round(float(confidence), 4),
            "posture": track.get("posture"),
            "reason": reason,
            "timestamp": timestamp,
        }
