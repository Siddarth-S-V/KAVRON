# KAVRON Stage 4 Final Performance Notes

## Fixes in this revision
- Live camera API is available at `/api/v1/stage4/live-camera/toggle` and a compatibility alias is provided.
- Virtual fences can be edited by dragging polygon handles, enabled/disabled, saved, and deleted.
- JPEG encoding happens once per captured frame and is cached for all browser clients.
- General and pose YOLO adapter objects are cached instead of being instantiated on every frame.
- Bounded inference/specialist workers and newest-frame replacement remain in place.
- CPU native thread counts are capped through `KAVRON_CPU_THREADS`.

## Why this is faster without only adding threads
1. Avoid repeated model-wrapper construction.
2. Drop stale frames instead of building latency queues.
3. Encode each frame once instead of once per HTTP stream client.
4. Run specialist inference only on ROIs and at configured intervals.
5. Serialize each model's forward pass while allowing camera/other model families to progress concurrently.
6. Use temporal smoothing and voting instead of increasing inference frequency.
7. Keep camera reconnection backoff bounded and avoid CPU spin loops.
