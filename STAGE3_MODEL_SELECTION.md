# Stage 3 Model Selection

KAVRON does **not** replace the proven Stage 2 YOLO11n model blindly.

## Default production path

- YOLO11n: primary person/vehicle detector.
- YOLO11n-pose: pose specialist.
- YuNet: face detection.
- SFace: optional face embeddings.
- LPD-YuNet: plate localization.
- PaddleOCR: plate text recognition.
- Stage 2 tracker + temporal behavior: identity and activity.

## Candidate upgrade path

The project includes a fetch script for official `yolo26n.pt`, `yolo11s.pt`, and
`yolo11s-pose.pt` candidates. We benchmark them against the existing models on
the actual target hardware before changing the default detector.

This matters because a newer model is not automatically better for the
hackathon's CPU/FPS/latency constraints. The final choice should use measured
latency, memory, throughput and accuracy on representative footage.
