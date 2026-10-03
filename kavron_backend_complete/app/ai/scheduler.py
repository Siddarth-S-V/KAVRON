from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
from pathlib import Path

from app.ai.behavior import BehaviorEngine
from app.ai.detector import YOLODetector, ModelDetector, PoseDetector
from app.ai.fusion import DetectionFusion
from app.ai.model_manager import ModelAssetManager
from app.ai.specialists import FaceSpecialist, LPDYuNet, OCRSpecialist
from app.ai.tracker import SimpleTracker


class InferenceScheduler:
    """Fair bounded scheduler plus Stage 3 multimodel fusion.

    Heavy detection is kept at the Stage 2 cadence. Face/plate/OCR work is
    ROI-based and throttled per camera, so specialist models never run across
    the entire frame at camera FPS.
    """

    VEHICLES = {"car", "truck", "bus", "motorcycle", "bicycle", "vehicle"}
    PERSONS = {"person", "human"}

    def __init__(self, settings, camera_registry, state, on_event):
        self.settings = settings
        self.camera_registry = camera_registry
        self.state = state
        self.on_event = on_event
        self.stop_event = threading.Event()
        self.workers = []
        try:
            self.specialist_pool.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self.registry = None
        self.fusion = DetectionFusion(settings.iou)
        self.simple_trackers = defaultdict(lambda: SimpleTracker(settings.tracker_max_distance, settings.tracker_max_age, settings.bbox_smoothing, settings.pose_smoothing))
        self.behavior = BehaviorEngine(settings.behavior_loiter_seconds, settings.behavior_running_speed_px_s)
        self.asset_manager = ModelAssetManager(settings.model_dir)
        self.face_specialists: dict[str, FaceSpecialist] = {}
        self.plate_specialists: dict[str, LPDYuNet] = {}
        self.ocr: OCRSpecialist | None = None
        self.specialist_pool = ThreadPoolExecutor(max_workers=max(1, int(settings.specialist_workers)), thread_name_prefix="kavron-specialist")
        self.last_infer = {}
        self.last_pose = {}
        self.last_face = {}
        self.last_anpr = {}
        self.plate_history = defaultdict(lambda: deque(maxlen=8))
        self._pending_by_camera = {}
        self._condition = threading.Condition()
        self._rr = deque()
        self.metrics = {
            "submitted": 0, "dropped": 0, "processed": 0, "pose_runs": 0,
            "face_runs": 0, "face_detections": 0, "plate_runs": 0,
            "ocr_runs": 0, "behavior_events": 0, "night_motion_events": 0, "avg_latency_ms": 0.0,
        }
        self.detectors: dict[str, YOLODetector] = {}
        self.pose_detectors: dict[str, PoseDetector] = {}
        self.model_detectors: dict[str, ModelDetector] = {}
        self.model_specs = {
            "general": {"filename": settings.general_model, "mode": "always"},
            "person": {"filename": settings.person_model, "mode": "conditional"},
            "pose": {"filename": settings.pose_model, "mode": "conditional"},
            "specialist": {"filename": settings.specialist_model, "mode": "conditional"},
            "pose_alt": {"filename": settings.pose_alt_model, "mode": "on_demand"},
        }

    def attach_registry(self, registry):
        self.registry = registry

    def submit(self, packet):
        now = time.time()
        interval = 1.0 / max(self.settings.ai_fps, 0.1)
        last = self.last_infer.get(packet.camera_id, 0.0)
        if now - last < interval:
            self.metrics["dropped"] += 1
            return False
        self.last_infer[packet.camera_id] = now
        with self._condition:
            replacing = packet.camera_id in self._pending_by_camera
            if replacing:
                self.metrics["dropped"] += 1
            self._pending_by_camera[packet.camera_id] = packet
            if not replacing and packet.camera_id not in self._rr:
                self._rr.append(packet.camera_id)
            self.metrics["submitted"] += 1
            self._condition.notify()
        return True

    def start(self):
        self.stop_event.clear()
        n = max(1, int(self.settings.inference_workers))
        self.workers = [threading.Thread(target=self._run, name=f"kavron-inference-{i+1}", daemon=True) for i in range(n)]
        for worker in self.workers:
            worker.start()

    def stop(self):
        self.stop_event.set()
        with self._condition:
            self._condition.notify_all()
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=3)
        self.workers = []

    def _next_packet(self):
        with self._condition:
            while not self.stop_event.is_set() and not self._pending_by_camera:
                self._condition.wait(timeout=0.25)
            if self.stop_event.is_set():
                return None
            while self._rr:
                cid = self._rr.popleft()
                packet = self._pending_by_camera.pop(cid, None)
                if packet is not None:
                    return packet
            cid, packet = next(iter(self._pending_by_camera.items()))
            self._pending_by_camera.pop(cid, None)
            return packet

    def _run(self):
        while not self.stop_event.is_set():
            packet = self._next_packet()
            if packet is None:
                continue
            started = time.perf_counter()
            try:
                self.process(packet)
            except Exception as exc:
                self.on_event({"type": "ai_error", "camera_id": packet.camera_id, "error": str(exc), "timestamp": time.time()})
            finally:
                latency = (time.perf_counter() - started) * 1000
                self.metrics["processed"] += 1
                self.metrics["avg_latency_ms"] = 0.9 * self.metrics["avg_latency_ms"] + 0.1 * latency

    def _face(self, camera_id: str):
        if camera_id not in self.face_specialists:
            detector = self.settings.model_dir and (Path(self.settings.model_dir) / self.settings.face_detector_filename)
            recognizer = self.asset_manager.path("face_recognizer")
            self.face_specialists[camera_id] = FaceSpecialist(str(detector), str(recognizer) if Path(recognizer).exists() else None, 0.70)
        return self.face_specialists[camera_id]

    def _plate(self, camera_id: str):
        if camera_id not in self.plate_specialists:
            plate_path = Path(self.settings.model_dir) / self.settings.plate_detector_filename
            self.plate_specialists[camera_id] = LPDYuNet(str(plate_path), self.settings.anpr_confidence)
        return self.plate_specialists[camera_id]

    def _run_specialists(self, packet, detections):
        if not self.settings.stage3_enabled:
            return
        frame_id = packet.frame_id
        cid = packet.camera_id

        if frame_id - self.last_face.get(cid, -10**9) >= max(1, self.settings.face_interval):
            persons = [d for d in detections if d.class_name.lower() in self.PERSONS]
            if persons and self.asset_manager.path("face_detector").exists():
                specialist = self._face(cid)
                self.last_face[cid] = frame_id
                for person in persons[:12]:
                    crop, offset = _crop(packet.frame, person.bbox, margin=0.15)
                    if crop is None:
                        continue
                    try:
                        faces = specialist.detect(crop)
                    except Exception as exc:
                        self.on_event({"type": "ai_warning", "camera_id": cid, "warning": f"face: {exc}", "timestamp": time.time()})
                        continue
                    if not faces:
                        continue
                    best = max(faces, key=lambda x: x["confidence"])
                    best["bbox"] = _offset_bbox(best["bbox"], offset)
                    if self.settings.enable_face_embedding:
                        try:
                            best["embedding"] = specialist.embedding(crop, faces[faces.index(max(faces, key=lambda x: x["confidence"]))])
                        except Exception:
                            best["embedding"] = None
                    person.face = best
                    self.metrics["face_detections"] += 1
                self.metrics["face_runs"] += 1

        if frame_id - self.last_anpr.get(cid, -10**9) >= max(1, self.settings.anpr_interval):
            vehicles = [d for d in detections if d.class_name.lower() in self.VEHICLES]
            if vehicles and self.asset_manager.path("plate_detector").exists():
                plate_detector = self._plate(cid)
                self.last_anpr[cid] = frame_id
                self.metrics["plate_runs"] += 1
                for vehicle in vehicles[:8]:
                    crop, _ = _crop(packet.frame, vehicle.bbox, margin=0.05)
                    if crop is None:
                        continue
                    try:
                        plates = plate_detector.detect(crop)
                    except Exception as exc:
                        self.on_event({"type": "ai_warning", "camera_id": cid, "warning": f"plate detector: {exc}", "timestamp": time.time()})
                        continue
                    if not plates:
                        continue
                    plate = max(plates, key=lambda x: x["confidence"])
                    px1, py1, px2, py2 = [int(round(v)) for v in plate["bbox"]]
                    plate_crop = crop[max(0, py1):min(crop.shape[0], py2), max(0, px1):min(crop.shape[1], px2)]
                    if plate_crop.size == 0:
                        continue
                    if self.ocr is None:
                        self.ocr = OCRSpecialist(model_dir=self.settings.paddleocr_model_dir)
                    try:
                        self.metrics["ocr_runs"] += 1
                        text = self.ocr.read(plate_crop)
                    except Exception as exc:
                        self.on_event({"type": "ai_warning", "camera_id": cid, "warning": f"ocr: {exc}", "timestamp": time.time()})
                        text = None
                    if text and text.get("text"):
                        tid = vehicle.track_id or f"vehicle-{vehicle.frame_id}"
                        self.plate_history[(cid, tid)].append(text)
                        winner = _vote_plate(self.plate_history[(cid, tid)])
                        vehicle.plate = {"text": winner[0], "confidence": winner[1], "bbox": _offset_bbox(plate["bbox"], _crop(packet.frame, vehicle.bbox, margin=0.05)[1])}

    def _general_detector(self):
        if "general" not in self.detectors:
            spec = self.model_specs["general"]
            self.detectors["general"] = YOLODetector(self.registry, "general", spec["filename"], self.settings.confidence, self.settings.iou, self.settings.device)
        return self.detectors["general"]

    def _pose_detector(self):
        if "pose" not in self.pose_detectors:
            spec = self.model_specs["pose"]
            self.pose_detectors["pose"] = PoseDetector(self.registry, "pose", spec["filename"], self.settings.confidence, self.settings.iou, self.settings.device)
        return self.pose_detectors["pose"]

    def _model_detector(self, model_id: str):
        if model_id not in self.model_detectors:
            self.model_detectors[model_id] = ModelDetector(self.registry, self.model_specs, self.settings.confidence, self.settings.iou, self.settings.device)
        return self.model_detectors[model_id]

    def process(self, packet):
        if self.registry is None:
            return
        general = self._general_detector()
        detections = general.predict(packet.frame, packet.camera_id, packet.frame_id, packet.timestamp)
        persons = [d for d in detections if d.class_name.lower() in self.PERSONS]

        if self.settings.enable_person_specialist and persons and self.model_specs["person"]["filename"]:
            try:
                detections += self._model_detector("person").predict("person", packet.frame, packet.camera_id, packet.frame_id, packet.timestamp)
            except Exception as exc:
                self.on_event({"type": "ai_warning", "camera_id": packet.camera_id, "warning": f"person specialist: {exc}", "timestamp": time.time()})

        pose_interval = max(1, int(self.settings.pose_interval))
        last_pose = self.last_pose.get(packet.camera_id, 0)
        pose_dets = []
        if persons and packet.frame_id - last_pose >= pose_interval:
            try:
                pose = self._pose_detector()
                pose_dets = pose.predict(packet.frame, packet.camera_id, packet.frame_id, packet.timestamp)
                self.last_pose[packet.camera_id] = packet.frame_id
                self.metrics["pose_runs"] += 1
            except Exception as exc:
                self.on_event({"type": "ai_warning", "camera_id": packet.camera_id, "warning": f"pose: {exc}", "timestamp": time.time()})

        fused = self.fusion.fuse(detections)
        self._attach_pose(fused, pose_dets)
        tracks = self.simple_trackers[packet.camera_id].update(fused)

        # Face and ANPR operate on disjoint ROIs. Run them in a bounded pool
        # and never create more workers than configured. This overlaps I/O/native
        # work while keeping CPU oversubscription bounded.
        if self.settings.stage3_enabled:
            jobs = []
            jobs.append(self.specialist_pool.submit(self._run_specialists, packet, fused))
            for job in jobs:
                job.result()
        track_payload = [_track_dict(t) for t in tracks]
        det_payload = [_det_dict(d, packet.width, packet.height) for d in fused]

        # Cheap low-light estimate once per processed frame. This powers the
        # problem-statement's night-time movement rule without another model.
        try:
            import cv2
            night_brightness = float(cv2.cvtColor(packet.frame, cv2.COLOR_BGR2GRAY).mean())
            is_night = night_brightness < 65.0
        except Exception:
            is_night = False

        # Build behavior state from the final track payload and publish only
        # confirmed temporal events, avoiding frame-by-frame alert spam.
        for track in track_payload:
            behavior_events = self.behavior.update(packet.camera_id, track, packet.timestamp, night=is_night)
            if behavior_events:
                track["behavior_flags"] = [e["event_type"] for e in behavior_events]
                self.metrics["behavior_events"] += len(behavior_events)
                self.metrics["night_motion_events"] += sum(1 for e in behavior_events if e.get("event_type") == "NIGHT_MOVEMENT")
                for event in behavior_events:
                    self.on_event(event)

        # Mirror specialist data from detections into the matching track.
        for det in det_payload:
            for track in track_payload:
                if det.get("track_id") == track.get("track_id"):
                    track["face"] = det.get("face")
                    track["plate"] = det.get("plate")
                    track["pose"] = det.get("pose")
                    track["keypoints"] = det.get("pose")
                    track["posture"] = det.get("posture")
                    break

        self.state.set_detections(packet.camera_id, det_payload)
        self.state.set_tracks(packet.camera_id, track_payload)
        self.on_event({"type": "detections", "camera_id": packet.camera_id, "frame_id": packet.frame_id, "timestamp": packet.timestamp, "detections": det_payload, "tracks": track_payload})
        for d in det_payload:
            self.on_event({"type": "detection", "camera_id": packet.camera_id, **d})

    @staticmethod
    def _attach_pose(detections, poses):
        if not poses:
            return
        persons = [d for d in detections if d.class_name.lower() in {"person", "human"}]
        used = set()
        for p in poses:
            best, best_score = None, 0.0
            for idx, d in enumerate(persons):
                if idx in used:
                    continue
                score = _iou(p.bbox, d.bbox)
                if score > best_score:
                    best_score, best = score, idx
            if best is not None and best_score >= 0.15:
                persons[best].pose = p.pose
                persons[best].posture = _posture_from_pose(p.pose, persons[best].bbox)
                persons[best].source_models = list(dict.fromkeys(persons[best].source_models + p.source_models))
                used.add(best)


def _posture_from_pose(points, bbox):
    from app.ai.tracker import classify_posture
    return classify_posture(points, bbox)


def _crop(frame, bbox, margin=0.0):
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = [float(v) for v in bbox]
    bw, bh = x2 - x1, y2 - y1
    x1, y1 = max(0, int(x1 - bw * margin)), max(0, int(y1 - bh * margin))
    x2, y2 = min(w, int(x2 + bw * margin)), min(h, int(y2 + bh * margin))
    if x2 <= x1 or y2 <= y1:
        return None, (0, 0)
    return frame[y1:y2, x1:x2], (x1, y1)


def _offset_bbox(bbox, offset):
    ox, oy = offset
    return [float(bbox[0] + ox), float(bbox[1] + oy), float(bbox[2] + ox), float(bbox[3] + oy)]


def _vote_plate(history):
    groups = defaultdict(list)
    for item in history:
        groups[item["text"]].append(float(item.get("confidence", 0.0)))
    text, scores = max(groups.items(), key=lambda item: (len(item[1]), sum(item[1]) / len(item[1])))
    return text, round(sum(scores) / len(scores), 4)


def _iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    aa = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    bb = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    return inter / max(1e-6, aa + bb - inter)


def _det_dict(d, width, height):
    return {
        "class_id": d.class_id, "class_name": d.class_name, "confidence": round(d.confidence, 4),
        "bbox": list(d.bbox), "track_id": d.track_id, "source_models": d.source_models,
        "frame_id": d.frame_id, "timestamp": d.timestamp, "pose": d.pose, "keypoints": d.pose,
        "posture": d.posture, "face": d.face, "plate": d.plate,
        "behavior_flags": d.behavior_flags, "image_width": width, "image_height": height,
    }


def _track_dict(t):
    return {
        "track_id": t.track_id, "class_name": t.class_name, "bbox": list(t.bbox),
        "confidence": round(t.confidence, 4), "first_seen": t.first_seen, "last_seen": t.last_seen,
        "hits": t.hits, "velocity": list(t.velocity), "posture": t.posture, "pose": t.pose,
        "keypoints": t.pose, "pose_confidence": round(t.pose_confidence, 4),
        "face": getattr(t, "face", None), "plate": getattr(t, "plate", None),
        "behavior_flags": getattr(t, "behavior_flags", []),
    }
