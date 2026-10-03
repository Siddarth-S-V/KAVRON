from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.database.models import Camera, DetectionRecord, EventRecord, IncidentRecord, VirtualFence

class CameraRepo:
    @staticmethod
    def list(db: Session):
        return db.scalars(select(Camera).order_by(Camera.id)).all()
    @staticmethod
    def get(db: Session, camera_id: str):
        return db.get(Camera, camera_id)
    @staticmethod
    def upsert(db: Session, data: dict):
        obj = db.get(Camera, data["id"])
        if obj is None:
            obj = Camera(**data); db.add(obj)
        else:
            for k, v in data.items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj

class DetectionRepo:
    @staticmethod
    def add(db: Session, data: dict):
        obj = DetectionRecord(**data); db.add(obj); db.commit(); db.refresh(obj); return obj
    @staticmethod
    def recent(db: Session, limit: int = 100):
        return db.scalars(select(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).limit(limit)).all()

class EventRepo:
    @staticmethod
    def add(db: Session, data: dict):
        obj = EventRecord(**data); db.add(obj); db.commit(); db.refresh(obj); return obj
    @staticmethod
    def recent(db: Session, limit: int = 100):
        return db.scalars(select(EventRecord).order_by(desc(EventRecord.timestamp)).limit(limit)).all()

class IncidentRepo:
    @staticmethod
    def add(db: Session, data: dict):
        obj = IncidentRecord(**data); db.add(obj); db.commit(); db.refresh(obj); return obj
    @staticmethod
    def list(db: Session, limit: int = 100):
        return db.scalars(select(IncidentRecord).order_by(desc(IncidentRecord.created_at)).limit(limit)).all()
    @staticmethod
    def get(db: Session, incident_id: str): return db.get(IncidentRecord, incident_id)

class FenceRepo:
    @staticmethod
    def list(db: Session): return db.scalars(select(VirtualFence).order_by(VirtualFence.name)).all()
    @staticmethod
    def add(db: Session, data: dict):
        obj = VirtualFence(**data); db.add(obj); db.commit(); db.refresh(obj); return obj
    @staticmethod
    def get(db: Session, fence_id: str): return db.get(VirtualFence, fence_id)
    @staticmethod
    def update(db: Session, fence_id: str, data: dict):
        obj = db.get(VirtualFence, fence_id)
        if obj is None: return None
        for k, v in data.items(): setattr(obj, k, v)
        db.commit(); db.refresh(obj); return obj
    @staticmethod
    def delete(db: Session, fence_id: str):
        obj = db.get(VirtualFence, fence_id)
        if obj is None: return None
        db.delete(obj); db.commit(); return obj
