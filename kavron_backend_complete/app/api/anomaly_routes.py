from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import db_session
from app.database.models import AnomalyRecord


router = APIRouter(
    prefix="/anomalies",
    tags=["anomalies"],
)


def serialize_anomaly(item: AnomalyRecord) -> dict:
    return {
        "id": item.id,
        "anomaly_id": item.anomaly_id,
        "camera_id": item.camera_id,
        "track_id": item.track_id,
        "anomaly_type": item.anomaly_type,
        "severity": item.severity,
        "message": item.message,
        "confidence": item.confidence,
        "bbox": item.bbox,
        "snapshot_path": item.snapshot_path,
        "metadata": item.metadata or {},
        "acknowledged": item.acknowledged,
        "created_at": (
            item.created_at.isoformat()
            if item.created_at
            else None
        ),
    }


@router.get("")
def list_anomalies(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    severity: str | None = Query(
        default=None,
    ),
    acknowledged: bool | None = Query(
        default=None,
    ),
    db: Session = Depends(db_session),
):
    query = (
        select(AnomalyRecord)
        .order_by(
            AnomalyRecord.created_at.desc()
        )
        .limit(limit)
    )

    if severity:
        query = query.where(
            AnomalyRecord.severity == severity.upper()
        )

    if acknowledged is not None:
        query = query.where(
            AnomalyRecord.acknowledged == acknowledged
        )

    records = db.scalars(query).all()

    return {
        "items": [
            serialize_anomaly(item)
            for item in records
        ],
        "count": len(records),
    }


@router.get("/{anomaly_id}")
def get_anomaly(
    anomaly_id: str,
    db: Session = Depends(db_session),
):
    item = db.scalar(
        select(AnomalyRecord).where(
            AnomalyRecord.anomaly_id == anomaly_id
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Anomaly not found",
        )

    return serialize_anomaly(item)


@router.patch("/{anomaly_id}/acknowledge")
def acknowledge_anomaly(
    anomaly_id: str,
    db: Session = Depends(db_session),
):
    item = db.scalar(
        select(AnomalyRecord).where(
            AnomalyRecord.anomaly_id == anomaly_id
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Anomaly not found",
        )

    item.acknowledged = True

    db.commit()
    db.refresh(item)

    return serialize_anomaly(item)