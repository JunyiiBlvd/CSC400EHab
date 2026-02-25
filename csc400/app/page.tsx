"use client";
import { Box, Paper, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import NodeGrid from "./components/NodeGrid";
import NodeGauges from "./components/NodeGauges";
import AlertsFeed from "./components/AlertsFeed";



type Telemetry = {
  node_id: string;
  timestamp: string;
  temperature: number;
  cpu_load: number;
};

export default function Home() {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  // Keep last 5 minutes (300 samples)
  const MAX_POINTS = 300;
  const [history, setHistory] = useState<Telemetry[]>([]);

  type AlertItem = {
    id: string;
    ts: string;
    level: "info" | "warn" | "crit";
    message: string;
  };

const [alerts, setAlerts] = useState<AlertItem[]>([]);



  // Poll backend once per second
  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const res = await fetch("/api/telemetry/step", { cache: "no-store" });
        if (!res.ok) throw new Error(`API error ${res.status}`);
        const data = (await res.json()) as Telemetry;

      if (!cancelled) {
        setTelemetry(data);
        setApiError(null);

        setHistory((prev) => {
          const next = [...prev, data];
          if (next.length > MAX_POINTS) {
            next.splice(0, next.length - MAX_POINTS);
          }
          return next;
        });
      }

      } catch (err: any) {
        if (!cancelled) {
          setApiError(err?.message ?? "Failed to reach backend");
        }
      }
    }

    // initial fetch immediately
    tick();

    const id = setInterval(tick, 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  // Alert generation
  useEffect(() => {
  if (!telemetry) return;

  const warnTemp = 24;
  const critTemp = 28;

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

    return next.slice(0, 10);
  });
}, [telemetry]);


  const node1Text = useMemo(() => {
    if (apiError) return `Backend offline: ${apiError}`;
    if (!telemetry) return "Waiting for telemetry...";
    return `Temp: ${telemetry.temperature.toFixed(2)} °C · CPU: ${(telemetry.cpu_load * 100).toFixed(1)}%`;
  }, [telemetry, apiError]);

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "#0b1220",
        color: "white",
        p: 3,
      }}
    >
      {/* Title */}
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 3 }}>
        E-Habitat Dashboard
      </Typography>

      {/* Main Layout */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "320px 1fr",
          gap: 2,
        }}
      >
        {/* Left Panel */}
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
        </Paper>

        {/* Right Panel */}
        <Box sx={{ display: "grid", gap: 2 }}>
          {telemetry && (
            <NodeGauges
              temperature={telemetry.temperature}
              cpuLoad={telemetry.cpu_load}
              nodeId={telemetry.node_id}
            />
          )}

          {/* Alerts */}
          <AlertsFeed alerts={alerts} />

          {/* Comparison */}
          <Paper sx={panelStyle}>
            <Typography variant="h6">Central vs Edge Comparison</Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Latency + message volume metrics go here.
            </Typography>
          </Paper>

          {/* Nodes */}
          <NodeGrid telemetry={telemetry} apiError={apiError} node1Text={node1Text} history={history} />

        </Box>
      </Box>
    </Box>
  );
}

/* Shared panel styling */
const panelStyle = {
  p: 2,
  borderRadius: 3,
  bgcolor: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.12)",
  color: "white",
};
