import { apiFetch } from "./api";

export interface Camera {
  camera_id: string;
  name?: string;
  location?: string;
  sector?: string;
  protocol?: string;
  resolution?: string;
  fps?: number;
  status?: string;
  ai_enabled?: boolean;
}

export function getCameras() {
  return apiFetch<Camera[]>("/api/v1/cameras");
}

export function startCamera(cameraId: string) {
  return apiFetch(`/api/v1/cameras/${cameraId}/start`, {
    method: "POST",
  });
}

export function stopCamera(cameraId: string) {
  return apiFetch(`/api/v1/cameras/${cameraId}/stop`, {
    method: "POST",
  });
}