import type { MlStatus } from "./types";

const API_BASE = "http://localhost:8000";

export async function setAirflowObstruction(
  ratio: number
): Promise<{ ok: true; obstruction_ratio: number }> {
  const res = await fetch(`${API_BASE}/api/controls/airflow_obstruction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ratio }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; obstruction_ratio: number };
}

export async function simulateFanFailure(): Promise<{ ok: true; obstruction_ratio: number }> {
  const res = await fetch(`${API_BASE}/api/controls/fan_failure`, { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; obstruction_ratio: number };
}

export async function resetAirflow(): Promise<{ ok: true; obstruction_ratio: number }> {
  const res = await fetch(`${API_BASE}/api/controls/reset_airflow`, { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; obstruction_ratio: number };
}

export async function setHumidity(
  humidity: number
): Promise<{ ok: true; humidity: number }> {
  const res = await fetch(`${API_BASE}/api/controls/set_humidity`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ humidity }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; humidity: number };
}

export async function fetchMlStatus(): Promise<MlStatus> {
  const res = await fetch(`${API_BASE}/api/ml/status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`ML status error ${res.status}`);
  return (await res.json()) as MlStatus;
}

export async function reloadMlModel(): Promise<{ ok: boolean; model_loaded: boolean; error?: string }> {
  const res = await fetch(`${API_BASE}/api/ml/reload`, { method: "POST" });
  if (!res.ok) throw new Error(`ML reload error ${res.status}`);
  return (await res.json()) as { ok: boolean; model_loaded: boolean; error?: string };
}
