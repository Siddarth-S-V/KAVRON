from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import cv2
from sqlalchemy.orm import Session

from app.database.models import AnomalyRecord


class AnomalyService:
    """
    Handles persistent anomaly creation and snapshot storage.
    """

    def __init__(self, snapshot_root: str = "data/anomaly_snapshots"):
        self.snapshot_root = Path(snapshot_root)
        self.snapshot_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def create_intrusion(
        self,
        db: Session,
        *,
        camera_id: str,
        track_id: str | None,
        confidence: float,
        bbox: list[float],
        frame,
        zone_name: str = "Restricted Zone",
        severity: str = "HIGH",
        metadata: dict | None = None,
    ) -> AnomalyRecord:

        anomaly_id = f"ANOM-{uuid4().hex[:12].upper()}"

        timestamp = datetime.now(timezone.utc)

        date_dir = self.snapshot_root / timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        snapshot_filename = (
            f"{anomaly_id}_"
            f"{camera_id}_"
            f"{timestamp.strftime('%H%M%S')}.jpg"
        )

        snapshot_path = date_dir / snapshot_filename

        snapshot_saved = False

        if frame is not None:
            try:
                snapshot_saved = bool(
                    cv2.imwrite(
                        str(snapshot_path),
                        frame,
                    )
                )
            except Exception:
                snapshot_saved = False

        stored_snapshot = (
            str(snapshot_path)
            if snapshot_saved
            else None
        )

        record = AnomalyRecord(
            anomaly_id=anomaly_id,
            camera_id=camera_id,
            track_id=track_id,
            anomaly_type="INTRUSION",
            severity=severity,
            message=(
                f"Person detected inside {zone_name}"
            ),
            confidence=float(confidence),
            bbox=[float(x) for x in bbox],
            snapshot_path=stored_snapshot,
            metadata=metadata or {},
            acknowledged=False,
            created_at=timestamp,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record