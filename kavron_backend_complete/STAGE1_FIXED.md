# KAVRON — Stage 1 Fixed Baseline

This package is the repaired baseline from the supplied project.

## Stage 1 fixes

- Fixed frontend `AnomalyFeed` prop contract (`compact`, `limit`) used by `App.tsx`.
- Added configurable frontend WebSocket path while preserving the existing `/ws/events` endpoint.
- Fixed camera runtime-state synchronization by wiring `state_callback` into camera workers and publishing live state changes.
- Hardened camera start/stop handling for missing camera IDs.
- Added `pytest.ini` so tests resolve the `app` package from the project root.
- Expanded documented CORS origins to include the supplied Vite port (`8443`).
- Kept the existing FastAPI, scheduler, registry, tracker, event engine, database and UI architecture intact.

## Verified in this environment

- Python syntax compilation: passed.
- Backend test suite: 2 passed.
- FastAPI root, health, cameras, overview, models and metrics endpoints: HTTP 200.
- Backend WebSocket `/ws/events`: connection accepted.
- Demo video camera start: live frames observed and camera state reported `online=true` with FPS.

## Frontend dependency note

The ZIP supplied by the user contains an incomplete/broken archived `node_modules` tree, so the browser production bundle was not falsely marked as verified from those archived dependencies. Run `npm install` or `pnpm install` in `Frontend/` before building.
