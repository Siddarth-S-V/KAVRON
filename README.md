<div align="center">

<img src="assets/KAVRON AI Surveillance Valley Banner.png" alt="KAVRON - AI Powered Surveillance and Intelligent Video Analytics" width="100%">

# 🛰️ KAVRON

### **AI-Powered Surveillance & Intelligent Video Analytics**

<p>
  <a href="https://github.com/Siddarth-S-V/KAVRON">
    <img src="https://img.shields.io/badge/GitHub-KAVRON-181717?style=for-the-badge&logo=github" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/AI-Computer%20Vision-00D9FF?style=for-the-badge" alt="AI">
  <img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=for-the-badge&logo=react&logoColor=111827" alt="React">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Detection-YOLO-7C3AED?style=for-the-badge" alt="YOLO">
  <img src="https://img.shields.io/badge/Realtime-WebSockets-0EA5E9?style=for-the-badge" alt="WebSockets">
</p>

**Detect • Track • Fuse • Alert • Visualize**

</div>

---

## 🌌 What is KAVRON?

**KAVRON** is a full-stack intelligent CCTV and video-analytics platform that processes camera streams and recorded video through an AI pipeline and delivers structured events to a live monitoring interface.

```text
🎥 Video Input
      ↓
🧠 AI Inference
      ↓
🎯 Detection + Fusion
      ↓
🛰️ Tracking
      ↓
🚧 Rules / Virtual Fences
      ↓
🚨 Alerts & Incidents
      ↓
📡 REST + WebSockets
      ↓
🖥️ React Dashboard
```

---

## ⚡ What KAVRON Does

<table>
<tr>
<td align="center" width="25%">

### 🎥

**VIDEO**

Camera & video ingestion

</td>
<td align="center" width="25%">

### 🧠

**AI**

Detection & specialist models

</td>
<td align="center" width="25%">

### 🛰️

**TRACK**

Object tracking across frames

</td>
<td align="center" width="25%">

### 🚨

**ALERT**

Events, incidents & notifications

</td>
</tr>
</table>

---

## 🧩 Core Features

<details open>
<summary><strong>🎥 Camera & Video Processing</strong></summary>

* CCTV / RTSP camera support
* Video-file and demo-video processing
* Threaded camera capture
* Latest-frame buffering
* Development MJPEG streaming

</details>

<details>
<summary><strong>🧠 AI Inference</strong></summary>

* Centralized AI inference scheduler
* Configurable inference FPS
* YOLO model registry
* Conditional specialist routing
* Detection fusion
* Model inspection tooling

</details>

<details>
<summary><strong>🛰️ Tracking & Events</strong></summary>

* DeepSORT adapter
* Lightweight fallback tracker
* Track management
* Virtual-fence polygon rules
* Intrusion events

</details>

<details>
<summary><strong>🚨 Events & Realtime Monitoring</strong></summary>

* Alerts
* Incident persistence
* REST APIs
* Detection WebSockets
* Alert WebSockets
* Camera-state WebSockets
* System metrics

</details>

---

# 🏗️ System Architecture

<div align="center">

<img src="assets/KAVRON AI Surveillance Architecture(1).png" alt="KAVRON System Architecture" width="100%">

</div>

### 🔄 Runtime Flow

```mermaid
flowchart LR

    A[📹 CCTV / RTSP / MP4]
    B[🎞️ Camera Capture]
    C[⏱️ AI Scheduler]
    D[🧠 YOLO + Specialist Models]
    E[🧩 Detection Fusion]
    F[🛰️ Tracking]
    G[🚧 Virtual Fence / Rules]
    H[🚨 Alerts & Incidents]
    I[📡 REST + WebSockets]
    J[🖥️ React Dashboard]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G -->|Event| H
    E --> I
    H --> I
    I --> J
```

---

# 🎬 KAVRON Demo

<div align="center">

### ▶️ KAVRON in Action

<video controls autoplay muted loop width="100%">
  <source src="assets/KAVRON Demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

<br>

**Real-time detection • Tracking • AI analytics • Alerts • Monitoring**

</div>

> [!NOTE]
> The video is stored directly in `assets/KAVRON Demo.mp4`. GitHub's README renderer may not always play repository-hosted MP4 files inline. When inline playback is unavailable, use the video file link below.

**🎥 [Open the full KAVRON Demo](assets/KAVRON%20Demo.mp4)**

---

# 🧠 AI Model Stack

KAVRON includes model assets in:

```text
kavron_backend_complete/models/
```

| Component              | Purpose                          |
| ---------------------- | -------------------------------- |
| YOLO checkpoints       | Object / person / pose detection |
| RTMPose                | Pose estimation                  |
| YuNet                  | Face detection                   |
| SFace                  | Face recognition                 |
| Expression model       | Facial-expression recognition    |
| License-plate detector | Plate detection                  |
| PaddleOCR assets       | OCR pipeline assets              |

### 🔍 Inspect Models

```bash
python scripts/inspect_models.py
```

> [!NOTE]
> Face and ANPR functionality are documented in the backend as extension points. The presence of model assets does not mean every specialist pipeline is active in every runtime path.

---

# 🎥 Video & Data

Development/demo video assets are included in:

```text
kavron_backend_complete/data/
```

The primary showcase video is kept separately in:

```text
assets/KAVRON Demo.mp4
```

> [!IMPORTANT]
> GitHub has a standard 100 MB per-file limit for normal Git repository files. Large videos above that size require Git LFS or another hosting method.

---

# 💻 Tech Stack

<div align="center">

| Layer        | Technologies                                |
| ------------ | ------------------------------------------- |
| 🎨 Frontend  | React 19 · Vite · TypeScript                |
| 🧩 UI        | Tailwind CSS · Framer Motion · Lucide React |
| 📊 Charts    | Recharts                                    |
| ⚡ Backend    | FastAPI · Uvicorn · Pydantic                |
| 🐍 Runtime   | Python 3.11                                 |
| 👁️ Vision   | OpenCV                                      |
| 🎯 Detection | Ultralytics / YOLO                          |
| 🛰️ Tracking | DeepSORT                                    |
| 🗄️ Database | SQLite · SQLAlchemy                         |
| 📡 Realtime  | WebSockets                                  |
| 🧪 Testing   | Pytest                                      |

</div>

---

# 🚀 Run KAVRON Locally

<details open>
<summary><strong>1️⃣ Clone the Repository</strong></summary>

```bash
git clone https://github.com/Siddarth-S-V/KAVRON.git
cd KAVRON
```

</details>

<details>
<summary><strong>2️⃣ Start the Backend</strong></summary>

### Windows PowerShell

```powershell
cd kavron_backend_complete

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start:

```powershell
python run.py
```

Or:

```powershell
uvicorn app.main:app --reload
```

</details>

<details>
<summary><strong>3️⃣ Configure & Start the Frontend</strong></summary>

```bash
cd Frontend
pnpm install
```

Configure:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Run:

```bash
pnpm dev
```

Build:

```bash
pnpm build
```

</details>

<details>
<summary><strong>4️⃣ Open the Backend</strong></summary>

### API Documentation

```text
http://127.0.0.1:8000/docs
```

### API Base

```text
http://127.0.0.1:8000/api/v1
```

</details>

---

# 📡 API & Realtime Layer

### REST

```text
GET /overview
GET /cameras
GET /detections
GET /tracks
GET /alerts
GET /incidents
GET /fences
GET /models
GET /system/metrics
```

### WebSockets

```text
ws://127.0.0.1:8000/api/v1/ws/detections
ws://127.0.0.1:8000/api/v1/ws/alerts
ws://127.0.0.1:8000/api/v1/ws/camera_state
```

### Example Detection Event

```json
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
```

---

# 📷 RTSP Camera

Add a camera:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"CAM-001","name":"Border Sector 01","source":"rtsp://user:password@camera/stream","protocol":"rtsp","sector":"01"}'
```

Start it:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/cameras/CAM-001/start
```

---

# 🧪 Testing

```bash
pytest -q
```

Model inspection:

```bash
python scripts/inspect_models.py
```

Developer and training utilities:

```text
kavron_backend_complete/scripts/
kavron_backend_complete/training/
```

---

# 📁 Project Structure

```text
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
```

---

# 🔐 Environment & Security

Real secrets should never be committed.

```text
✅ .env.example

❌ .env
❌ passwords
❌ API keys
❌ private camera credentials
❌ production secrets
```

---

# 🛣️ Future Direction

Potential future extensions include:

* 🌐 WebRTC / HLS production video delivery
* ☁️ Distributed camera processing
* 🧠 Additional specialist AI models
* 📊 Advanced analytics
* 🔔 Rich notification integrations
* 🗺️ Geospatial monitoring

---

# 👨‍💻 About the Developer

<div align="center">

## **Siddarth S V**

Engineering Student
**B.E. Electronics & Communication Engineering**
**BS in Data Science and Applications**

<br>

<a href="https://github.com/Siddarth-S-V">
<img src="https://img.shields.io/badge/GitHub-Siddarth--S--V-181717?style=for-the-badge&logo=github">
</a>

<a href="https://www.linkedin.com/in/siddarth-s-v-0b20792b7/">
<img src="https://img.shields.io/badge/LinkedIn-Siddarth%20S%20V-0A66C2?style=for-the-badge&logo=linkedin">
</a>

</div>

---

# © Copyright

<div align="center">

### **© 2026 Siddarth S V — KAVRON**

**All Rights Reserved.**

The **KAVRON** name, original source code, original documentation, branding, visual designs, and original project materials are the property of **Siddarth S V**, unless otherwise stated.

Third-party libraries, pretrained AI models, datasets, OCR assets, and externally sourced media remain subject to their respective licenses and terms.

Unauthorized reproduction, redistribution, modification, or commercial use of the original KAVRON project materials is not permitted without prior permission from the copyright holder.

</div>

---

<div align="center">

# 🛰️ KAVRON

### **FROM CAMERA STREAMS TO ACTIONABLE INTELLIGENCE**

**Detect · Track · Fuse · Alert · Visualize**

<br>

⭐ **Star the repository if you find KAVRON interesting.**

</div>
