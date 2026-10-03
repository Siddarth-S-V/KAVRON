# KAVRON Stage 2 — Performance + Tracking + Pose

## Implemented
- Fair newest-frame scheduler for multi-camera workloads.
- Configurable inference worker pool with bounded queues and drop-old-frame behavior.
- Per-model inference locks so shared Ultralytics models are safe while capture/post-processing remain concurrent.
- CPU oversubscription guard through `KAVRON_CPU_THREADS`.
- Persistent model instances; no per-frame model construction.
- General detection at `AI_FPS`, pose throttled independently with `POSE_INTERVAL`.
- Fast centroid tracking with motion prediction, EMA bounding-box smoothing, track aging and stable IDs.
- YOLO pose integration with 17-keypoint payloads.
- Lightweight posture classification: standing/sitting/lying.
- Pose/keypoint EMA smoothing.
- Frontend bounding-box interpolation and posture/track labels.
- Scheduler throughput/latency metrics exposed in `/api/v1/overview`.

## Recommended CPU settings
For a normal CPU-only hackathon laptop, start with:
- `INFERENCE_WORKERS=2`
- `AI_FPS=8`
- `POSE_INTERVAL=2`
- `MAX_QUEUE_SIZE=2`
- `SCHEDULER_QUEUE_SIZE=8`
- `KAVRON_CPU_THREADS=2` or `4`

If CPU usage stays near 100% with thermal throttling, reduce native threads before reducing camera FPS.
