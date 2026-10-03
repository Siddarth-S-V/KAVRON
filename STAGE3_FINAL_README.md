# KAVRON Stage 3 — Complete Multimodel Package

This package is built on the Stage 2 optimized project and adds the Stage 3 multimodel layer without replacing the existing tracking/event logic.

## Included local model assets

- YOLO11n + YOLO11n-Pose (existing Stage 2 models)
- YOLO26n and YOLO26s candidate detector weights
- YuNet face detector (`face_detection_yunet_2023mar.onnx`)
- newer YuNet candidate (`face_detection_yunet_2026may.onnx`)
- LPD-YuNet license-plate detector
- local PP-OCRv5 English mobile recognition model files
- RTMPose-S COCO 256x192 config + checkpoint (candidate/benchmark path)
- MobileFaceNet facial-expression model (optional asset)

## Stage 3 runtime

1. Person/vehicle detection uses the existing YOLO detector by default. YOLO26n/s are installed as local candidates and can be benchmarked before changing the default.
2. Byte/centroid-style tracking remains the CPU-first identity layer, with EMA bounding-box and keypoint smoothing, motion prediction, posture classification and temporal behavior events.
3. YuNet runs only on person ROIs and is independently throttled.
4. LPD-YuNet runs only on vehicle ROIs and is independently throttled.
5. PaddleOCR reads only the detected plate crop. The local PP-OCRv5 model is used when the PaddleOCR package supports a local recognition-model directory; otherwise the normal PaddleOCR model resolver is used, with EasyOCR as fallback.
6. Virtual-fence and anomaly/event logic remain database-backed and continue through the existing EventEngine.
7. The frontend receives compact detection/track events through the existing WebSocket and worker path.

## Important model notes

- SFace is not included as a binary because it was not uploaded in this turn. The existing atomic model manager can download the official SFace asset on demand if network access is available, and face embeddings remain disabled by default.
- RTMPose-S is included as a candidate. It is not forced into the default hot path because the MMPose/MMDetection runtime is a heavier dependency than YOLO pose. The existing YOLO11n-Pose model remains the reliable default; RTMPose can be benchmarked before switching.
- LPD-YuNet is a general license-plate detector and should be evaluated on the actual target-country footage before claiming production-grade ANPR accuracy.

## CPU/scalability changes

- Bounded newest-frame scheduling per camera.
- Per-model inference locks to prevent unsafe concurrent Ultralytics forwards.
- Native CPU thread guard to reduce oversubscription.
- Independent pose/face/ANPR throttles.
- ROI-only specialist inference.
- Bounded specialist executor.
- EMA smoothing and motion prediction for stable boxes/keypoints.
- Optional person-specialist detector disabled by default because the primary detector already returns person boxes; enable it only if benchmarking shows a measurable accuracy gain.

## Setup

```powershell
cd kavron_backend_complete
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Optional but recommended for Stage 3 ANPR:
pip install paddleocr
python run.py
```

If PaddleOCR is not installed, KAVRON falls back to EasyOCR if installed. Face detection and LPD-YuNet do not require an OCR package.

## Useful endpoints

- `GET /api/v1/models/stage3/status`
- `POST /api/v1/models/stage3/download`
- `GET /api/v1/models`
- `GET /api/v1/models/metadata`
- `GET /api/v1/system/metrics`
- `WS /api/v1/ws/events` (existing frontend event channel)

## Verification

Run:

```powershell
python scripts/verify_stage3_pack.py
pytest -q
```

The verification script checks model presence/size, required Python modules, ONNX readability, and the Stage 3 test suite.
