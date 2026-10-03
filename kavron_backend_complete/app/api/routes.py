from __future__ import annotations

import asyncio
import json
import os
import time
import uuid

import cv2

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
)

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.database.db import db_session
from app.database.repositories import (
    CameraRepo,
    DetectionRepo,
    EventRepo,
    IncidentRepo,
    FenceRepo,
)
from app.database.models import IncidentRecord
from app.schemas.common import (
    CameraCreate,
    CameraLocationUpdate,
    FenceCreate,
    FenceUpdate,
    IncidentUpdate,
)


router = APIRouter()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def db():
    yield from db_session()


# ============================================================
# SERIALIZATION
# ============================================================

def serialize(obj):
    """
    Convert SQLAlchemy objects into JSON-safe dictionaries.
    """

    if hasattr(obj, "__table__"):
        return {
            column.name: getattr(obj, column.name)
            for column in obj.__table__.columns
        }

    return obj


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def health(request: Request):

    scheduler = request.app.state.scheduler

    return {
        "status": "ok",
        "service": "KAVRON",
        "version": request.app.state.settings.version,
        "yolo_enabled": request.app.state.settings.enable_yolo,
        "models_loaded": (
            scheduler.registry.loaded()
            if scheduler.registry
            else []
        ),
    }


# ============================================================
# OVERVIEW
# ============================================================

@router.get("/overview")
def overview(request: Request):

    state = request.app.state.runtime_state
    registry = request.app.state.camera_registry

    cameras = list(state.cameras.values())

    online = 0

    for camera in cameras:

        camera_id = camera.get(
            "camera_id",
            camera.get("id")
        )

        runtime_camera = registry.items.get(camera_id)

        is_online = bool(
            camera.get("online")
            or camera.get("running")
            or str(camera.get("status", "")).lower() == "online"
            or (
                runtime_camera is not None
                and (
                    getattr(runtime_camera, "running", False)
                    or str(
                        getattr(runtime_camera, "status", "")
                    ).lower() == "online"
                )
            )
        )

        if is_online:
            online += 1

    alerts = list(state.alerts)[:10]

    active_incidents = sum(
        1
        for incident in state.incidents
        if incident.get("status") != "RESOLVED"
    )

    return {
        "cameras_total": len(cameras),

        "cameras_online": online,

        "active_incidents": active_incidents,

        "detections_today": state.metrics.get(
            "detections_total",
            0,
        ),

        "alerts": state.metrics.get(
            "alerts_total",
            0,
        ),

        "tracked_objects": sum(
            len(value)
            for value in state.latest_tracks.values()
        ),

        "system_health": round(
            (online / max(1, len(cameras))) * 100,
            1,
        ),

        "recent_alerts": alerts,
        "inference": dict(getattr(request.app.state.scheduler, "metrics", {})),
    }

# ============================================================
# CAMERAS
# ============================================================

@router.get("/cameras")
def list_cameras(
    request: Request,
    session: Session = Depends(db),
):
    """
    Return the union of:
    1. Cameras stored in SQLite
    2. Cameras currently registered in runtime

    This allows the demo camera to appear immediately even
    when it has not yet been persisted to the database.
    """

    runtime_state = request.app.state.runtime_state

    # --------------------------------------------------------
    # Database cameras
    # --------------------------------------------------------

    database_items = CameraRepo.list(session)

    result = {}

    for camera in database_items:
        item = serialize(camera)
        result[camera.id] = item

    # --------------------------------------------------------
    # Runtime cameras
    # --------------------------------------------------------
    # Runtime data wins because it contains live information
    # such as online status, FPS, dimensions, etc.
    # --------------------------------------------------------

    for camera_id, runtime_camera in runtime_state.cameras.items():

        current = result.get(
            camera_id,
            {
                "id": camera_id,
            },
        )

        current.update(runtime_camera)

        # Keep API naming consistent with frontend.
        current["camera_id"] = camera_id

        result[camera_id] = current

    return list(result.values())


# ============================================================
# ADD CAMERA
# ============================================================

@router.post("/cameras")
def add_camera(
    payload: CameraCreate,
    request: Request,
    session: Session = Depends(db),
):

    data = payload.model_dump()

    camera_id = data.pop("camera_id")

    # Persist camera
    CameraRepo.upsert(
        session,
        {
            "id": camera_id,
            **data,
        },
    )

    # Add runtime camera
    state = request.app.state.camera_registry.add(
        {
            "camera_id": camera_id,
            **data,
        }
    )

    request.app.state.runtime_state.set_camera(
        camera_id,
        state.__dict__.copy(),
    )

    return {
        "camera_id": camera_id,
        "status": "created",
    }


# ============================================================
# START CAMERA
# ============================================================

@router.post("/cameras/{camera_id}/start")
def start_camera(
    camera_id: str,
    request: Request,
):

    registry = request.app.state.camera_registry

    try:
        state = registry.start(camera_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Camera not found",
        )

    return state.__dict__


# ============================================================
# STOP CAMERA
# ============================================================

@router.post("/cameras/{camera_id}/stop")
def stop_camera(
    camera_id: str,
    request: Request,
):

    registry = request.app.state.camera_registry

    try:
        state = registry.stop(camera_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Camera not found",
        )

    return state.__dict__


# ============================================================
# CAMERA LOCATION
# ============================================================

@router.patch("/cameras/{camera_id}/location")
def update_camera_location(
    camera_id: str,
    payload: CameraLocationUpdate,
    request: Request,
    session: Session = Depends(db),
):
    """Persist a real-world map position for a camera and update runtime state."""
    obj = CameraRepo.get(session, camera_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    data = payload.model_dump()
    obj.latitude = data["latitude"]
    obj.longitude = data["longitude"]
    obj.location_accuracy_m = data.get("accuracy_m")
    obj.location_source = data.get("source", "manual")
    if data.get("location"):
        obj.location = data["location"]
    session.commit()
    session.refresh(obj)

    registry = request.app.state.camera_registry
    runtime = registry.items.get(camera_id)
    if runtime is not None:
        runtime.latitude = obj.latitude
        runtime.longitude = obj.longitude
        runtime.location_accuracy_m = obj.location_accuracy_m
        runtime.location_source = obj.location_source
        if obj.location:
            runtime.location = obj.location
        request.app.state.runtime_state.set_camera(camera_id, runtime.__dict__.copy())

    return serialize(obj)


# ============================================================
# DELETE CAMERA
# ============================================================

@router.delete("/cameras/{camera_id}")
def delete_camera(
    camera_id: str,
    request: Request,
    session: Session = Depends(db),
):

    registry = request.app.state.camera_registry

    registry.remove(camera_id)

    obj = CameraRepo.get(
        session,
        camera_id,
    )

    if obj:
        session.delete(obj)
        session.commit()

    return {
        "status": "deleted",
        "camera_id": camera_id,
    }


# ============================================================
# LIVE CAMERA STREAM
# ============================================================

@router.get("/cameras/{camera_id}/stream")
def stream_camera(camera_id: str, request: Request):
    """Low-overhead MJPEG stream backed by the single per-frame JPEG cache."""
    registry = request.app.state.camera_registry
    runtime_state = request.app.state.runtime_state
    if camera_id not in registry.items:
        raise HTTPException(status_code=404, detail="Camera not found")

    def generate():
        last_seq = -1
        while True:
            jpeg, seq = runtime_state.get_stream_snapshot(camera_id)
            if jpeg is None or seq == last_seq:
                time.sleep(0.02)
                continue
            last_seq = seq
            yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
            time.sleep(0.01)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame", headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Access-Control-Allow-Origin": "*",
    })


# ============================================================
# DETECTIONS
# ============================================================

@router.get("/detections")
def detections(request: Request):

    return (
        request
        .app
        .state
        .runtime_state
        .latest_detections
    )


# ============================================================
# TRACKS
# ============================================================

@router.get("/tracks")
def tracks(request: Request):

    return (
        request
        .app
        .state
        .runtime_state
        .latest_tracks
    )


# ============================================================
# ALERTS
# ============================================================

@router.get("/alerts")
def alerts(request: Request):

    return list(
        request
        .app
        .state
        .runtime_state
        .alerts
    )[:100]


# ============================================================
# ACKNOWLEDGE ALERT
# ============================================================

@router.post("/alerts/{event_id}/acknowledge")
def acknowledge_alert(
    event_id: str,
    request: Request,
):

    state = request.app.state.runtime_state

    for alert in state.alerts:

        if alert.get("event_id") == event_id:

            alert["acknowledged"] = True

            return alert

    raise HTTPException(
        status_code=404,
        detail="Alert not found",
    )


# ============================================================
# INCIDENTS
# ============================================================

@router.get("/incidents")
def incidents(
    session: Session = Depends(db),
):

    return [
        serialize(item)
        for item in IncidentRepo.list(session)
    ]


# ============================================================
# CREATE INCIDENT
# ============================================================

@router.post("/incidents")
def create_incident(
    payload: dict,
    session: Session = Depends(db),
):

    incident_id = (
        payload.get("id")
        or f"INC-{uuid.uuid4().hex[:10].upper()}"
    )

    data = {
        "id": incident_id,
        "title": payload.get(
            "title",
            "KAVRON Incident",
        ),
        "severity": payload.get(
            "severity",
            "HIGH",
        ),
        "status": "NEW",
        "camera_id": payload.get(
            "camera_id",
            "",
        ),
        "payload": payload,
    }

    IncidentRepo.add(
        session,
        data,
    )

    return data


# ============================================================
# UPDATE INCIDENT
# ============================================================

@router.patch("/incidents/{incident_id}")
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    session: Session = Depends(db),
):

    incident = IncidentRepo.get(
        session,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    incident.status = payload.status

    if payload.notes:

        incident.payload = {
            **(incident.payload or {}),
            "notes": payload.notes,
        }

    if payload.status == "RESOLVED":

        from datetime import datetime, timezone

        incident.resolved_at = datetime.now(
            timezone.utc
        )

    session.commit()
    session.refresh(incident)

    return serialize(incident)


# ============================================================
# VIRTUAL FENCES
# ============================================================

@router.get("/fences")
def fences(
    session: Session = Depends(db),
):

    return [
        serialize(item)
        for item in FenceRepo.list(session)
    ]


# ============================================================
# ADD VIRTUAL FENCE
# ============================================================

@router.post("/fences")
def add_fence(
    payload: FenceCreate,
    request: Request,
    session: Session = Depends(db),
):

    data = payload.model_dump()

    FenceRepo.add(
        session,
        data,
    )

    request.app.state.event_engine.set_fences(
        [
            serialize(item)
            for item in FenceRepo.list(session)
        ]
    )

    return data


@router.patch("/fences/{fence_id}")
def update_fence(
    fence_id: str,
    payload: FenceUpdate,
    request: Request,
    session: Session = Depends(db),
):
    data = payload.model_dump(exclude_none=True)
    if "coordinates" in data and not data["coordinates"]:
        raise HTTPException(status_code=400, detail="Fence coordinates cannot be empty")
    obj = FenceRepo.update(session, fence_id, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="Fence not found")
    request.app.state.event_engine.set_fences([serialize(item) for item in FenceRepo.list(session)])
    return serialize(obj)


@router.delete("/fences/{fence_id}")
def delete_fence(
    fence_id: str,
    request: Request,
    session: Session = Depends(db),
):
    obj = FenceRepo.delete(session, fence_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Fence not found")
    request.app.state.event_engine.set_fences([serialize(item) for item in FenceRepo.list(session)])
    return {"status": "deleted", "id": fence_id}


# ============================================================
# MODELS
# ============================================================

@router.get("/models/stage3/status")
def stage3_model_status(request: Request):
    manager = request.app.state.model_asset_manager
    return {
        "stage": 3,
        "assets": manager.status(),
        "local_models": manager.local_status(),
        "auto_download": request.app.state.settings.auto_download_specialist_models,
        "detector_candidates": [x.strip() for x in request.app.state.settings.detector_candidates.split(",") if x.strip()],
        "active_detector": request.app.state.settings.general_model,
        "pose_model": request.app.state.settings.pose_model,
        "rtmpose_enabled": request.app.state.settings.enable_rtmpose,
        "ocr_model_dir": request.app.state.settings.paddleocr_model_dir,
    }


@router.post("/models/stage3/download")
def stage3_model_download(request: Request):
    manager = request.app.state.model_asset_manager
    result = {}
    for key in manager.status():
        try:
            result[key] = {"ok": True, "path": str(manager.ensure(key))}
        except Exception as exc:
            result[key] = {"ok": False, "error": str(exc)}
    return result


@router.get("/models")
def models(request: Request):

    return (
        request
        .app
        .state
        .scheduler
        .registry
        .discover()
    )


# ============================================================
# MODEL METADATA
# ============================================================

@router.get("/models/metadata")
def model_metadata(request: Request):

    return (
        request
        .app
        .state
        .scheduler
        .registry
        .metadata()
    )


# ============================================================
# SYSTEM METRICS
# ============================================================

@router.get("/system/metrics")
def metrics(request: Request):

    state = request.app.state.runtime_state
    scheduler = request.app.state.scheduler
    return {
        **dict(state.metrics),
        "inference": dict(getattr(scheduler, "metrics", {})),
    }


# ============================================================
# WEBSOCKET EVENTS
# ============================================================

@router.websocket("/ws/{topic}")
async def websocket_endpoint(
    websocket: WebSocket,
    topic: str,
):

    await websocket.accept()

    bus = websocket.app.state.event_bus

    queue = await bus.subscribe(topic)

    try:

        while True:

            event = await queue.get()

            await websocket.send_text(
                json.dumps(
                    event,
                    default=str,
                )
            )

    except WebSocketDisconnect:
        pass

    finally:

        await bus.unsubscribe(
            topic,
            queue,
        )