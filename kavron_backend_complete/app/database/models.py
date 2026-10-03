from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(Text)
    protocol: Mapped[str] = mapped_column(String(32), default="file")
    location: Mapped[str] = mapped_column(String(255), default="")
    sector: Mapped[str] = mapped_column(String(128), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_source: Mapped[str] = mapped_column(String(32), default="manual")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
    )


class DetectionRecord(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    camera_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    frame_id: Mapped[int] = mapped_column(
        Integer,
    )

    class_name: Mapped[str] = mapped_column(
        String(120),
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
    )

    bbox: Mapped[list] = mapped_column(
        JSON,
    )

    track_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        index=True,
    )


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    event_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )

    camera_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    track_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        index=True,
    )


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
    )

    severity: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="NEW",
        index=True,
    )

    camera_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class VirtualFence(Base):
    __tablename__ = "virtual_fences"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
    )

    camera_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    geometry_type: Mapped[str] = mapped_column(
        String(32),
    )

    coordinates: Mapped[list] = mapped_column(
        JSON,
    )

    allowed_objects: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    severity: Mapped[str] = mapped_column(
        String(32),
        default="HIGH",
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )


class AnomalyRecord(Base):
    """
    Persistent anomaly / intrusion log.

    This intentionally records an event based on detection + rule context,
    not biometric identity.
    """

    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    anomaly_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )

    camera_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    track_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    anomaly_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
    )

    bbox: Mapped[list] = mapped_column(
        JSON,
    )

    snapshot_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # "metadata" is reserved by SQLAlchemy's Declarative API.
    # Use a different Python attribute name.
    extra_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        index=True,
    )