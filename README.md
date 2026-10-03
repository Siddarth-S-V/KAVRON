::: {align="center"}
<img src="assets/KAVRON AI Surveillance Valley Banner.png" alt="KAVRON — AI-Powered Surveillance & Intelligent Video Analytics" width="100%">{=html}

🛰️ KAVRON

AI-Powered Surveillance & Intelligent Video Analytics

<p>

<img src="https://img.shields.io/badge/Computer%20Vision-YOLO-7C3AED?style=for-the-badge" alt="Computer Vision">{=html}
<img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=for-the-badge&logo=react&logoColor=111827" alt="React">{=html}
<img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">{=html}
<img src="https://img.shields.io/badge/Realtime-WebSockets-0EA5E9?style=for-the-badge" alt="WebSockets">{=html}
<img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">{=html}

</p>

SEE → UNDERSTAND → TRACK → RESPOND

KAVRON turns raw camera streams into structured, actionable
intelligence.
:::

🌐 The Idea Behind KAVRON

Modern camera systems can see everything, but seeing is not the same
as understanding.

KAVRON is designed as an intelligent video-analytics layer between
camera feeds and human decision-making. It accepts CCTV/RTSP streams and
recorded video, runs computer-vision inference, fuses detections,
maintains object tracks, evaluates virtual-fence rules, and exposes
alerts and analytics through a realtime dashboard.

The system is intentionally modular:

CAMERA WORLD
     │
     ▼
┌──────────────────┐
│ Video Acquisition│
└────────┬─────────┘
         ▼
┌──────────────────┐
│  AI Inference    │
│ YOLO + Specialists│
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Detection Fusion │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Object Tracking  │
│    DeepSORT      │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Rules & Fences   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Alerts / Incidents│
└────────┬─────────┘
         ▼
┌──────────────────┐
│ REST + WebSockets│
└────────┬─────────┘
         ▼
   KAVRON DASHBOARD

✦ Why KAVRON?

KAVRON is not built around a single detection model.

It combines multiple stages into one operational pipeline:

Layer                               Responsibility

🎥 Capture                      Receives CCTV, RTSP and video-file
sources

🧠 Inference                    Runs YOLO and specialist
computer-vision models

🧩 Fusion                       Combines and refines model outputs

🛰️ Tracking                     Maintains object identities across
frames

🚧 Rules                        Applies virtual-fence and intrusion
logic

🚨 Incidents                    Converts events into alerts and
persistent incidents

📡 Realtime                     Streams detection, alert and
camera-state events

🧭 System at a Glance

::: {align="center"}
<img src="assets/KAVRON AI Surveillance Architecture(1).png" alt="KAVRON System Architecture" width="100%">{=html}
:::

Processing path

CCTV / RTSP / MP4
        │
        ▼
Camera Capture
        │
        ▼
AI Scheduler
        │
        ▼
YOLO + Specialist Models
        │
        ▼
Detection Fusion
        │
        ▼
DeepSORT / Fallback Tracker
        │
        ▼
Virtual Fence + Event Rules
        │
        ├──────────────► Alerts & Incidents
        │
        ▼
REST APIs + WebSockets
        │
        ▼
React Monitoring Dashboard

⚙️ A Different Approach to Video Processing

KAVRON separates camera capture from AI inference.

A camera may deliver frames faster than the AI pipeline needs to process
them. Instead of forcing inference on every incoming frame, KAVRON
maintains the newest frame and schedules inference according to the
configured AI_FPS.

High-FPS Camera
      │
      ▼
┌─────────────────────┐
│ Capture Thread      │
│ Keep Latest Frame   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ AI Scheduler        │
│ Configurable AI_FPS │
└──────────┬──────────┘
           │
           ▼
      AI Inference

This keeps the acquisition layer independent from the computational
workload.

🧠 Computer Vision Stack

KAVRON's backend contains a collection of AI/computer-vision assets:

Model / Component            Intended Role

YOLO checkpoints         Object, person and pose detection
RTMPose                  Pose estimation
YuNet                    Face detection
SFace                    Face recognition
Expression model         Facial-expression recognition
License Plate Detector   Plate detection
PaddleOCR assets         OCR pipeline

Model assets are located under:

kavron_backend_complete/models/

Inspect available model metadata with:

python scripts/inspect_models.py

Note: Face and ANPR capabilities are documented as extension
points. The presence of a model asset does not by itself mean that
every specialist pipeline is active in every runtime path.

🚨 From Detection to Incident

A detection becomes useful when the system can reason about what happens
next.

KAVRON follows this event-oriented path:

Detection
   │
   ▼
Track ID Assigned
   │
   ▼
Object Position Updated
   │
   ▼
Virtual-Fence / Rule Check
   │
   ├── No Event ──► Continue Tracking
   │
   └── Event ─────► Create Incident
                         │
                         ▼
                    Generate Alert
                         │
                         ▼
                   Realtime Delivery

This allows the frontend to receive structured events instead of dealing
directly with raw model output.

📡 Realtime Communication

KAVRON exposes both REST and WebSocket interfaces.

REST endpoints

GET /overview
GET /cameras
GET /detections
GET /tracks
GET /alerts
GET /incidents
GET /fences
GET /models
GET /system/metrics

WebSocket channels

ws://127.0.0.1:8000/api/v1/ws/detections
ws://127.0.0.1:8000/api/v1/ws/alerts
ws://127.0.0.1:8000/api/v1/ws/camera_state

Example detection event

{
  "type": "detection",
  "camera_id": "CAM-DEMO-01",
  "class_name": "person",
  "confidence": 0.92,
  "bbox": [100, 80, 240, 430],
  "track_id": "TRACK-0001",
  "source_models": ["general", "person"],
  "frame_id": 123,
  "timestamp": 1770000000.0
}

🎬 KAVRON --- See It Running

<div align="center">

▶️ Live Demo

<video controls muted loop width="100%">

<source src="assets/KAVRON Demo.mp4" type="video/mp4">

</video>

Realtime detection · Tracking · AI analytics · Alerts · Monitoring

</div>

GitHub note: repository-hosted MP4 files may not play inline in
every GitHub README view. If the embedded player does not appear, open
the video directly:

🎥 Open KAVRON Demo

The showcase video is stored separately from the backend demo assets:

assets/KAVRON Demo.mp4

For files larger than GitHub's standard 100 MB repository limit, use Git
LFS or another video-hosting approach.

🧱 Technology Blueprint

::: {align="center"}
Area                 Technology

🎨 Frontend          React 19 · Vite · TypeScript
🧩 UI                Tailwind CSS · Framer Motion · Lucide React
📊 Visualization     Recharts
⚡ Backend           FastAPI · Uvicorn · Pydantic
🐍 Runtime           Python 3.11
👁️ Computer Vision   OpenCV
🎯 Detection         Ultralytics / YOLO
🛰️ Tracking          DeepSORT
🗄️ Persistence       SQLite · SQLAlchemy
📡 Realtime          WebSockets
🧪 Testing           Pytest
:::

🚀 Run KAVRON Locally

1. Clone

git clone https://github.com/Siddarth-S-V/KAVRON.git
cd KAVRON

2. Backend

Windows PowerShell

cd kavron_backend_complete

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Start the API:

python run.py

Or:

uvicorn app.main:app --reload

3. Frontend

cd Frontend
pnpm install

Configure:

VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1

Run:

pnpm dev

Build:

pnpm build

4. API Documentation

Once the backend is running:

http://127.0.0.1:8000/docs

API base:

http://127.0.0.1:8000/api/v1

📷 Connect an RTSP Camera

Add a camera:

curl -X POST http://127.0.0.1:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"CAM-001","name":"Border Sector 01","source":"rtsp://user:password@camera/stream","protocol":"rtsp","sector":"01"}'

Start it:

curl -X POST http://127.0.0.1:8000/api/v1/cameras/CAM-001/start

🧪 Validation & Developer Tools

Run the backend test suite:

pytest -q

Inspect model assets:

python scripts/inspect_models.py

Developer and training utilities:

kavron_backend_complete/scripts/
kavron_backend_complete/training/

📁 Repository Map

KAVRON/
│
├── Frontend/
│   ├── src/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── vite.config.ts
│
├── kavron_backend_complete/
│   ├── app/
│   ├── data/
│   ├── models/
│   ├── scripts/
│   ├── tests/
│   ├── training/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
│
├── assets/
│   ├── KAVRON AI Surveillance Valley Banner.png
│   ├── KAVRON AI Surveillance Architecture(1).png
│   └── KAVRON Demo.mp4
│
├── .gitignore
└── README.md

🔐 Security First

Never commit secrets or private infrastructure credentials.

✅ .env.example
❌ .env
❌ API keys
❌ passwords
❌ private camera credentials
❌ production secrets

Camera credentials and deployment secrets should remain outside version
control.

🛣️ Where KAVRON Can Go Next

The current architecture leaves room for additional capabilities:

🌐 WebRTC / HLS production video delivery

☁️ Distributed camera processing

🧠 Additional specialist AI models

📊 Advanced analytics dashboards

🔔 Rich notification integrations

🗺️ Geospatial monitoring

⚙️ Production-scale deployment tooling

These are future directions, not claims about the current
implementation.

👨‍💻 Built By

::: {align="center"}

Siddarth S V

Engineering Student

B.E. Electronics & Communication Engineering

BS in Data Science and Applications

<p>

<a href="https://github.com/Siddarth-S-V">{=html}
<img src="https://img.shields.io/badge/GitHub-Siddarth--S--V-181717?style=for-the-badge&logo=github" alt="GitHub">{=html}
</a>{=html}
<a href="https://www.linkedin.com/in/siddarth-s-v-0b20792b7/">{=html}
<img src="https://img.shields.io/badge/LinkedIn-Siddarth%20S%20V-0A66C2?style=for-the-badge&logo=linkedin" alt="LinkedIn">{=html}
</a>{=html}

</p>

:::

📜 Project & Third-Party Assets

KAVRON contains third-party libraries, pretrained model assets,
datasets, OCR components and demonstration media.

Before redistribution or commercial deployment, verify the applicable
licenses and usage restrictions for each external component.

The project documentation does not currently define a separate project
license.

::: {align="center"}

🛰️ KAVRON

SEE THE FRAME. UNDERSTAND THE EVENT. ACT ON THE SIGNAL.

Detect · Track · Fuse · Alert · Visualize

<br>{=html}

⭐ If KAVRON is useful or interesting, consider starring the
repository.
:::