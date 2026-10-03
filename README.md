<div align="center">

# 🛰️ KAVRON

### **SEE · UNDERSTAND · TRACK · RESPOND**

**AI-Powered Surveillance & Intelligent Video Analytics**

Turning camera streams into **structured events, intelligent tracking, and actionable alerts.**

<br>

![KAVRON Banner](assets/KAVRON%20AI%20Surveillance%20Valley%20Banner.png)

<br>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square\&logo=python\&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square\&logo=react\&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square\&logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLO](https://img.shields.io/badge/YOLO-Computer%20Vision-111111?style=flat-square)](https://ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=flat-square\&logo=opencv\&logoColor=white)](https://opencv.org/)

</div>

---

## ◈ What is KAVRON?

**KAVRON is an AI-powered surveillance intelligence platform that transforms live video into context-aware events.**

Instead of stopping at object detection, KAVRON connects **computer vision, multi-model detection, object tracking, virtual fences, incident intelligence, REST APIs, and realtime communication** into one unified monitoring system.

### The idea is simple:

> **Capture → Detect → Fuse → Track → Reason → Alert → Visualize**

---

## ⚡ Why KAVRON?

KAVRON goes beyond frame-by-frame detection by connecting **vision, tracking, rules, incidents, and realtime communication** into a single intelligent surveillance pipeline.

| From                   | To                       |
| ---------------------- | ------------------------ |
| 🎥 Raw video           | 📌 Structured events     |
| 🧠 Object detection    | 🛰️ Persistent tracking  |
| 📹 Camera feeds        | 🚧 Rule-aware monitoring |
| 🔍 Isolated detections | 🚨 Incident generation   |
| 📊 Static information  | 📡 Realtime intelligence |

> **KAVRON transforms visual data into actionable intelligence.**

---

## 📌 Project Status

<div align="center">

### 🟢 Active Development

**AI Detection · Tracking · Incident Intelligence · Realtime Monitoring**

</div>

---

## 🎥 KAVRON in Action

<div align="center">

### Live System Demo

https://github.com/Siddarth-S-V/KAVRON/raw/main/assets/KAVRON%20Demo.mp4

<br>

**Real-time Detection · Object Tracking · AI Analytics · Alerts · Monitoring**

</div>

> **Note:** GitHub may not render repository-hosted MP4 files inline in every README view. If the player does not appear, open the video directly from the `assets` folder.

---

## 🧠 System Architecture

<div align="center">

![KAVRON Architecture](assets/KAVRON%20AI%20Surveillance%20Architecture.png)

</div>

### Processing Flow

```text
                    ┌─────────────────────┐
                    │ Camera / RTSP /     │
                    │ Recorded Video      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Camera Capture     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    AI Scheduler     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ YOLO + CV Models    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Detection Fusion   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Object Tracking    │
                    │      DeepSORT       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Rules & Fences    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Incidents & Alerts  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ REST API + WebSocket│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  KAVRON Dashboard   │
                    └─────────────────────┘
```

---

## ⚡ Core Capabilities

| Capability                  | Purpose                                      |
| --------------------------- | -------------------------------------------- |
| 🎥 **Video Ingestion**      | CCTV, RTSP and recorded video sources        |
| 🧠 **AI Detection**         | YOLO-based computer vision inference         |
| 🧩 **Detection Fusion**     | Combines outputs from multiple vision models |
| 🛰️ **Object Tracking**     | Maintains object identities across frames    |
| 🚧 **Virtual Fences**       | Detects boundary and rule violations         |
| 🚨 **Incident Engine**      | Converts events into structured incidents    |
| 📡 **Realtime Updates**     | WebSocket-based live communication           |
| 📊 **Monitoring Dashboard** | Centralized visualization and analytics      |

---

## 🔬 Computer Vision Stack

KAVRON follows a modular computer-vision architecture where different models can perform specialized tasks.

| Model / Tool  | Role                     |
| ------------- | ------------------------ |
| **YOLO**      | Object Detection         |
| **DeepSORT**  | Multi-Object Tracking    |
| **RTMPose**   | Pose Estimation          |
| **YuNet**     | Face Detection           |
| **SFace**     | Face Recognition         |
| **PaddleOCR** | OCR / Text Extraction    |
| **OpenCV**    | Image & Video Processing |

This modular approach makes it possible to extend KAVRON with additional specialist models without redesigning the complete processing pipeline.

---

## 🛠️ Technology Stack

<div align="center">

| Layer             | Technologies                                |
| ----------------- | ------------------------------------------- |
| **Frontend**      | React · TypeScript · Vite                   |
| **UI**            | Tailwind CSS · Framer Motion · Lucide React |
| **Visualization** | Recharts                                    |
| **Backend**       | FastAPI · Uvicorn · Pydantic                |
| **AI / Vision**   | YOLO · OpenCV                               |
| **Tracking**      | DeepSORT                                    |
| **Database**      | SQLite · SQLAlchemy                         |
| **Realtime**      | WebSockets                                  |
| **Testing**       | Pytest                                      |

</div>

---

## 🚀 Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Siddarth-S-V/KAVRON.git
cd KAVRON
```

---

### 2. Start the Backend

```bash
cd kavron_backend_complete

py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python run.py
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

### 3. Start the Frontend

Open another terminal:

```bash
cd Frontend

pnpm install
pnpm dev
```

Configure the API endpoint:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

The frontend will then be available through the Vite development server.

---

## 📡 API & Realtime Communication

KAVRON exposes structured REST APIs for managing and monitoring the surveillance pipeline.

### REST Endpoints

```text
GET /api/v1/overview
GET /api/v1/cameras
GET /api/v1/detections
GET /api/v1/tracks
GET /api/v1/alerts
GET /api/v1/incidents
GET /api/v1/fences
GET /api/v1/models
```

### WebSocket Channels

```text
/api/v1/ws/detections
/api/v1/ws/alerts
/api/v1/ws/camera_state
```

This enables the dashboard to receive live system events without continuously polling the backend.

---

## 🔐 Security

Never commit sensitive information to the repository.

```text
.env
API keys
Passwords
Camera credentials
Private infrastructure credentials
Production secrets
```

Use `.env.example` as the starting point for local configuration.

---

## 🧭 Future Direction

KAVRON is designed with extensibility in mind.

Potential directions include:

* Distributed camera processing
* Advanced video analytics
* Additional specialist AI models
* WebRTC / HLS video delivery
* Geospatial monitoring
* Rich notification systems
* Production-scale deployment
* Edge-based AI processing

---

## 👨‍💻 Built By

<div align="center">

### **Siddarth S V**

**B.E. Electronics & Communication Engineering**
**BS in Data Science and Applications**

<br>

[![GitHub](https://img.shields.io/badge/GitHub-Siddarth--S--V-181717?style=flat-square\&logo=github)](https://github.com/Siddarth-S-V)

</div>

---

## 📜 Copyright & Ownership

**© 2026 Siddarth S V. All Rights Reserved.**

KAVRON is an original project developed by **Siddarth S V**.

The source code, project architecture, documentation, original visual assets, and project-specific implementations are protected by applicable copyright laws unless otherwise stated.

Third-party libraries, frameworks, pretrained models, datasets, and external assets remain subject to their respective licenses and copyrights.

**No permission is granted to reproduce, redistribute, modify, or commercially use the original KAVRON project materials without prior written permission from the author, except where permitted by applicable third-party licenses.**

For third-party components, always refer to their respective licenses before redistribution or commercial deployment.

---

<div align="center">

# 🛰️ KAVRON

### **SEE THE FRAME. UNDERSTAND THE EVENT. ACT ON THE SIGNAL.**

**Detect · Track · Fuse · Alert · Visualize**

<br>

⭐ **If KAVRON is useful or interesting, consider starring the repository.**

<br>

**© 2026 Siddarth S V · KAVRON**

</div>
