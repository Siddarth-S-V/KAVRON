# KAVRON Backend 1.0

KAVRON is a FastAPI backend for an intelligent CCTV/video analytics platform. It provides camera management, low-latency capture, centralized YOLO11 inference, multi-model fusion, tracking, virtual-fence events, alerts, incidents, REST APIs, WebSockets, and a demo video mode.

## What is implemented

- FastAPI + Uvicorn
- SQLite by default, PostgreSQL-compatible SQLAlchemy configuration
- Threaded camera capture with latest-frame behavior
- Central AI inference scheduler with frame throttling
- YOLO11 model registry
- Conditional specialist routing
- Detection fusion
- DeepSORT adapter with a lightweight deterministic fallback tracker
- Virtual fence polygon intrusion events
- Alert/event WebSocket
- Camera MJPEG preview for development
- Camera/system APIs
- Incidents/fences persistence
- Model inspection and benchmark scripts

## Install

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and adjust `DEVICE` to `cuda:0` on a CUDA-capable machine if your PyTorch/Ultralytics installation supports it.

## Models

Put the provided `.pt` files in `models/`:

- yolo11n.pt
- yolo11n1.pt
- yolo11n_person.pt
- yolo11n_pose.pt
- yolo11n-pose.pt

Run:

```bash
python scripts/inspect_models.py
```

This loads the checkpoints with Ultralytics and prints task/class metadata. Do not infer specialist capabilities from filenames alone.

## Start

```bash
python run.py
```

or:

```bash
uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000/docs

The demo camera is automatically registered from `data/demo.mp4` when present.

## Frontend endpoints

Base API:

`http://127.0.0.1:8000/api/v1`

Live WebSockets:

`ws://127.0.0.1:8000/api/v1/ws/events`

`ws://127.0.0.1:8000/api/v1/ws/detection`

`ws://127.0.0.1:8000/api/v1/ws/alerts`

`ws://127.0.0.1:8000/api/v1/ws/*`

Live demo video:

`http://127.0.0.1:8000/api/v1/cameras/CAM-DEMO-01/stream`

## Add an RTSP camera

```bash
curl -X POST http://127.0.0.1:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"CAM-001","name":"Border Sector 01","source":"rtsp://user:password@camera/stream","protocol":"rtsp","sector":"01"}'
```

Then:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/cameras/CAM-001/start
```

## Performance model

Capture is threaded and independent of inference. The system keeps only the newest frame for AI scheduling and throttles inference to `AI_FPS` so 30-FPS video does not force 30-FPS inference.

YOLO specialists are invoked conditionally. The browser should receive lightweight JSON detection/track events over WebSocket instead of raw AI frames.

## Important limitation

ANPR and face analytics are exposed as extension points; the uploaded YOLO11 checkpoints must be inspected before claiming those functions are available. This backend does not invent missing OCR/face-recognition models.

## Tests

```bash
pytest -q
```
