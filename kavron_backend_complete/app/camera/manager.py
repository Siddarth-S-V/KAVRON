from __future__ import annotations

import cv2
import threading
import time
from queue import Queue

from app.core.types import CameraState, FramePacket


class CameraWorker:
    def __init__(self, state: CameraState, on_frame, state_callback=None, queue_size=2):
        self.state = state
        self.on_frame = on_frame
        self.state_callback = state_callback
        self.queue = Queue(maxsize=max(1, queue_size))
        self.stop_event = threading.Event()
        self.thread = None
        self.capture = None
        self.frame_id = 0
        self._last_stat = time.time()
        self._frames_stat = 0
        self._last_state_push = 0.0

    def _notify_state(self, force: bool = False) -> None:
        if self.state_callback is None:
            return
        now = time.time()
        if not force and now - self._last_state_push < 0.5:
            return
        self._last_state_push = now
        try:
            self.state_callback(self.state)
        except Exception:
            # Camera state notifications must never stop video capture.
            pass

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name=f"cam-{self.state.camera_id}",
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.capture is not None:
            self.capture.release()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.state.running = False
        self.state.online = False
        self._notify_state(force=True)

    def _open(self):
        source = int(self.state.source) if self.state.source.isdigit() else self.state.source
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            return cap
        cap.release()
        return None

    def _run(self):
        self.state.running = True
        self._notify_state(force=True)
        backoff = 1.0

        while not self.stop_event.is_set():
            self.capture = self._open()
            if self.capture is None:
                self.state.online = False
                self.state.error = "Unable to open stream"
                self.state.reconnects += 1
                self._notify_state(force=True)
                self.stop_event.wait(backoff)
                backoff = min(backoff * 2, 10.0)
                continue

            backoff = 1.0
            self.state.error = None
            self._notify_state(force=True)

            while not self.stop_event.is_set():
                ok, frame = self.capture.read()
                if not ok or frame is None:
                    self.state.online = False
                    self.state.error = "Stream ended or frame read failed"
                    self._notify_state(force=True)
                    break

                h, w = frame.shape[:2]
                self.frame_id += 1
                self._frames_stat += 1
                self.state.touch(w, h)

                now = time.time()
                if now - self._last_stat >= 1.0:
                    self.state.fps = self._frames_stat / max(now - self._last_stat, 1e-6)
                    self._frames_stat = 0
                    self._last_stat = now
                    self._notify_state(force=True)

                packet = FramePacket(
                    self.state.camera_id,
                    self.frame_id,
                    now,
                    frame,
                    w,
                    h,
                )

                # Keep the worker queue bounded and newest-frame oriented.
                try:
                    while not self.queue.empty():
                        self.queue.get_nowait()
                except Exception:
                    pass

                try:
                    self.queue.put_nowait(packet)
                except Exception:
                    pass

                self.on_frame(packet)

            if self.capture is not None:
                self.capture.release()
                self.capture = None

        self.state.running = False
        self.state.online = False
        self._notify_state(force=True)


class CameraManager:
    def __init__(self, on_frame, state_callback=None, queue_size=2):
        self.workers = {}
        self.on_frame = on_frame
        self.state_callback = state_callback
        self.queue_size = max(1, queue_size)
        self.lock = threading.Lock()

    def add(self, state: CameraState):
        with self.lock:
            if state.camera_id in self.workers:
                self.remove(state.camera_id)
            self.workers[state.camera_id] = CameraWorker(
                state,
                self.on_frame,
                self.state_callback,
                self.queue_size,
            )
        return state

    def remove(self, camera_id):
        with self.lock:
            worker = self.workers.pop(camera_id, None)
        if worker:
            worker.stop()

    def start(self, camera_id):
        worker = self.workers.get(camera_id)
        if worker is None:
            raise KeyError(camera_id)
        worker.start()
        return worker.state

    def stop(self, camera_id):
        worker = self.workers.get(camera_id)
        if worker is None:
            raise KeyError(camera_id)
        worker.stop()
        return worker.state

    def start_all(self):
        for worker in list(self.workers.values()):
            worker.start()

    def stop_all(self):
        for worker in list(self.workers.values()):
            worker.stop()

    def get_frame(self, camera_id):
        worker = self.workers.get(camera_id)
        return None if worker is None else getattr(worker, "capture", None)
