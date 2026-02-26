import type { Telemetry } from "./types";

export async function fetchTelemetryStep(): Promise<Telemetry> {
  // Prefer env_step
  const envRes = await fetch("/api/telemetry/env_step", { cache: "no-store" });
  if (envRes.ok) return (await envRes.json()) as Telemetry;

  // Fall back to legacy step
  const legacyRes = await fetch("/api/telemetry/step", { cache: "no-store" });
  if (!legacyRes.ok) throw new Error(`API error ${envRes.status}/${legacyRes.status}`);
  return (await legacyRes.json()) as Telemetry;
}

export async function setAirflowObstruction(ratio: number) {
  const res = await fetch("/api/controls/airflow_obstruction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ratio }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<{ ok: true; obstruction_ratio: number }>;
}

export async function simulateFanFailure() {
  const res = await fetch("/api/controls/fan_failure", { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<{ ok: true; obstruction_ratio: number }>;
}

export async function resetAirflow() {
  const res = await fetch("/api/controls/reset_airflow", { method: "POST" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<{ ok: true; obstruction_ratio: number }>;
}