# KAVRON Stage 5 — Maps, Location + Final Integration

## Added
- Real OpenStreetMap interactive map.
- Browser location services with explicit permission.
- Camera latitude/longitude persistence.
- Camera placement by map click.
- Reverse geocoding for saved camera locations.
- Place search using Nominatim.
- Fifth supplied demo video (`user_demo_05.mp4`).
- Problem Statement 26187 model/capability audit.
- Night-time movement detection rule.
- Stage 5 status API.

## Map usage
The frontend requests normal visible tiles only. It displays OpenStreetMap attribution. Public Nominatim is throttled and cached; for production use a dedicated geocoding provider or self-hosted service.

## Location
Browser geolocation requires user permission and a secure context. `localhost` is treated as a trustworthy development origin by modern browsers. For a deployed site, use HTTPS.

## Camera mapping
1. Open Border Map.
2. Select a camera.
3. Click the real position on the map.
4. Click Place Selected Camera.
5. KAVRON reverse-geocodes the coordinate when available and persists the result.

## Stage 5 validation
`GET /api/v1/stage5/status` reports:
- model file presence
- ONNX runtime validity for specialist models
- problem statement capability coverage
- fine-tuning readiness
- map/location integration state

## Important truth
Fine-tuning is not claimed until reviewed labels exist. The training pipeline from Stage 4 remains available.

## Performance refinements
- AI inference cadence is independent from capture cadence.
- Camera queues remain bounded and newest-frame oriented.
- Browser JPEG encoding is capped by `stream_jpeg_fps` (default 12 FPS) instead of encoding every captured frame.
- Specialist models remain ROI-based and interval-throttled.
- Native CPU thread counts are capped to avoid oversubscription.
- Model wrappers are cached and reused.
