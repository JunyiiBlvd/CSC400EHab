"use client";

import {
  Box,
  Paper,
  Typography,
  Slider,
  Button,
  Stack,
  Chip,
  Tabs,
  Tab,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { useEffect, useMemo, useRef, useState } from "react";

import NodeGrid from "./components/NodeGrid";
import NodeGauges from "./components/NodeGauges";
import AlertsFeed from "./components/AlertsFeed";

import type {
  AlertItem,
  HistoryByNode,
  MlStatus,
  Telemetry,
  TelemetryByNode,
  UserProfile,
} from "./lib/types";
import {
  createProfile,
  fetchMlStatus,
  fetchProfiles,
  reloadMlModel,
  resetAirflow,
  setAirflowObstruction,
  simulateFanFailure,
  setHumidity,
  injectThermalSpike,
} from "./lib/api";

const NODE_IDS = ["node-1", "node-2", "node-3"] as const;
const MAX_POINTS = 300;

// ── History tab ──────────────────────────────────────────────────────────────

type AnomalyEvent = {
  id: number;
  seq_id: number;
  node_id: string;
  injection_timestamp: number | null;
  edge_detection_ts: number | null;
  central_detection_ts: number | null;
  edge_latency_ms: number | null;
  central_latency_ms: number | null;
  detection_source: string | null;
  bytes_edge: number | null;
  bytes_central: number | null;
};

type SummaryRow = {
  detection_source: string | null;
  sample_count: number;
  avg_edge_ms: number | null;
  avg_central_ms: number | null;
  avg_delta_ms: number | null;
  min_delta_ms: number | null;
  max_delta_ms: number | null;
};

function HistoryTab({ profileId }: { profileId: number | null }) {
  const [events, setEvents] = useState<AnomalyEvent[]>([]);
  const [summary, setSummary] = useState<SummaryRow | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  async function fetchEvents() {
    setLoading(true);
    setFetchError(null);
    try {
      if (profileId == null) {
        setEvents([]);
        setSummary(null);
        setLoading(false);
        return;
      }

      const [evRes, sumRes] = await Promise.all([
        fetch(
          `http://localhost:8000/db/history/events?profile_id=${profileId}`,
        ),
        fetch(
          `http://localhost:8000/db/anomaly_summary?profile_id=${profileId}`,
        ),
      ]);
      const evData = await evRes.json();
      const sumData = await sumRes.json();
      if (evData.ok) {
        setEvents(evData.events);
      } else {
        setFetchError(evData.error ?? "Failed to fetch events");
      }
      if (sumData.ok && sumData.summary.length > 0) {
        setSummary(sumData.summary[0]);
      } else {
        setSummary(null);
      }
    } catch (e: unknown) {
      setFetchError(e instanceof Error ? e.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (profileId == null) return;
    fetchEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId]);

  function fmtTs(ts: number | null): string {
    if (ts == null) return "—";
    return new Date(ts * 1000).toLocaleString();
  }

  function fmtMs(v: number | null): string {
    return v == null ? "—" : v.toFixed(1);
  }

  function fmtDelta(edge: number | null, central: number | null): string {
    return edge == null || central == null ? "—" : (central - edge).toFixed(1);
  }

  function fmtStat(v: number | null | undefined): string {
    return v == null ? "—" : v.toFixed(1) + " ms";
  }

  const statCards = [
    {
      label: "Total Events",
      value: summary ? String(summary.sample_count) : "—",
    },
    { label: "Avg Edge Latency", value: fmtStat(summary?.avg_edge_ms) },
    { label: "Avg Central Latency", value: fmtStat(summary?.avg_central_ms) },
    { label: "Avg Delta", value: fmtStat(summary?.avg_delta_ms) },
    { label: "Min Delta", value: fmtStat(summary?.min_delta_ms) },
    { label: "Max Delta", value: fmtStat(summary?.max_delta_ms) },
  ];

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Typography variant="h6">Anomaly Event History</Typography>
        <Button
          variant="outlined"
          onClick={fetchEvents}
          disabled={loading}
          size="small"
        >
          {loading ? "Loading..." : "Refresh"}
        </Button>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: 1.5,
          mb: 3,
        }}
      >
        {statCards.map(({ label, value }) => (
          <Paper key={label} sx={statCardStyle}>
            <Typography
              variant="caption"
              sx={{ opacity: 0.6, display: "block", mb: 0.75, lineHeight: 1.3 }}
            >
              {label}
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {value}
            </Typography>
          </Paper>
        ))}
      </Box>

      {fetchError && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {fetchError}
        </Typography>
      )}

      {!loading && events.length === 0 ? (
        <Box sx={{ textAlign: "center", mt: 10, opacity: 0.55 }}>
          <Typography variant="body1">
            No anomaly events recorded yet. Run a simulation and inject an
            anomaly to see history.
          </Typography>
        </Box>
      ) : (
        <TableContainer
          component={Paper}
          sx={{
            bgcolor: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={thStyle}>Node ID</TableCell>
                <TableCell sx={thStyle}>Detection Source</TableCell>
                <TableCell sx={thStyle}>Injection Time</TableCell>
                <TableCell sx={thStyle}>Edge Latency (ms)</TableCell>
                <TableCell sx={thStyle}>Central Latency (ms)</TableCell>
                <TableCell sx={thStyle}>Delta (ms)</TableCell>
                <TableCell sx={thStyle}>Bytes Edge</TableCell>
                <TableCell sx={thStyle}>Bytes Central</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {events.map((ev) => (
                <TableRow
                  key={ev.id}
                  sx={{ "&:hover": { bgcolor: "rgba(255,255,255,0.06)" } }}
                >
                  <TableCell sx={tdStyle}>{ev.node_id}</TableCell>
                  <TableCell sx={tdStyle}>
                    {ev.detection_source ?? "—"}
                  </TableCell>
                  <TableCell sx={tdStyle}>
                    {fmtTs(ev.injection_timestamp)}
                  </TableCell>
                  <TableCell sx={tdStyle}>
                    {fmtMs(ev.edge_latency_ms)}
                  </TableCell>
                  <TableCell sx={tdStyle}>
                    {fmtMs(ev.central_latency_ms)}
                  </TableCell>
                  <TableCell sx={tdStyle}>
                    {fmtDelta(ev.edge_latency_ms, ev.central_latency_ms)}
                  </TableCell>
                  <TableCell sx={tdStyle}>{ev.bytes_edge ?? "—"}</TableCell>
                  <TableCell sx={tdStyle}>{ev.bytes_central ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default function Home() {
  const [activeTab, setActiveTab] = useState(0);
  const [profiles, setProfiles] = useState<UserProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [profileDraft, setProfileDraft] = useState("");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [telemetryByNode, setTelemetryByNode] = useState<TelemetryByNode>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("node-1");
  const [historyByNode, setHistoryByNode] = useState<HistoryByNode>({});
  const [alertsByProfile, setAlertsByProfile] = useState<Record<number, AlertItem[]>>({});
  const [controlsError, setControlsError] = useState<string | null>(null);
  const [mlStatus, setMlStatus] = useState<MlStatus | null>(null);
  const [mlError, setMlError] = useState<string | null>(null);
  const [obstructionDraftByNode, setObstructionDraftByNode] = useState<
    Record<string, number>
  >({});
  const [humidityDraftByNode, setHumidityDraftByNode] = useState<
    Record<string, number>
  >({});
  const [draggingObstructionNodeId, setDraggingObstructionNodeId] = useState<
    string | null
  >(null);
  const [draggingHumidityNodeId, setDraggingHumidityNodeId] = useState<
    string | null
  >(null);
  const prevMlReady = useRef<boolean>(false);
  const draggingObstructionNodeIdRef = useRef<string | null>(null);
  const draggingHumidityNodeIdRef = useRef<string | null>(null);
  const prevAnomalyRef = useRef<Record<string, boolean>>({});
  const activeProfileIdRef = useRef<number | null>(null);

  const selectedTelemetry = telemetryByNode[selectedNodeId] ?? null;
  const alerts =
    activeProfileId != null ? (alertsByProfile[activeProfileId] ?? []) : [];

  // Keep ref in sync with state and reset per-node anomaly tracking on switch
  useEffect(() => {
    activeProfileIdRef.current = activeProfileId;
    prevAnomalyRef.current = {};
  }, [activeProfileId]);

  function addAlerts(newAlerts: AlertItem[]) {
    const pid = activeProfileIdRef.current;
    if (pid == null) return;
    setAlertsByProfile((prev) => {
      const existing = prev[pid] ?? [];
      return { ...prev, [pid]: [...newAlerts, ...existing].slice(0, 10) };
    });
  }

  useEffect(() => {
    let cancelled = false;

    async function loadProfiles() {
      try {
        const loaded = await fetchProfiles();
        if (cancelled) return;

        setProfiles(loaded);

        const savedProfileId = window.localStorage.getItem(
          "ehabitat-active-profile-id",
        );
        const parsedId = savedProfileId ? Number(savedProfileId) : NaN;

        const fallbackProfile = loaded[0] ?? null;
        const matchingProfile =
          loaded.find((profile) => profile.id === parsedId) ?? fallbackProfile;

        setActiveProfileId(matchingProfile ? matchingProfile.id : null);
        setProfileError(null);
      } catch (e: unknown) {
        if (!cancelled) {
          setProfileError(
            e instanceof Error ? e.message : "Failed to load profiles",
          );
        }
      }
    }

    loadProfiles();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (activeProfileId == null) return;
    window.localStorage.setItem(
      "ehabitat-active-profile-id",
      String(activeProfileId),
    );
  }, [activeProfileId]);

  function getAnomalyReason(telemetry: Telemetry) {
    const reasons: string[] = [];

    if (telemetry.cpu_load > 0.85) {
      reasons.push(
        "CPU elevated (" + (telemetry.cpu_load * 100).toFixed(0) + "%)",
      );
    }

    if (telemetry.temperature > 21.5) {
      reasons.push(
        "Temperature rising (" + telemetry.temperature.toFixed(2) + "°C)",
      );
    }

    if (telemetry.airflow < 1.5 && telemetry.airflow > 0.1) {
      reasons.push(
        "Airflow degraded (" + telemetry.airflow.toFixed(2) + " units)",
      );
    }

    if (telemetry.airflow <= 0.1) {
      reasons.push("Airflow critical — possible HVAC failure");
    }

    if (telemetry.humidity > 55) {
      reasons.push(
        "Humidity elevated (" + telemetry.humidity.toFixed(1) + "%)",
      );
    }

    if (reasons.length === 0) {
      reasons.push(
        "Subtle multi-signal pattern — no single threshold exceeded",
      );
    }

    return reasons.join(" · ");
  }

  useEffect(() => {
    let socket: WebSocket | null = null;
    let cancelled = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (activeProfileId == null) return;
      socket = new WebSocket(
        `ws://localhost:8000/ws/simulation?profile_id=${activeProfileId}`,
      );

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
            }),
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
  }, [activeProfileId]);

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

            addAlerts([alert]);
          }
          if (!s.window_ready) prevMlReady.current = false;
        }
      } catch (e: unknown) {
        if (!cancelled) {
          setMlError(
            e instanceof Error ? e.message : "Failed to load ML status",
          );
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
        const scoreStr =
          typeof telemetry.anomaly_score === "number"
            ? telemetry.anomaly_score.toFixed(4)
            : "N/A";
        newAlerts.push({
          id: "ml-anomaly-" + nodeId + "-" + telemetry.timestamp,
          ts: (() => {
            try {
              const d = new Date(Number(telemetry.timestamp) * 1000);
              return isNaN(d.getTime())
                ? new Date().toISOString()
                : d.toISOString();
            } catch {
              return new Date().toISOString();
            }
          })(),
          level: "crit",
          message:
            "ML Anomaly Detected on " +
            nodeId.toUpperCase() +
            " | Score: " +
            scoreStr +
            " | " +
            reason,
        });
      }

      prevAnomalyRef.current[nodeId] = isAnomaly;
    }

    if (newAlerts.length > 0) {
      addAlerts(newAlerts);
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
  const [centralStatus, setCentralStatus] = useState<
    Record<string, CentralNodeStatus>
  >({});

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
    obstructionDraftByNode[selectedNodeId] ??
    selectedTelemetry?.obstruction_ratio ??
    0;
  const selectedHumidityValue =
    humidityDraftByNode[selectedNodeId] ?? selectedTelemetry?.humidity ?? 45;

  const summaryText = useMemo(() => {
    if (apiError) return `Backend offline: ${apiError}`;
    const count = Object.keys(telemetryByNode).length;
    if (count === 0) return "Waiting for telemetry...";
    return `${count} nodes streaming`;
  }, [telemetryByNode, apiError]);

  async function handleCreateProfile() {
    const trimmed = profileDraft.trim();

    if (!trimmed) {
      setProfileError("Enter a profile name first");
      return;
    }

    try {
      setProfileError(null);
      const profile = await createProfile(trimmed);

      setProfiles((prev) =>
        [...prev, profile].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setActiveProfileId(profile.id);
      setProfileDraft("");
    } catch (e: unknown) {
      setProfileError(
        e instanceof Error ? e.message : "Failed to create profile",
      );
    }
  }

  async function applyObstruction(nodeId: string, ratio: number) {
    try {
      setControlsError(null);
      setObstructionDraftByNode((prev) => ({ ...prev, [nodeId]: ratio }));
      const res = await setAirflowObstruction(nodeId, ratio);
      setObstructionDraftByNode((prev) => ({
        ...prev,
        [nodeId]: res.obstruction_ratio,
      }));
    } catch (e: unknown) {
      setControlsError(
        e instanceof Error ? e.message : "Failed to update airflow obstruction",
      );
    } finally {
      draggingObstructionNodeIdRef.current = null;
      setDraggingObstructionNodeId(null);
    }
  }

  async function doFanFailure() {
    try {
      setControlsError(null);
      const res = await simulateFanFailure(selectedNodeId);
      setObstructionDraftByNode((prev) => ({
        ...prev,
        [selectedNodeId]: res.obstruction_ratio,
      }));
    } catch (e: unknown) {
      setControlsError(
        e instanceof Error ? e.message : "Failed to simulate fan failure",
      );
    }
  }

  async function doResetAirflow() {
    try {
      setControlsError(null);
      const res = await resetAirflow(selectedNodeId);
      setObstructionDraftByNode((prev) => ({
        ...prev,
        [selectedNodeId]: res.obstruction_ratio,
      }));
    } catch (e: unknown) {
      setControlsError(
        e instanceof Error ? e.message : "Failed to reset airflow",
      );
    }
  }

  async function applyHumidity(nodeId: string, humidity: number) {
    try {
      setControlsError(null);
      setHumidityDraftByNode((prev) => ({ ...prev, [nodeId]: humidity }));
      const res = await setHumidity(nodeId, humidity);
      setHumidityDraftByNode((prev) => ({ ...prev, [nodeId]: res.humidity }));
    } catch (e: unknown) {
      setControlsError(
        e instanceof Error ? e.message : "Failed to update humidity",
      );
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

      addAlerts([alertThermal]);
    } catch (e: unknown) {
      setControlsError(
        e instanceof Error ? e.message : "Failed to inject thermal spike",
      );
    }
  }

  async function doInjectCoolantLeak() {
    try {
      setControlsError(null);
      const params = new URLSearchParams({
        node_id: selectedNodeId,
        scenario: "coolant_leak",
      });
      const res = await fetch(
        `http://localhost:8000/simulation/inject?${params.toString()}`,
        { method: "POST" },
      );
      if (!res.ok) throw new Error(`API error ${res.status}`);

      const alertCoolant: AlertItem = {
        id: `coolant-leak-${selectedNodeId}-${Date.now()}`,
        ts: new Date().toISOString(),
        level: "warn" as const,
        message: `Coolant leak injected on ${selectedNodeId}`,
      };

      addAlerts([alertCoolant]);
    } catch (e: unknown) {
      setControlsError(
        e instanceof Error ? e.message : "Failed to inject coolant leak",
      );
    }
  }

  const activeProfile =
    profiles.find((profile) => profile.id === activeProfileId) ?? null;

  const anomalyChip =
    selectedTelemetry?.is_anomaly === true ? (
      <Chip label="ANOMALY" color="error" size="small" />
    ) : mlStatus?.window_ready ? (
      <Chip label="ML Ready" color="success" size="small" />
    ) : (
      <Chip label="ML Warming" color="warning" size="small" />
    );

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#0b1220", color: "white", p: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          E-Habitat Dashboard
        </Typography>
        {anomalyChip}
        <Typography variant="body2" sx={{ opacity: 0.75 }}>
          {summaryText}
        </Typography>
        <Chip
          label={
            activeProfile
              ? `Profile: ${activeProfile.name}`
              : "No profile selected"
          }
          variant="outlined"
          size="small"
          sx={{
            color: "#fff",
          }}
        />
      </Box>

      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v as number)}
        sx={tabsStyle}
      >
        <Tab label="Dashboard" />
        <Tab label="History" />
      </Tabs>

      {activeTab === 0 && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: "320px 1fr",
            gap: 2,
            mt: 2,
          }}
        >
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
                {apiError
                  ? "Disconnected"
                  : Object.keys(telemetryByNode).length
                    ? "Connected"
                    : "Connecting..."}
              </Typography>
            </Box>

            <Box sx={{ mt: 3 }}>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Active profile
              </Typography>

              <TextField
                select
                fullWidth
                size="small"
                value={activeProfileId ?? ""}
                onChange={(event) => {
                  const nextValue = Number(event.target.value);
                  setActiveProfileId(
                    Number.isNaN(nextValue) ? null : nextValue,
                  );
                }}
                sx={{
                  mt: 1,
                  "& .MuiOutlinedInput-root": {
                    color: "rgba(255,255,255,0.85)",
                  },
                  "& .MuiSvgIcon-root": {
                    color: "rgba(255,255,255,0.85)",
                  },
                }}
              >
                {profiles.map((profile) => (
                  <MenuItem key={profile.id} value={profile.id}>
                    {profile.name}
                  </MenuItem>
                ))}
              </TextField>

              <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                <TextField
                  label="New profile"
                  size="small"
                  fullWidth
                  value={profileDraft}
                  onChange={(event) => setProfileDraft(event.target.value)}
                  sx={{
                    "& .MuiInputLabel-root": {
                      color: "rgba(255,255,255,0.85)",
                    },
                    "& .MuiOutlinedInput-root": {
                      color: "rgba(255,255,255,0.85)",
                    },
                  }}
                />
                <Button variant="contained" onClick={handleCreateProfile}>
                  Add
                </Button>
              </Stack>

              {profileError && (
                <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                  {profileError}
                </Typography>
              )}
            </Box>

            <Box sx={{ mt: 3 }}>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Focus node
              </Typography>
              <Stack
                direction="row"
                spacing={1}
                sx={{ mt: 1, flexWrap: "wrap" }}
              >
                {NODE_IDS.map((nodeId) => (
                  <Button
                    key={nodeId}
                    variant={
                      selectedNodeId === nodeId ? "contained" : "outlined"
                    }
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
                  setObstructionDraftByNode((prev) => ({
                    ...prev,
                    [selectedNodeId]: v as number,
                  }));
                }}
                onChangeCommitted={(_, v) =>
                  applyObstruction(selectedNodeId, v as number)
                }
                sx={{ mt: 1 }}
              />
              <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.8 }}>
                {selectedObstructionValue.toFixed(2)} on {selectedNodeId}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Button variant="contained" onClick={doFanFailure}>
                  Fan failure
                </Button>
                <Button variant="outlined" onClick={doResetAirflow}>
                  Reset airflow
                </Button>
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
                  setHumidityDraftByNode((prev) => ({
                    ...prev,
                    [selectedNodeId]: v as number,
                  }));
                }}
                onChangeCommitted={(_, v) =>
                  applyHumidity(selectedNodeId, v as number)
                }
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

            <Box
              sx={{ mt: 3, display: "flex", flexDirection: "column", gap: 1 }}
            >
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Anomalies
              </Typography>
              <Button
                variant="contained"
                color="warning"
                onClick={doThermalSpike}
              >
                Inject Thermal Spike
              </Button>
              <Button
                variant="contained"
                sx={{ bgcolor: "#3b82f6" }}
                onClick={doInjectCoolantLeak}
              >
                Inject Coolant Leak
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
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: 2,
                }}
              >
                {NODE_IDS.map((nodeId) => {
                  const s = centralStatus[nodeId];
                  const fmt = (v: number | null | undefined, unit: string) =>
                    v == null
                      ? "Waiting for anomaly..."
                      : `${v.toFixed(2)} ${unit}`;
                  const bwRatio =
                    s?.bytes_edge != null &&
                    s.bytes_edge > 0 &&
                    s?.bytes_central != null
                      ? ((s.bytes_central / s.bytes_edge) * 100).toFixed(1) +
                        "%"
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
                      <Typography
                        variant="subtitle2"
                        sx={{ mb: 1, opacity: 0.9, fontWeight: 700 }}
                      >
                        {nodeId.toUpperCase()}
                      </Typography>
                      <Stack spacing={0.5}>
                        <Typography variant="body2">
                          <span style={{ opacity: 0.6 }}>Edge latency: </span>
                          {fmt(s?.edge_latency_ms, "ms")}
                        </Typography>
                        <Typography variant="body2">
                          <span style={{ opacity: 0.6 }}>
                            Central latency:{" "}
                          </span>
                          {fmt(s?.central_latency_ms, "ms")}
                        </Typography>
                        <Typography variant="body2">
                          <span style={{ opacity: 0.6 }}>Latency delta: </span>
                          {fmt(s?.latency_delta_ms, "ms")}
                        </Typography>
                        <Typography variant="body2">
                          <span style={{ opacity: 0.6 }}>Bytes (edge): </span>
                          {s?.bytes_edge != null
                            ? `${s.bytes_edge} B`
                            : "Waiting for anomaly..."}
                        </Typography>
                        <Typography variant="body2">
                          <span style={{ opacity: 0.6 }}>
                            Bytes (central):{" "}
                          </span>
                          {s?.bytes_central != null
                            ? `${s.bytes_central} B`
                            : "Waiting for anomaly..."}
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
      )}

      {activeTab === 1 && (
        <Box sx={{ mt: 2 }}>
          <HistoryTab profileId={activeProfileId} />
        </Box>
      )}
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

const tabsStyle = {
  borderBottom: "1px solid rgba(255,255,255,0.12)",
  "& .MuiTab-root": {
    color: "rgba(255,255,255,0.6)",
    "&.Mui-selected": { color: "white" },
  },
  "& .MuiTabs-indicator": { backgroundColor: "#3b82f6" },
};

const thStyle = {
  color: "rgba(255,255,255,0.6)",
  borderBottom: "1px solid rgba(255,255,255,0.12)",
  fontWeight: 600,
  fontSize: "0.75rem",
  textTransform: "uppercase" as const,
  letterSpacing: "0.05em",
};

const tdStyle = {
  color: "rgba(255,255,255,0.87)",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
};

const statCardStyle = {
  p: 2,
  bgcolor: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 2,
  color: "white",
  textAlign: "center" as const,
};
