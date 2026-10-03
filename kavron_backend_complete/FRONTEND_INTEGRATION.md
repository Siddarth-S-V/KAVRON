# KAVRON Frontend Integration

The supplied React frontend can connect without a redesign.

## REST

Set:

`VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`

Useful calls:

- `GET /overview`
- `GET /cameras`
- `GET /detections`
- `GET /tracks`
- `GET /alerts`
- `GET /incidents`
- `GET /fences`
- `GET /models`
- `GET /system/metrics`

## WebSocket

Use:

`ws://127.0.0.1:8000/api/v1/ws/detections`

`ws://127.0.0.1:8000/api/v1/ws/alerts`

`ws://127.0.0.1:8000/api/v1/ws/camera_state`

Detection event shape:

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

## Video

The development MJPEG endpoint can be used directly in an `<img>` element for a first integration:

`/api/v1/cameras/{camera_id}/stream`

For a scalable deployment, keep video delivery separate from the AI event WebSocket. A production browser video path can later move to WebRTC/HLS without changing the AI event contracts.
