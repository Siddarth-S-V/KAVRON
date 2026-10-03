export interface Anomaly {
  id: number;
  anomaly_id: string;
  camera_id: string;
  track_id: string | null;
  anomaly_type: string;
  severity: string;
  message: string;
  confidence: number;
  bbox: number[];
  snapshot_path: string | null;
  metadata: Record<string, unknown>;
  acknowledged: boolean;
  created_at: string | null;
}

interface AnomalyResponse {
  items: Anomaly[];
  count: number;
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api/v1";

export async function getAnomalies(
  limit = 50,
): Promise<Anomaly[]> {

  const response = await fetch(
    `${API_BASE}/anomalies?limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load anomalies: ${response.status}`,
    );
  }

  const data =
    (await response.json()) as AnomalyResponse;

  return data.items;
}


export async function acknowledgeAnomaly(
  anomalyId: string,
): Promise<Anomaly> {

  const response = await fetch(
    `${API_BASE}/anomalies/${encodeURIComponent(
      anomalyId,
    )}/acknowledge`,
    {
      method: "PATCH",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to acknowledge anomaly: ${response.status}`,
    );
  }

  return response.json();
}