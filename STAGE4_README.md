# KAVRON Stage 4 — Product + Fine-Tuning

## Delivered
- Overview camera selector: switch between every available demo/live camera without leaving the Overview page.
- Overview intelligence table: Tracking, Number Plate, Person Detection and Posture columns.
- Live Camera switch: starts `CAM-LIVE-01` from Windows webcam index `0` through the FastAPI backend, so the same AI pipeline processes the feed.
- Virtual fence annotation: stored polygon fences are rendered over the selected feed and enforced by the backend event engine.
- AI Model Lab: shows installed/loaded/active model state and Stage 4 training readiness.
- Stage 4 fine-tuning gate: reproducible training + validation script with a promotion report.
- Four supplied videos are included alongside `demo1.mp4`, `demo2.mp4`, and `131232-749706873_medium.mp4`. The old `demo.mp4` is removed.

## Performance architecture
The live path keeps the Stage 2/3 bounded scheduler. Duplicate detector candidates are not run simultaneously. One production detector, pose model, ROI face/plate specialists, OCR and temporal behavior run with bounded queues and throttled specialist intervals. YOLO26 and RTMPose remain benchmark candidates until measured on the target machine.

## Fine-tuning truth
A truly fine-tuned model requires reviewed labels. This package contains the complete reproducible training/validation pipeline but does not pretend raw videos are ground truth. Put labeled images/labels into `kavron_backend_complete/training/dataset`, create `dataset.yaml`, then run `training/train_yolo_stage4.py`.

## Live camera
Windows camera permissions must allow the Python backend process to access the webcam. If another application owns the camera, the backend may report `Unable to open stream`.

## Fine-tuning commands

```powershell
cd kavron_backend_complete
python training/stage4_pipeline.py --component all
python training/train_yolo_stage4.py --model yolo11n.pt --data training/dataset.yaml --device cpu
```


## Stage 5
See `STAGE5_README.md` and `STAGE5_MODEL_AUDIT.md` for real maps, geolocation, fifth demo video and final capability audit.
