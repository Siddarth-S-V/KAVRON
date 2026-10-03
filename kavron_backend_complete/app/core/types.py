from __future__ import annotations
from dataclasses import dataclass, field
from time import time
from typing import Any

@dataclass
class FramePacket:
    camera_id: str
    frame_id: int
    timestamp: float
    frame: Any
    width: int
    height: int

@dataclass
class Detection:
    camera_id: str
    frame_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]
    timestamp: float
    source_models: list[str] = field(default_factory=list)
    track_id: str | None = None
    pose: list[list[float]] | None = None
    posture: str | None = None
    face: dict | None = None
    plate: dict | None = None
    behavior_flags: list[str] = field(default_factory=list)

@dataclass
class CameraState:
    camera_id: str
    name: str
    source: str
    protocol: str
    location: str = ""
    sector: str = ""
    latitude: float | None = None
    longitude: float | None = None
    location_accuracy_m: float | None = None
    location_source: str = "manual"
    running: bool = False
    online: bool = False
    fps: float = 0.0
    width: int = 0
    height: int = 0
    last_frame_at: float | None = None
    frames_seen: int = 0
    reconnects: int = 0
    inference_fps: float = 0.0
    error: str | None = None

    def touch(self, width: int, height: int) -> None:
        self.online = True
        self.width = width
        self.height = height
        self.last_frame_at = time()
        self.frames_seen += 1

