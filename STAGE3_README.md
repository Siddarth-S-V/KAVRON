# KAVRON Stage 3 — Multimodel Intelligence

This package is built directly on Stage 2.

## What changed

1. Added a model asset manager with atomic official-model downloads.
2. Added YuNet face detection and optional SFace embeddings.
3. Added LPD-YuNet license-plate detection and temporal OCR voting.
4. Added optional PaddleOCR/EasyOCR integration.
5. Added ROI-based specialist scheduling so face/ANPR never run on every full frame.
6. Added temporal behavior analysis for fall, rapid movement and loitering.
7. Loaded persisted virtual fences into the existing event engine at startup.
8. Unified face, plate, pose, posture and behavior fields in detection/track payloads.
9. Added Stage 3 model status/download API endpoints.
10. Updated the frontend overlay to display posture, plate text and behavior alerts.

## First setup on Windows

From `kavron_backend_complete`:

```powershell
python -m pip install -r requirements.txt
python scripts/download_models.py --all
# Optional OCR engine:
python -m pip install paddleocr
```

Optional Ultralytics candidates:

```powershell
python scripts/download_yolo_models.py
```

The backend can also auto-download the three OpenCV Zoo specialist weights in
the background when `auto_download_specialist_models=true`.

## Default strategy

- Primary detection: existing YOLO11n.
- Pose: existing YOLO11n-pose.
- Tracking: Stage 2 tracker.
- Face: YuNet on person ROIs every N inference frames.
- ANPR: LPD-YuNet on vehicle ROIs every N inference frames, then OCR only when a
  plate candidate exists.
- Behavior: temporal track/pose analysis.
- Virtual fence: geometry + track events.

This intentionally does not run every model on every frame.
