"use client";
import { Box, Paper, Typography, Slider, Button, Stack } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import NodeGrid from "./components/NodeGrid";
import NodeGauges from "./components/NodeGauges";
import AlertsFeed from "./components/AlertsFeed";

import type { Telemetry, AlertItem } from "./lib/types";
import { fetchTelemetryStep, setAirflowObstruction, simulateFanFailure, resetAirflow } from "./lib/api";

export default function Home() {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const MAX_POINTS = 300;
  const [history, setHistory] = useState<Telemetry[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  const [obstructionRatio, setObstructionRatio] = useState<number>(0);
  const [controlsError, setControlsError] = useState<string | null>(null);

  // Poll backend once per second
  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const data = await fetchTelemetryStep();

        if (!cancelled) {
          setTelemetry(data);
          setApiError(null);

          // keep slider in sync if backend reports it
          if (typeof data.obstruction_ratio === "number") {
            setObstructionRatio(data.obstruction_ratio);
          }

          setHistory((prev) => {
            const next = [...prev, data];
            if (next.length > MAX_POINTS) next.splice(0, next.length - MAX_POINTS);
            return next;
          });
        }
      } catch (err: any) {
        if (!cancelled) setApiError(err?.message ?? "Failed to reach backend");
      }
    }

    tick();
    const id = setInterval(tick, 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  // Alert generation (temp/cpu + humidity/airflow if present)
  useEffect(() => {
    if (!telemetry) return;

    const warnTemp = 24;
    const critTemp = 28;

    const warnHumidityHi = 70;
    const warnHumidityLo = 20;
    const warnAirflowLow = 0.25;

    setAlerts((prev) => {
      const next = [...prev];

      const push = (level: AlertItem["level"], message: string) => {
        next.unshift({
          id: `${telemetry.timestamp}-${level}-${message}`,
          ts: telemetry.timestamp,
          level,
          message,
        });
      };

      if (telemetry.temperature >= critTemp) {
        push("crit", `🔥 ${telemetry.node_id} temperature CRITICAL (${telemetry.temperature.toFixed(2)} °C)`);
      } else if (telemetry.temperature >= warnTemp) {
        push("warn", `⚠️ ${telemetry.node_id} temperature elevated (${telemetry.temperature.toFixed(2)} °C)`);
      }

      if (telemetry.cpu_load >= 0.9) {
        push("warn", `📈 ${telemetry.node_id} CPU high (${(telemetry.cpu_load * 100).toFixed(1)}%)`);
      }

      if (typeof telemetry.humidity === "number") {
        if (telemetry.humidity >= warnHumidityHi) {
          push("warn", `💧 ${telemetry.node_id} humidity high (${telemetry.humidity.toFixed(1)}%)`);
        } else if (telemetry.humidity <= warnHumidityLo) {
          push("warn", `🌵 ${telemetry.node_id} humidity low (${telemetry.humidity.toFixed(1)}%)`);
        }
      }

      if (typeof telemetry.airflow === "number" && telemetry.airflow <= warnAirflowLow) {
        push("crit", `🌀 ${telemetry.node_id} airflow LOW (${telemetry.airflow.toFixed(2)})`);
      }

      if (telemetry.is_anomaly === true) {
        push("crit", `🤖 ${telemetry.node_id} anomaly detected (score ${telemetry.anomaly_score ?? "?"})`);
      }

      return next.slice(0, 10);
    });
  }, [telemetry]);

  const node1Text = useMemo(() => {
    if (apiError) return `Backend offline: ${apiError}`;
    if (!telemetry) return "Waiting for telemetry...";

    const extras: string[] = [];
    if (typeof telemetry.humidity === "number") extras.push(`Hum: ${telemetry.humidity.toFixed(1)}%`);
    if (typeof telemetry.airflow === "number") extras.push(`Air: ${telemetry.airflow.toFixed(2)}`);

    return `Temp: ${telemetry.temperature.toFixed(2)} °C · CPU: ${(telemetry.cpu_load * 100).toFixed(1)}%${
      extras.length ? " · " + extras.join(" · ") : ""
    }`;
  }, [telemetry, apiError]);

  async function applyObstruction(ratio: number) {
    try {
      setControlsError(null);
      const res = await setAirflowObstruction(ratio);
      setObstructionRatio(res.obstruction_ratio);
    } catch (e: any) {
      setControlsError(e?.message ?? "Failed to update airflow obstruction");
    }
  }

  async function doFanFailure() {
    try {
      setControlsError(null);
      const res = await simulateFanFailure();
      setObstructionRatio(res.obstruction_ratio);
    } catch (e: any) {
      setControlsError(e?.message ?? "Failed to simulate fan failure");
    }
  }

  async function doResetAirflow() {
    try {
      setControlsError(null);
      const res = await resetAirflow();
      setObstructionRatio(res.obstruction_ratio);
    } catch (e: any) {
      setControlsError(e?.message ?? "Failed to reset airflow");
    }
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#0b1220", color: "white", p: 3 }}>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 3 }}>
        E-Habitat Dashboard
      </Typography>

      <Box sx={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 2 }}>
        <Paper sx={panelStyle}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Controls Panel
          </Typography>

          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            Start/Stop simulation, configure thresholds, inject anomalies.
          </Typography>

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              API status
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {apiError ? "❌ Disconnected" : telemetry ? "✅ Connected" : "⏳ Connecting..."}
            </Typography>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Airflow obstruction (0 = none, 1 = fully blocked)
            </Typography>

            <Slider
              value={obstructionRatio}
              min={0}
              max={1}
              step={0.05}
              onChange={(_, v) => setObstructionRatio(v as number)}
              onChangeCommitted={(_, v) => applyObstruction(v as number)}
              sx={{ mt: 1 }}
            />

            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Button variant="contained" onClick={doFanFailure}>
                Fan failure
              </Button>
              <Button variant="outlined" onClick={doResetAirflow}>
                Reset airflow
              </Button>
            </Stack>

            {controlsError && (
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.85 }}>
                ⚠️ {controlsError}
              </Typography>
            )}
          </Box>
        </Paper>

        <Box sx={{ display: "grid", gap: 2 }}>
          {telemetry && (
            <NodeGauges
              temperature={telemetry.temperature}
              cpuLoad={telemetry.cpu_load}
              humidity={telemetry.humidity}
              airflow={telemetry.airflow}
              nodeId={telemetry.node_id}
            />
          )}

          <AlertsFeed alerts={alerts} />

          <Paper sx={panelStyle}>
            <Typography variant="h6">Central vs Edge Comparison</Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Latency + message volume metrics go here.
            </Typography>
          </Paper>

          <NodeGrid telemetry={telemetry} apiError={apiError} node1Text={node1Text} history={history} />
        </Box>
      </Box>
    </Box>
  );
}

const panelStyle = {
  p: 2,
  borderRadius: 3,
  bgcolor: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.12)",
  color: "white",
};