import type { MlStatus } from "./types";

const API_BASE = "http://localhost:8000";

type NodeControlResponse = {
  ok: true;
  node_id: string;
};

export async function setAirflowObstruction(
  nodeId: string,
  ratio: number
): Promise<NodeControlResponse & { obstruction_ratio: number }> {
  const res = await fetch(`${API_BASE}/api/controls/airflow_obstruction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId, ratio }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as NodeControlResponse & { obstruction_ratio: number };
}

export async function simulateFanFailure(
  nodeId: string
): Promise<NodeControlResponse & { obstruction_ratio: number }> {
  const res = await fetch(`${API_BASE}/api/controls/fan_failure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as NodeControlResponse & { obstruction_ratio: number };
}

export async function resetAirflow(
  nodeId: string
): Promise<NodeControlResponse & { obstruction_ratio: number }> {
  const res = await fetch(`${API_BASE}/api/controls/reset_airflow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as NodeControlResponse & { obstruction_ratio: number };
}

export async function setHumidity(
  nodeId: string,
  humidity: number
): Promise<NodeControlResponse & { humidity: number }> {
  const res = await fetch(`${API_BASE}/api/controls/set_humidity`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId, humidity }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as NodeControlResponse & { humidity: number };
}

export async function fetchMlStatus(): Promise<MlStatus> {
  const res = await fetch(`${API_BASE}/api/ml/status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as MlStatus;
}

export async function reloadMlModel(): Promise<{
  ok: boolean;
  model_loaded: boolean;
  error?: string | null;
}> {
  const res = await fetch(`${API_BASE}/api/ml/reload`, { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: boolean; model_loaded: boolean; error?: string | null };
}

export async function injectThermalSpike(
  nodeId: string
): Promise<{ status: string; node: string; scenario: string }> {
  const params = new URLSearchParams({
    node_id: nodeId,
    scenario: "thermal_spike",
  });

  const res = await fetch(`${API_BASE}/simulation/inject?${params.toString()}`, {
    method: "POST",
  });

  if (!res.ok) throw new Error(`API error ${res.status}`);

  return (await res.json()) as { status: string; node: string; scenario: string };
}
