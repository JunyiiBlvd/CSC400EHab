import type { MlStatus, Telemetry } from "./types";

export async function fetchTelemetryStep(): Promise<Telemetry> {
  // Prefer env_step
  const envRes = await fetch("/api/telemetry/env_step", { cache: "no-store" });
  if (envRes.ok) return (await envRes.json()) as Telemetry;

  // Fall back to legacy step (in case env_step breaks)
  const legacyRes = await fetch("/api/telemetry/step", { cache: "no-store" });
  if (!legacyRes.ok) throw new Error(`API error ${envRes.status}/${legacyRes.status}`);
  return (await legacyRes.json()) as Telemetry;
}

export async function setAirflowObstruction(
  ratio: number
): Promise<{ ok: true; obstruction_ratio: number }> {
  const res = await fetch("/api/controls/airflow_obstruction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ratio }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; obstruction_ratio: number };
}

export async function simulateFanFailure(): Promise<{ ok: true; obstruction_ratio: number }> {
  const res = await fetch("/api/controls/fan_failure", { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; obstruction_ratio: number };
}

export async function resetAirflow(): Promise<{ ok: true; obstruction_ratio: number }> {
  const res = await fetch("/api/controls/reset_airflow", { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return (await res.json()) as { ok: true; obstruction_ratio: number };
}

export async function fetchMlStatus(): Promise<MlStatus> {
  const res = await fetch("/api/ml/status", { cache: "no-store" });
  if (!res.ok) throw new Error(`ML status error ${res.status}`);
  return (await res.json()) as MlStatus;
}

export async function reloadMlModel(): Promise<{ ok: boolean; model_loaded: boolean; error?: string }> {
  const res = await fetch("/api/ml/reload", { method: "POST" });
  if (!res.ok) throw new Error(`ML reload error ${res.status}`);
  return (await res.json()) as { ok: boolean; model_loaded: boolean; error?: string };
}