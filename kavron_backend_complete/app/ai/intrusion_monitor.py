from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import cv2
from ultralytics import YOLO
from sqlalchemy.orm import sessionmaker

from app.services.anomaly_service import AnomalyService


class IntrusionMonitor:
    """
    Person detection + tracking + restricted-zone anomaly detection.

    This does NOT identify individual people.
    It detects persons and evaluates whether they enter
    a restricted polygon.
    """

    def __init__(
        self,
        model_path: str,
        source,
        camera_id: str,
        session_factory,
        snapshot_root: str = "data/anomaly_snapshots",
        confidence: float = 0.35,
    ):
        self.model_path = model_path
        self.source = source
        self.camera_id = camera_id
        self.session_factory = session_factory
        self.confidence = confidence

        self.model = YOLO(model_path)

        self.anomaly_service = AnomalyService(
            snapshot_root=snapshot_root
        )

        self.running = False

        # Track IDs that already triggered recently.
        self.cooldowns: dict[str, float] = {}

        # seconds before the same track can generate another alert
        self.alert_cooldown = 8.0

        # Default rectangular restricted zone.
        # Replace these with your actual zone coordinates.
        self.zone = [
            (150, 100),
            (1100, 100),
            (1100, 650),
            (150, 650),
        ]

        self.frame_callback: Callable | None = None
        self.event_callback: Callable | None = None

    def set_zone(
        self,
        points: list[tuple[int, int]],
    ) -> None:
        if len(points) < 3:
            raise ValueError(
                "Restricted zone requires at least 3 points"
            )

        self.zone = points

    def set_frame_callback(
        self,
        callback: Callable,
    ) -> None:
        self.frame_callback = callback

    def set_event_callback(
        self,
        callback: Callable,
    ) -> None:
        self.event_callback = callback

    @staticmethod
    def center_inside_polygon(
        center: tuple[int, int],
        polygon: list[tuple[int, int]],
    ) -> bool:
        x, y = center

        inside = False

        j = len(polygon) - 1

        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            intersects = (
                (yi > y) != (yj > y)
                and (
                    x
                    < (xj - xi)
                    * (y - yi)
                    / ((yj - yi) or 1e-9)
                    + xi
                )
            )

            if intersects:
                inside = not inside

            j = i

        return inside

    def should_alert(
        self,
        track_id: str,
    ) -> bool:

        now = time.time()

        previous = self.cooldowns.get(track_id)

        if previous is not None:
            if now - previous < self.alert_cooldown:
                return False

        self.cooldowns[track_id] = now

        return True

    def process_frame(
        self,
        frame,
        frame_id: int,
    ):
        results = self.model.track(
            source=frame,
            persist=True,
            classes=[0],
            tracker="bytetrack.yaml",
            conf=self.confidence,
            verbose=False,
        )

        if not results:
            return frame

        result = results[0]

        annotated = frame.copy()

        # Draw restricted area.
        zone_points = [
            tuple(map(int, p))
            for p in self.zone
        ]

        cv2.polylines(
            annotated,
            [
                __import__("numpy").array(
                    zone_points,
                    dtype=__import__("numpy").int32,
                )
            ],
            True,
            (0, 0, 255),
            2,
        )

        cv2.putText(
            annotated,
            "RESTRICTED ZONE",
            zone_points[0],
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
        )

        if result.boxes is None:
            return annotated

        boxes = result.boxes

        ids = (
            boxes.id.int().cpu().tolist()
            if boxes.id is not None
            else [None] * len(boxes)
        )

        confidences = (
            boxes.conf.cpu().tolist()
            if boxes.conf is not None
            else [0.0] * len(boxes)
        )

        coordinates = (
            boxes.xyxy.cpu().tolist()
        )

        for track_id, confidence, bbox in zip(
            ids,
            confidences,
            coordinates,
        ):
            x1, y1, x2, y2 = map(
                int,
                bbox,
            )

            center = (
                (x1 + x2) // 2,
                (y1 + y2) // 2,
            )

            inside = self.center_inside_polygon(
                center,
                self.zone,
            )

            track_label = (
                str(track_id)
                if track_id is not None
                else "UNTRACKED"
            )

            if inside:
                label = (
                    f"INTRUSION | Track {track_label}"
                )

                cv2.rectangle(
                    annotated,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    3,
                )

                cv2.putText(
                    annotated,
                    label,
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2,
                )

                if track_id is not None:
                    track_key = str(track_id)

                    if self.should_alert(track_key):

                        db = self.session_factory()

                        try:
                            anomaly = (
                                self.anomaly_service.create_intrusion(
                                    db,
                                    camera_id=self.camera_id,
                                    track_id=track_key,
                                    confidence=float(confidence),
                                    bbox=[
                                        x1,
                                        y1,
                                        x2,
                                        y2,
                                    ],
                                    frame=annotated,
                                    zone_name="Restricted Zone",
                                    severity="HIGH",
                                    metadata={
                                        "frame_id": frame_id,
                                        "class_name": "person",
                                        "center": [
                                            center[0],
                                            center[1],
                                        ],
                                    },
                                )
                            )

                            if self.event_callback:
                                self.event_callback(
                                    {
                                        "type": "anomaly",
                                        "event_type": "INTRUSION",
                                        "severity": "HIGH",
                                        "camera_id": self.camera_id,
                                        "track_id": track_key,
                                        "anomaly_id": anomaly.anomaly_id,
                                        "confidence": float(
                                            confidence
                                        ),
                                        "bbox": [
                                            x1,
                                            y1,
                                            x2,
                                            y2,
                                        ],
                                        "message": (
                                            "Person detected "
                                            "inside restricted zone"
                                        ),
                                        "snapshot_path": (
                                            anomaly.snapshot_path
                                        ),
                                    }
                                )

                        finally:
                            db.close()

            else:
                cv2.rectangle(
                    annotated,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    annotated,
                    f"PERSON | Track {track_label}",
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

        if self.frame_callback:
            self.frame_callback(
                self.camera_id,
                annotated,
            )

        return annotated

    def run(self):
        source = (
            int(self.source)
            if isinstance(self.source, str)
            and self.source.isdigit()
            else self.source
        )

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise RuntimeError(
                f"Unable to open source: {self.source}"
            )

        self.running = True

        frame_id = 0

        try:
            while self.running:
                ok, frame = cap.read()

                if not ok:
                    break

                frame_id += 1

                annotated = self.process_frame(
                    frame,
                    frame_id,
                )

                cv2.imshow(
                    "KAVRON Intrusion Monitor",
                    annotated,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break

        finally:
            self.running = False

            cap.release()
            cv2.destroyAllWindows()

    def stop(self):
        self.running = False