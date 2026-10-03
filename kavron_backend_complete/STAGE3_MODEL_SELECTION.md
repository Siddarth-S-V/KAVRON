# Stage 3 Model Selection

### Default hot path
- YOLO11n: primary detector (kept as the compatibility/performance default).
- YOLO11n-Pose: primary pose model.
- YuNet 2023: face detection.
- LPD-YuNet: plate localization.
- PP-OCRv5 English mobile: local OCR model.
- Stage 2 tracker + posture + temporal behavior engine.

### Installed candidates
- YOLO26n
- YOLO26s
- RTMPose-S COCO 256x192
- YuNet 2026 candidate
- MobileFaceNet expression model

The candidates are deliberately not forced into the live path without a benchmark on the actual hardware and target footage. This avoids a hackathon demo becoming slower or less stable simply because a model is newer/larger.
