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

  const selectedTelemetry = telemetryByNode[selectedNodeId] ?? null;

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
    const telemetryList = Object.values(telemetryByNode);
    if (telemetryList.length === 0) return;

    setAlerts((prev) => {
      const next = [...prev];
      const push = (telemetry: Telemetry, level: AlertItem["level"], message: string) => {
        next.unshift({
          id: `${telemetry.timestamp}-${level}-${message}`,
          ts: telemetry.timestamp,
          level,
          message,
        });
      };

      for (const telemetry of telemetryList) {
        if (telemetry.temperature >= 28) {
          push(telemetry, "crit", `${telemetry.node_id} temperature CRITICAL (${telemetry.temperature.toFixed(2)} °C)`);
        } else if (telemetry.temperature >= 24) {
          push(telemetry, "warn", `${telemetry.node_id} temperature elevated (${telemetry.temperature.toFixed(2)} °C)`);
        }

        if (telemetry.cpu_load >= 0.9) {
          push(telemetry, "warn", `${telemetry.node_id} CPU high (${(telemetry.cpu_load * 100).toFixed(1)}%)`);
        }

        if (telemetry.humidity >= 70) {
          push(telemetry, "warn", `${telemetry.node_id} humidity high (${telemetry.humidity.toFixed(1)}%)`);
        } else if (telemetry.humidity <= 20) {
          push(telemetry, "warn", `${telemetry.node_id} humidity low (${telemetry.humidity.toFixed(1)}%)`);
        }

        if (telemetry.airflow <= 0.25) {
          push(telemetry, "crit", `${telemetry.node_id} airflow LOW (${telemetry.airflow.toFixed(2)})`);
        }

        if (telemetry.is_anomaly === true) {
          push(
            telemetry,
            "crit",
            `${telemetry.node_id} anomaly detected (score ${
              typeof telemetry.anomaly_score === "number" ? telemetry.anomaly_score.toFixed(3) : "?"
            })`
          );
        }
      }

      return next.slice(0, 10);
    });
  }, [telemetryByNode]);

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
            <Typography variant="h6">Central vs Edge Comparison</Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Placeholder for latency + message volume metrics.
            </Typography>
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
