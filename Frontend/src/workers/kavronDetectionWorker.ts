export type WorkerDetection = {
  camera_id?: string;
  class_id?: number;
  class_name?: string;
  confidence?: number;
  bbox?: number[] | { x1?: number; y1?: number; x2?: number; y2?: number; x?: number; y?: number; width?: number; height?: number };
  track_id?: string | number | null;
  frame_id?: number;
  timestamp?: number;
  image_width?: number;
  image_height?: number;
  keypoints?: any[];
  pose?: any[];
  landmarks?: any[];
  posture?: string;
  pose_confidence?: number;
};

type WorkerMessage =
  | { type: "event"; payload: any }
  | { type: "reset" };

const store: Record<string, WorkerDetection[]> = {};

function extract(payload: any): WorkerDetection[] {
  if (payload?.type === "detection") return [payload];
  if (payload?.type === "detections" && Array.isArray(payload.detections)) {
    return payload.detections;
  }
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.detections)) return payload.detections;
  return [];
}

function key(item: WorkerDetection): string {
  if (item.track_id != null) return `track:${item.track_id}`;
  return `object:${item.class_name || "unknown"}:${item.frame_id ?? ""}`;
}

function merge(cameraId: string, incoming: WorkerDetection[], replace: boolean) {
  if (replace) {
    store[cameraId] = incoming.slice(0, 64);
    return;
  }

  const merged = new Map<string, WorkerDetection>();
  for (const item of store[cameraId] || []) merged.set(key(item), item);
  for (const item of incoming) merged.set(key(item), item);
  store[cameraId] = Array.from(merged.values()).slice(-64);
}

let timer: number | undefined;

function publishSnapshot() {
  const snapshot: Record<string, WorkerDetection[]> = {};
  for (const [cameraId, items] of Object.entries(store)) {
    snapshot[cameraId] = items;
  }
  self.postMessage({ type: "snapshot", payload: snapshot });
}

self.onmessage = (event: MessageEvent<WorkerMessage>) => {
  const message = event.data;

  if (message.type === "reset") {
    for (const key of Object.keys(store)) delete store[key];
    return;
  }

  const payload = message.payload;
  if (!payload?.camera_id) return;

  const cameraId = String(payload.camera_id);
  const incoming = extract(payload).filter(Boolean);
  if (!incoming.length) return;

  merge(
    cameraId,
    incoming,
    payload.type === "detections" || Array.isArray(payload.detections),
  );
};

// 10 Hz UI snapshots. The worker absorbs high-frequency events while React
// only receives compact snapshots, reducing main-thread pressure.
timer = self.setInterval(publishSnapshot, 100);

self.onclose = () => {
  if (timer !== undefined) self.clearInterval(timer);
};
