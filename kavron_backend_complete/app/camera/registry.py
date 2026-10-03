from __future__ import annotations

from app.core.types import CameraState
from app.camera.manager import CameraManager


class CameraRegistry:
    def __init__(self, on_frame, state_callback=None, queue_size=2):
        self.items = {}
        self.manager = CameraManager(
            on_frame,
            state_callback,
            queue_size,
        )

    def add(self, camera: dict):
        state = CameraState(
            camera["camera_id"],
            camera.get("name", camera["camera_id"]),
            str(camera["source"]),
            camera.get("protocol", "file"),
            camera.get("location", ""),
            camera.get("sector", ""),
            camera.get("latitude"),
            camera.get("longitude"),
            camera.get("location_accuracy_m"),
            camera.get("location_source", "manual"),
        )
        self.items[state.camera_id] = state
        self.manager.add(state)
        return state

    def remove(self, camera_id):
        self.manager.remove(camera_id)
        return self.items.pop(camera_id, None)

    def start(self, camera_id):
        return self.manager.start(camera_id)

    def stop(self, camera_id):
        return self.manager.stop(camera_id)

    def stop_all(self):
        self.manager.stop_all()
