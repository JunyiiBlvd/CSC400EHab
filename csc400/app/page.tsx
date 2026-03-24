"use client";

import { Box, Paper, Typography, Slider, Button, Stack, Chip } from "@mui/material";
import { useEffect, useMemo, useRef, useState } from "react";

import NodeGrid from "./components/NodeGrid";
import NodeGauges from "./components/NodeGauges";
import AlertsFeed from "./components/AlertsFeed";

import type { AlertItem, HistoryByNode, MlStatus, Telemetry, TelemetryByNode } from "./lib/types";
import {
  fetchMlStatus,
  reloadMlModel,
  resetAirflow,
  setAirflowObstruction,
  simulateFanFailure,
  setHumidity,
  injectThermalSpike,
} from "./lib/api";

const NODE_IDS = ["node-1", "node-2", "node-3"] as const;
const MAX_POINTS = 300;

export default function Home() {
  const [telemetryByNode, setTelemetryByNode] = useState<TelemetryByNode>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("node-1");
  const [historyByNode, setHistoryByNode] = useState<HistoryByNode>({});
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [controlsError, setControlsError] = useState<string | null>(null);
  const [mlStatus, setMlStatus] = useState<MlStatus | null>(null);
  const [mlError, setMlError] = useState<string | null>(null);
  const [obstructionDraftByNode, setObstructionDraftByNode] = useState<Record<string, number>>({});
  const [humidityDraftByNode, setHumidityDraftByNode] = useState<Record<string, number>>({});
  const [draggingObstructionNodeId, setDraggingObstructionNodeId] = useState<string | null>(null);
  const [draggingHumidityNodeId, setDraggingHumidityNodeId] = useState<string | null>(null);
  const prevMlReady = useRef<boolean>(false);
  const draggingObstructionNodeIdRef = useRef<string | null>(null);
  const draggingHumidityNodeIdRef = useRef<string | null>(null);
  const prevAnomalyRef = useRef<Record<string, boolean>>({});

  const selectedTelemetry = telemetryByNode[selectedNodeId] ?? null;

  function getAnomalyReason(telemetry: Telemetry) {
    const reasons: string[] = [];

    if (telemetry.cpu_load > 0.85) {
      reasons.push("CPU elevated (" + (telemetry.cpu_load * 100).toFixed(0) + "%)");
    }

    if (telemetry.temperature > 21.5) {
      reasons.push("Temperature rising (" + telemetry.temperature.toFixed(2) + "°C)");
    }

    if (telemetry.airflow < 1.5 && telemetry.airflow > 0.1) {
      reasons.push("Airflow degraded (" + telemetry.airflow.toFixed(2) + " units)");
    }

    if (telemetry.airflow <= 0.1) {
      reasons.push("Airflow critical — possible HVAC failure");
    }

    if (telemetry.humidity > 55) {
      reasons.push("Humidity elevated (" + telemetry.humidity.toFixed(1) + "%)");
    }

    if (reasons.length === 0) {
      reasons.push("Subtle multi-signal pattern — no single threshold exceeded");
    }

    return reasons.join(" · ");
  }

  useEffect(() => {
    let socket: WebSocket | null = null;
    let cancelled = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      socket = new WebSocket("ws://localhost:8000/ws/simulation");

      socket.onopen = () => {
        if (!cancelled) setApiError(null);
      };

      socket.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data) as Record<string, Telemetry>;
          if (cancelled) return;

          const normalizedFrame = Object.fromEntries(
            Object.entries(frame).map(([nodeId, data]) => {
              const ts =
                typeof data.timestamp === "number"
                  ? new Date(data.timestamp * 1000).toISOString()
                  : data.timestamp;

              return [
                nodeId,
                {
                  ...data,
                  node_id: nodeId,
                  timestamp: ts,
                },
              ];
            })
          ) as TelemetryByNode;

          setTelemetryByNode(normalizedFrame);
          setApiError(null);

          setObstructionDraftByNode((prev) => {
            const next = { ...prev };
            for (const [nodeId, data] of Object.entries(normalizedFrame)) {
              if (draggingObstructionNodeIdRef.current !== nodeId) {
                next[nodeId] = data.obstruction_ratio;
              }
            }
            return next;
          });

          setHumidityDraftByNode((prev) => {
            const next = { ...prev };
            for (const [nodeId, data] of Object.entries(normalizedFrame)) {
              if (draggingHumidityNodeIdRef.current !== nodeId) {
                next[nodeId] = data.humidity;
              }
            }
            return next;
          });

          setHistoryByNode((prev) => {
            const next: HistoryByNode = { ...prev };
            for (const [nodeId, data] of Object.entries(normalizedFrame)) {
              const existing = next[nodeId] ?? [];
              const updated = [...existing, data];
              if (updated.length > MAX_POINTS) {
                updated.splice(0, updated.length - MAX_POINTS);
              }
              next[nodeId] = updated;
            }
            return next;
          });
        } catch (err) {
          console.error("Bad WS payload", err);
        }
      };

      socket.onerror = () => {
        if (!cancelled) setApiError("WebSocket connection error");
      };

      socket.onclose = () => {
        if (!cancelled) {
          setApiError("WebSocket disconnected");
          reconnectTimer = setTimeout(connect, 2000);
        }
      };
    }

    connect();
    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function tickMl() {
      try {
        const s = await fetchMlStatus();
        if (!cancelled) {
          setMlStatus(s);
          setMlError(null);

          if (!prevMlReady.current && s.window_ready) {
            prevMlReady.current = true;

            const alert: AlertItem = {
              id: `ml-ready-${Date.now()}`,
              ts: new Date().toISOString(),
              level: "info",
              message: `ML window ready (${s.points_in_window}/${s.window_size}). Anomaly scoring active.`,
            };

            setAlerts((prev) => [alert, ...prev].slice(0, 10));
          }
          if (!s.window_ready) prevMlReady.current = false;
        }
      } catch (e: unknown) {
        if (!cancelled) {
          setMlError(e instanceof Error ? e.message : "Failed to load ML status");
        }
      }
    }

    tickMl();
    const id = setInterval(tickMl, 3000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    const telemetryEntries = Object.entries(telemetryByNode);
    if (telemetryEntries.length === 0) return;

    const newAlerts: AlertItem[] = [];

    for (const [nodeId, telemetry] of telemetryEntries) {
      const wasAnomaly = prevAnomalyRef.current[nodeId] ?? false;
      const isAnomaly = telemetry.is_anomaly === true;

      if (!wasAnomaly && isAnomaly) {
        const reason = getAnomalyReason(telemetry);
        const scoreStr = typeof telemetry.anomaly_score === 'number'
          ? telemetry.anomaly_score.toFixed(4) : 'N/A';
        newAlerts.push({
          id: 'ml-anomaly-' + nodeId + '-' + telemetry.timestamp,
          ts: (() => {
            try {
              const d = new Date(Number(telemetry.timestamp) * 1000);
              return isNaN(d.getTime()) ? new Date().toISOString() : d.toISOString();
            } catch {
              return new Date().toISOString();
            }
          })(),
          level: 'crit',
          message: 'ML Anomaly Detected on ' + nodeId.toUpperCase() +
                   ' | Score: ' + scoreStr + ' | ' + reason,
        });
      }

      prevAnomalyRef.current[nodeId] = isAnomaly;
    }

    if (newAlerts.length > 0) {
      setAlerts((prev) => [...newAlerts, ...prev].slice(0, 10));
    }
  }, [telemetryByNode]);

  // Central vs Edge comparison state
  type CentralNodeStatus = {
    edge_latency_ms: number | null;
    central_latency_ms: number | null;
    latency_delta_ms: number | null;
    bytes_edge: number | null;
    bytes_central: number | null;
    last_updated: number | null;
  };
  const [centralStatus, setCentralStatus] = useState<Record<string, CentralNodeStatus>>({});

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const res = await fetch("http://localhost:8000/central/status");
        const data = await res.json();
        if (!cancelled && data.ok) setCentralStatus(data.nodes);
      } catch {
        // backend offline — silently ignore, keep last value
      }
    }
    poll();
    const id = setInterval(poll, 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const selectedObstructionValue =
    obstructionDraftByNode[selectedNodeId] ?? selectedTelemetry?.obstruction_ratio ?? 0;
  const selectedHumidityValue = humidityDraftByNode[selectedNodeId] ?? selectedTelemetry?.humidity ?? 45;

  const summaryText = useMemo(() => {
    if (apiError) return `Backend offline: ${apiError}`;
    const count = Object.keys(telemetryByNode).length;
    if (count === 0) return "Waiting for telemetry...";
    return `${count} nodes streaming`;
  }, [telemetryByNode, apiError]);

  async function applyObstruction(nodeId: string, ratio: number) {
    try {
      setControlsError(null);
      setObstructionDraftByNode((prev) => ({ ...prev, [nodeId]: ratio }));
      const res = await setAirflowObstruction(nodeId, ratio);
      setObstructionDraftByNode((prev) => ({ ...prev, [nodeId]: res.obstruction_ratio }));
    } catch (e: unknown) {
      setControlsError(e instanceof Error ? e.message : "Failed to update airflow obstruction");
    } finally {
      draggingObstructionNodeIdRef.current = null;
      setDraggingObstructionNodeId(null);
    }
  }

  async function doFanFailure() {
    try {
      setControlsError(null);
      const res = await simulateFanFailure(selectedNodeId);
      setObstructionDraftByNode((prev) => ({ ...prev, [selectedNodeId]: res.obstruction_ratio }));
    } catch (e: unknown) {
      setControlsError(e instanceof Error ? e.message : "Failed to simulate fan failure");
    }
  }

  async function doResetAirflow() {
    try {
      setControlsError(null);
      const res = await resetAirflow(selectedNodeId);
      setObstructionDraftByNode((prev) => ({ ...prev, [selectedNodeId]: res.obstruction_ratio }));
    } catch (e: unknown) {
      setControlsError(e instanceof Error ? e.message : "Failed to reset airflow");
    }
  }

  async function applyHumidity(nodeId: string, humidity: number) {
    try {
      setControlsError(null);
      setHumidityDraftByNode((prev) => ({ ...prev, [nodeId]: humidity }));
      const res = await setHumidity(nodeId, humidity);
      setHumidityDraftByNode((prev) => ({ ...prev, [nodeId]: res.humidity }));
    } catch (e: unknown) {
      setControlsError(e instanceof Error ? e.message : "Failed to update humidity");
    } finally {
      draggingHumidityNodeIdRef.current = null;
      setDraggingHumidityNodeId(null);
    }
  }

  async function doReloadMl() {
    try {
      setMlError(null);
      const r = await reloadMlModel();
      if (!r.ok) setMlError(r.error ?? "Reload failed");
      const s = await fetchMlStatus();
      setMlStatus(s);
    } catch (e: unknown) {
      setMlError(e instanceof Error ? e.message : "Failed to reload ML model");
    }
  }

  async function doThermalSpike() {
    try {
      setControlsError(null);
      await injectThermalSpike(selectedNodeId);

      const alertThermal: AlertItem = {
        id: `thermal-spike-${selectedNodeId}-${Date.now()}`,
        ts: new Date().toISOString(),
        level: "warn" as const,
        message: `Thermal spike injected on ${selectedNodeId}`,
      };

      setAlerts((prev) => [alertThermal, ...prev].slice(0, 10));
    } catch (e: unknown) {
      setControlsError(e instanceof Error ? e.message : "Failed to inject thermal spike");
    }
  }

  const anomalyChip = selectedTelemetry?.is_anomaly === true ? (
    <Chip label="ANOMALY" color="error" size="small" />
  ) : mlStatus?.window_ready ? (
    <Chip label="ML Ready" color="success" size="small" />
  ) : (
    <Chip label="ML Warming" color="warning" size="small" />
  );

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#0b1220", color: "white", p: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          E-Habitat Dashboard
        </Typography>
        {anomalyChip}
        <Typography variant="body2" sx={{ opacity: 0.75 }}>
          {summaryText}
        </Typography>
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 2 }}>
        <Paper sx={panelStyle}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Controls Panel
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            Controls apply only to the currently selected node.
          </Typography>

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              API status
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {apiError ? "Disconnected" : Object.keys(telemetryByNode).length ? "Connected" : "Connecting..."}
            </Typography>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Focus node
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
              {NODE_IDS.map((nodeId) => (
                <Button
                  key={nodeId}
                  variant={selectedNodeId === nodeId ? "contained" : "outlined"}
                  onClick={() => setSelectedNodeId(nodeId)}
                >
                  {nodeId}
                </Button>
              ))}
            </Stack>
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Selected node: <strong>{selectedNodeId}</strong>
            </Typography>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Airflow obstruction (0 = none, 1 = fully blocked)
            </Typography>
            <Slider
              value={selectedObstructionValue}
              min={0}
              max={1}
              step={0.05}
              onChange={(_, v) => {
                setDraggingObstructionNodeId(selectedNodeId);
                draggingObstructionNodeIdRef.current = selectedNodeId;
                setObstructionDraftByNode((prev) => ({ ...prev, [selectedNodeId]: v as number }));
              }}
              onChangeCommitted={(_, v) => applyObstruction(selectedNodeId, v as number)}
              sx={{ mt: 1 }}
            />
            <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.8 }}>
              {selectedObstructionValue.toFixed(2)} on {selectedNodeId}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Button variant="contained" onClick={doFanFailure}>Fan failure</Button>
              <Button variant="outlined" onClick={doResetAirflow}>Reset airflow</Button>
            </Stack>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Humidity (%)
            </Typography>
            <Slider
              value={selectedHumidityValue}
              min={0}
              max={100}
              step={1}
              onChange={(_, v) => {
                setDraggingHumidityNodeId(selectedNodeId);
                draggingHumidityNodeIdRef.current = selectedNodeId;
                setHumidityDraftByNode((prev) => ({ ...prev, [selectedNodeId]: v as number }));
              }}
              onChangeCommitted={(_, v) => applyHumidity(selectedNodeId, v as number)}
              sx={{ mt: 1 }}
            />
            <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.8 }}>
              {selectedHumidityValue.toFixed(1)}% on {selectedNodeId}
            </Typography>
            {controlsError && (
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.85 }}>
                {controlsError}
              </Typography>
            )}
          </Box>

          <Box sx={{ mt: 3, display: "flex", flexDirection: "column", gap: 1 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Anomalies
            </Typography>
            <Button variant="contained" color="warning" onClick={doThermalSpike}>
              Inject Thermal Spike
            </Button>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              ML status
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {!mlStatus
                ? "Loading..."
                : mlStatus.model_loaded
                ? `Model loaded · window ${mlStatus.points_in_window}/${mlStatus.window_size}${
                    mlStatus.window_ready ? " · ready" : " · warming up"
                  }`
                : "Model not loaded"}
            </Typography>
            {mlStatus?.model_load_error && (
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.85 }}>
                {mlStatus.model_load_error}
              </Typography>
            )}
            {mlError && (
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.85 }}>
                {mlError}
              </Typography>
            )}
            <Button variant="outlined" onClick={doReloadMl} sx={{ mt: 1 }}>
              Reload ML model
            </Button>
          </Box>
        </Paper>

        <Box sx={{ display: "grid", gap: 2 }}>
          {selectedTelemetry && (
            <NodeGauges
              temperature={selectedTelemetry.temperature}
              cpuLoad={selectedTelemetry.cpu_load}
              humidity={selectedTelemetry.humidity}
              airflow={selectedTelemetry.airflow}
              isAnomaly={selectedTelemetry.is_anomaly === true}
              nodeId={selectedTelemetry.node_id}
            />
          )}

          <AlertsFeed alerts={alerts} />

          <Paper sx={panelStyle}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Central vs Edge Comparison
            </Typography>
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 2 }}>
              {NODE_IDS.map((nodeId) => {
                const s = centralStatus[nodeId];
                const fmt = (v: number | null | undefined, unit: string) =>
                  v == null ? "Waiting for anomaly..." : `${v.toFixed(2)} ${unit}`;
                const bwRatio =
                  s?.bytes_edge != null && s.bytes_edge > 0 && s?.bytes_central != null
                    ? ((s.bytes_central / s.bytes_edge) * 100).toFixed(1) + "%"
                    : "Waiting for anomaly...";
                return (
                  <Box
                    key={nodeId}
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.10)",
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ mb: 1, opacity: 0.9, fontWeight: 700 }}>
                      {nodeId.toUpperCase()}
                    </Typography>
                    <Stack spacing={0.5}>
                      <Typography variant="body2">
                        <span style={{ opacity: 0.6 }}>Edge latency: </span>
                        {fmt(s?.edge_latency_ms, "ms")}
                      </Typography>
                      <Typography variant="body2">
                        <span style={{ opacity: 0.6 }}>Central latency: </span>
                        {fmt(s?.central_latency_ms, "ms")}
                      </Typography>
                      <Typography variant="body2">
                        <span style={{ opacity: 0.6 }}>Latency delta: </span>
                        {fmt(s?.latency_delta_ms, "ms")}
                      </Typography>
                      <Typography variant="body2">
                        <span style={{ opacity: 0.6 }}>Bytes (edge): </span>
                        {s?.bytes_edge != null ? `${s.bytes_edge} B` : "Waiting for anomaly..."}
                      </Typography>
                      <Typography variant="body2">
                        <span style={{ opacity: 0.6 }}>Bytes (central): </span>
                        {s?.bytes_central != null ? `${s.bytes_central} B` : "Waiting for anomaly..."}
                      </Typography>
                      <Typography variant="body2">
                        <span style={{ opacity: 0.6 }}>BW ratio: </span>
                        {bwRatio}
                      </Typography>
                    </Stack>
                  </Box>
                );
              })}
            </Box>
          </Paper>

          <NodeGrid
            telemetryByNode={telemetryByNode}
            apiError={apiError}
            historyByNode={historyByNode}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
          />
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
