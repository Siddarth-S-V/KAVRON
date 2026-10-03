# KAVRON Stage 3 Model Pack

This Stage 3 package contains the core local binaries that were uploaded for this build, including YOLO26n/s, YuNet, LPD-YuNet, PP-OCRv5 English mobile recognition assets, and RTMPose-S config/checkpoint.

Optional specialist binaries can still be fetched atomically from official sources when explicitly requested:
- SFace face recognition
- any missing OpenCV Zoo specialist asset

The live hot path remains conservative: YOLO11n + YOLO11n-Pose + ROI specialists. YOLO26 and RTMPose are installed candidates for measured benchmarking before switching the default detector/pose engine.

## Local binary verification

`MODEL_MANIFEST.json` contains size and SHA-256 values for the packaged model files.

Run `python kavron_backend_complete/scripts/verify_stage3_pack.py` after extraction.
