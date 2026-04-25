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
import TopologyOverview from "./components/TopologyOverview";

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
  resetRuntime,
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

type InfoSlide = {
  title: string;
  body: string;
  emphasis: string;
  label?: string;
  diagram: string;
};

const INFO_SLIDES: readonly InfoSlide[] = [
  {
    title: "Virtual Server Room Simulation",
    body: "E-Habitat simulates a three-node server room environment with live thermal, humidity, airflow, and CPU telemetry. It runs two anomaly detection architectures simultaneously to compare their real-world tradeoffs.",
    emphasis: "Two architectures. One dataset. Live comparison.",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <circle cx="50" cy="38" r="16" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/><text x="50" y="41" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="500">N-1</text>
  <circle cx="140" cy="38" r="16" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/><text x="140" y="41" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="500">N-2</text>
  <circle cx="230" cy="38" r="16" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/><text x="230" y="41" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="500">N-3</text>
  <line x1="57" y1="52" x2="121" y2="74" stroke="#64748b" stroke-width=".9"/><line x1="140" y1="54" x2="140" y2="70" stroke="#64748b" stroke-width=".9"/><line x1="223" y1="52" x2="159" y2="74" stroke="#64748b" stroke-width=".9"/>
  <rect x="107" y="70" width="66" height="26" rx="5" fill="rgba(255,255,255,0.02)" stroke="#fbbf24" stroke-width="1.5"/>
  <text x="140" y="86" text-anchor="middle" font-size="8" fill="#fbbf24" font-family="sans-serif" font-weight="500">CENTRAL SERVER</text>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">3 sensor nodes · 1 server</tspan>
    <tspan x="140" dy="12">dual-path inference</tspan>
  </text>
</svg>`,
  },
  {
    title: "Three Independent Sensor Nodes",
    body: "NODE-1, NODE-2, and NODE-3 each run a full physics simulation — heat transfer, fan airflow, and humidity drift. Each node operates independently and streams data once per second.",
    label: "Edge",
    emphasis: "1 Hz telemetry per node",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <g>
    <circle cx="50" cy="68" r="16" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/><text x="50" y="71" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="500">NODE</text>
    <path d="M28,40 A24 24 0 0 1 72,40" fill="none" stroke="#22d3ee" stroke-width=".9" opacity=".45"/>
    <path d="M36,48 A16 16 0 0 1 64,48" fill="none" stroke="#22d3ee" stroke-width="1" opacity=".65"/>
    <path d="M43,56 A8 8 0 0 1 57,56" fill="none" stroke="#22d3ee" stroke-width="1.2" opacity=".9"/>
  </g>
  <g>
    <circle cx="140" cy="68" r="16" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/><text x="140" y="71" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="500">NODE</text>
    <path d="M118,40 A24 24 0 0 1 162,40" fill="none" stroke="#22d3ee" stroke-width=".9" opacity=".45"/>
    <path d="M126,48 A16 16 0 0 1 154,48" fill="none" stroke="#22d3ee" stroke-width="1" opacity=".65"/>
    <path d="M133,56 A8 8 0 0 1 147,56" fill="none" stroke="#22d3ee" stroke-width="1.2" opacity=".9"/>
  </g>
  <g>
    <circle cx="230" cy="68" r="16" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/><text x="230" y="71" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="500">NODE</text>
    <path d="M208,40 A24 24 0 0 1 252,40" fill="none" stroke="#22d3ee" stroke-width=".9" opacity=".45"/>
    <path d="M216,48 A16 16 0 0 1 244,48" fill="none" stroke="#22d3ee" stroke-width="1" opacity=".65"/>
    <path d="M223,56 A8 8 0 0 1 237,56" fill="none" stroke="#22d3ee" stroke-width="1.2" opacity=".9"/>
  </g>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">each node runs full physics</tspan>
    <tspan x="140" dy="12">no inter-node communication</tspan>
  </text>
</svg>`,
  },
  {
    title: "ML Runs at the Node",
    body: "Each node runs an Isolation Forest model locally before telemetry leaves. Anomaly scores are computed at the source — no round trip required.",
    label: "Edge",
    emphasis: "Score < 0.15 → anomaly flagged",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <circle cx="56" cy="50" r="28" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/>
  <text x="56" y="46" text-anchor="middle" font-size="9" fill="#22d3ee" font-family="sans-serif" font-weight="600">IF</text>
  <text x="56" y="58" text-anchor="middle" font-size="7" fill="#94a3b8" font-family="sans-serif">model</text>
  <line x1="84" y1="50" x2="130" y2="50" stroke="#64748b" stroke-width=".9"/>
  <text x="107" y="44" text-anchor="middle" font-size="7" fill="#64748b" font-family="sans-serif">score</text>
  <rect x="132" y="36" width="74" height="28" rx="5" fill="rgba(255,255,255,0.02)" stroke="#94a3b8" stroke-width=".8"/>
  <text x="169" y="51" text-anchor="middle" font-size="9" fill="#94a3b8" font-family="sans-serif">score: 0.11</text>
  <text x="169" y="61" text-anchor="middle" font-size="7" fill="#f87171" font-family="sans-serif">↓ anomalous</text>
  <line x1="206" y1="50" x2="238" y2="50" stroke="#f87171" stroke-width="1"/>
  <rect x="240" y="38" width="32" height="24" rx="5" fill="rgba(255,255,255,0.02)" stroke="#f87171" stroke-width="1.2"/>
  <text x="256" y="49" text-anchor="middle" font-size="7" fill="#f87171" font-family="sans-serif" font-weight="600">CRIT</text>
  <text x="256" y="59" text-anchor="middle" font-size="7" fill="#f87171" font-family="sans-serif">alert</text>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">inference runs locally</tspan>
    <tspan x="140" dy="12">score &lt; 0.15 flags anomaly</tspan>
  </text>
</svg>`,
  },
  {
    title: "Server Collects, Then Decides",
    body: "The central server receives raw telemetry from all three nodes and runs its own inference pass. Detection happens after the data travels — introducing measurable latency.",
    label: "Central",
    emphasis: "~258ms average detection lag",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <circle cx="28" cy="22" r="11" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.2"/><text x="28" y="25" text-anchor="middle" font-size="7" fill="#22d3ee" font-family="sans-serif">N1</text>
  <circle cx="28" cy="50" r="11" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.2"/><text x="28" y="53" text-anchor="middle" font-size="7" fill="#22d3ee" font-family="sans-serif">N2</text>
  <circle cx="28" cy="78" r="11" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.2"/><text x="28" y="81" text-anchor="middle" font-size="7" fill="#22d3ee" font-family="sans-serif">N3</text>
  <line x1="39" y1="22" x2="100" y2="48" stroke="#64748b" stroke-width=".7" stroke-dasharray="3 2"/>
  <line x1="39" y1="50" x2="100" y2="50" stroke="#64748b" stroke-width=".7" stroke-dasharray="3 2"/>
  <line x1="39" y1="78" x2="100" y2="52" stroke="#64748b" stroke-width=".7" stroke-dasharray="3 2"/>
  <text x="72" y="36" text-anchor="middle" font-size="7" fill="#64748b" font-family="sans-serif">raw</text>
  <circle cx="120" cy="50" r="20" fill="rgba(255,255,255,0.02)" stroke="#fbbf24" stroke-width="1.5"/>
  <text x="120" y="47" text-anchor="middle" font-size="7" fill="#fbbf24" font-family="sans-serif" font-weight="600">CENTRAL</text>
  <text x="120" y="57" text-anchor="middle" font-size="7" fill="#fbbf24" font-family="sans-serif">SERVER</text>
  <line x1="140" y1="50" x2="172" y2="50" stroke="#fbbf24" stroke-width="1"/>
  <rect x="174" y="36" width="60" height="28" rx="5" fill="rgba(255,255,255,0.02)" stroke="#fbbf24" stroke-width="1"/>
  <text x="204" y="48" text-anchor="middle" font-size="7" fill="#fbbf24" font-family="sans-serif">run</text>
  <text x="204" y="58" text-anchor="middle" font-size="7" fill="#fbbf24" font-family="sans-serif">inference</text>
  <line x1="234" y1="50" x2="256" y2="50" stroke="#f87171" stroke-width="1"/>
  <circle cx="264" cy="50" r="10" fill="rgba(255,255,255,0.02)" stroke="#f87171" stroke-width="1"/>
  <text x="264" y="53" text-anchor="middle" font-size="8" fill="#f87171" font-family="sans-serif">!</text>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">data travels first · server decides after</tspan>
    <tspan x="140" dy="12">latency cost</tspan>
  </text>
</svg>`,
  },
  {
    title: "Alerts on State Transitions",
    body: "Alerts fire only on a normal → anomalous transition, not on every anomalous frame. This prevents alert flooding during sustained failures and reflects real monitoring system design.",
    label: "Alerts",
    emphasis: "False → True transition only",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <rect x="14" y="30" width="84" height="38" rx="6" fill="rgba(255,255,255,0.02)" stroke="#4ade80" stroke-width="1.5"/>
  <text x="56" y="49" text-anchor="middle" font-size="9" fill="#4ade80" font-family="sans-serif" font-weight="600">NORMAL</text>
  <text x="56" y="61" text-anchor="middle" font-size="7" fill="#4ade80" font-family="sans-serif" opacity=".7">score ≥ 0.15</text>
  <line x1="98" y1="49" x2="162" y2="49" stroke="#64748b" stroke-width=".8" stroke-dasharray="4 2"/>
  <text x="130" y="40" text-anchor="middle" font-size="7" fill="#64748b" font-family="sans-serif">crossing</text>
  <rect x="112" y="44" width="36" height="10" rx="3" fill="rgba(255,255,255,0.02)" stroke="#f87171" stroke-width=".6"/>
  <text x="130" y="52" text-anchor="middle" font-size="6.5" fill="#f87171" font-family="sans-serif">fires once</text>
  <path d="M160,45 L166,49 L160,53" stroke="#64748b" stroke-width="1" fill="none" stroke-linecap="round"/>
  <rect x="168" y="30" width="96" height="38" rx="6" fill="rgba(255,255,255,0.02)" stroke="#f87171" stroke-width="1.5"/>
  <text x="216" y="49" text-anchor="middle" font-size="9" fill="#f87171" font-family="sans-serif" font-weight="600">ANOMALY</text>
  <text x="216" y="61" text-anchor="middle" font-size="7" fill="#f87171" font-family="sans-serif" opacity=".7">score &lt; 0.15</text>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">alert fires on false → true transition</tspan>
    <tspan x="140" dy="12">no flooding</tspan>
  </text>
</svg>`,
  },
  {
    title: "Inject Real Failure Scenarios",
    body: "Three scenarios can be triggered live: thermal spike, HVAC failure, and coolant leak. Each produces a distinct multi-signal pattern that the ML model was trained to detect.",
    label: "ML",
    emphasis: "Thermal · HVAC · Coolant",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <rect x="8" y="18" width="82" height="66" rx="6" fill="rgba(255,255,255,0.02)" stroke="#fb923c" stroke-width="1.5"/>
  <polygon points="49,28 63,52 35,52" fill="none" stroke="#fb923c" stroke-width="1.5" stroke-linejoin="round"/>
  <text x="49" y="62" text-anchor="middle" font-size="8" fill="#fb923c" font-family="sans-serif" font-weight="600">Thermal</text>
  <text x="49" y="74" text-anchor="middle" font-size="8" fill="#fb923c" font-family="sans-serif">Spike</text>
  <rect x="99" y="18" width="82" height="66" rx="6" fill="rgba(255,255,255,0.02)" stroke="#fbbf24" stroke-width="1.5"/>
  <line x1="126" y1="28" x2="154" y2="52" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="154" y1="28" x2="126" y2="52" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round"/>
  <circle cx="140" cy="40" r="14" fill="none" stroke="#fbbf24" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="140" y="62" text-anchor="middle" font-size="8" fill="#fbbf24" font-family="sans-serif" font-weight="600">HVAC</text>
  <text x="140" y="74" text-anchor="middle" font-size="8" fill="#fbbf24" font-family="sans-serif">Failure</text>
  <rect x="190" y="18" width="82" height="66" rx="6" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/>
  <path d="M231,26 C231,26 218,42 218,50 A13 13 0 0 0 244,50 C244,42 231,26 231,26 Z" fill="none" stroke="#22d3ee" stroke-width="1.5" stroke-linejoin="round"/>
  <text x="231" y="62" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif" font-weight="600">Coolant</text>
  <text x="231" y="74" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif">Leak</text>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">distinct multi-signal pattern per scenario</tspan>
    <tspan x="140" dy="12">ML detectable</tspan>
  </text>
</svg>`,
  },
  {
    title: "The Architectural Tradeoff",
    body: "Edge detects faster but transmits more data. Central uses roughly half the bandwidth but pays a latency penalty. Neither is strictly better — the right choice depends on the environment.",
    emphasis: "~48% bandwidth reduction, ~258ms cost",
    diagram: `<svg width="100%" viewBox="0 0 280 132">
  <line x1="140" y1="8" x2="140" y2="94" stroke="#64748b" stroke-width=".5" stroke-dasharray="4 3"/>
  <text x="70" y="16" text-anchor="middle" font-size="9" fill="#22d3ee" font-family="sans-serif" font-weight="600">EDGE</text>
  <circle cx="70" cy="50" r="22" fill="rgba(255,255,255,0.02)" stroke="#22d3ee" stroke-width="1.5"/>
  <text x="70" y="47" text-anchor="middle" font-size="7" fill="#22d3ee" font-family="sans-serif">infer</text>
  <text x="70" y="57" text-anchor="middle" font-size="7" fill="#22d3ee" font-family="sans-serif">locally</text>
  <text x="70" y="80" text-anchor="middle" font-size="8" fill="#22d3ee" font-family="sans-serif">faster detect</text>
  <text x="70" y="94" text-anchor="middle" font-size="8.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">full frame sent</text>
  <text x="210" y="16" text-anchor="middle" font-size="9" fill="#fbbf24" font-family="sans-serif" font-weight="600">CENTRAL</text>
  <rect x="178" y="32" width="64" height="36" rx="6" fill="rgba(255,255,255,0.02)" stroke="#fbbf24" stroke-width="1.5"/>
  <text x="210" y="49" text-anchor="middle" font-size="7" fill="#fbbf24" font-family="sans-serif">infer at</text>
  <text x="210" y="59" text-anchor="middle" font-size="7" fill="#fbbf24" font-family="sans-serif">server</text>
  <text x="210" y="80" text-anchor="middle" font-size="8" fill="#fbbf24" font-family="sans-serif">~258ms lag</text>
  <text x="210" y="94" text-anchor="middle" font-size="8.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">48% bandwidth</text>
  <text x="140" y="114" text-anchor="middle" font-size="11.5" fill="#cbd5e1" font-family="sans-serif" font-weight="600">
    <tspan x="140" dy="0">neither is strictly better</tspan>
    <tspan x="140" dy="12">tradeoff depends on environment</tspan>
  </text>
</svg>`,
  },
] as const;

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
  const [alertsByProfile, setAlertsByProfile] = useState<
    Record<number, AlertItem[]>
  >({});
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
  const [infoSlideIndex, setInfoSlideIndex] = useState(0);
  const [buttonFlash, setButtonFlash] = useState<{
    thermal: boolean;
    hvac: boolean;
    coolant: boolean;
  }>({
    thermal: false,
    hvac: false,
    coolant: false,
  });
  const prevMlReady = useRef<boolean>(false);
  const draggingObstructionNodeIdRef = useRef<string | null>(null);
  const draggingHumidityNodeIdRef = useRef<string | null>(null);
  const prevAnomalyRef = useRef<Record<string, boolean>>({});
  const lastAnomalyAlertTs = useRef<Record<string, number>>({});
  const activeProfileIdRef = useRef<number | null>(null);

  const selectedTelemetry = telemetryByNode[selectedNodeId] ?? null;
  const alerts =
    activeProfileId != null ? (alertsByProfile[activeProfileId] ?? []) : [];

  // Keep ref in sync with state and reset per-node anomaly tracking on switch
  useEffect(() => {
    activeProfileIdRef.current = activeProfileId;
    prevAnomalyRef.current = {};
    lastAnomalyAlertTs.current = {};
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

      const nowMs = Date.now();
      const lastAlertMs = lastAnomalyAlertTs.current[nodeId] ?? 0;
      const withinDebounce = nowMs - lastAlertMs < 60_000;

      if (!wasAnomaly && isAnomaly && !withinDebounce) {
        lastAnomalyAlertTs.current[nodeId] = nowMs;
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
            " ↓ anomalous | " +
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
    1;
  const selectedHumidityValue =
    humidityDraftByNode[selectedNodeId] ?? selectedTelemetry?.humidity ?? 45;
  const infoSlide = INFO_SLIDES[infoSlideIndex];

  function flashButton(key: "thermal" | "hvac" | "coolant") {
    setButtonFlash((prev) => ({ ...prev, [key]: true }));
    window.setTimeout(() => {
      setButtonFlash((prev) => ({ ...prev, [key]: false }));
    }, 220);
  }

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

      await resetRuntime();
      setHistoryByNode({});
      setTelemetryByNode({});

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

  async function handleProfileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const nextValue = Number(event.target.value);
    const nextProfileId = Number.isNaN(nextValue) ? null : nextValue;

    try {
      setProfileError(null);

      await resetRuntime();
      setHistoryByNode({});
      setTelemetryByNode({});

      setActiveProfileId(nextProfileId);
    } catch (e: unknown) {
      setProfileError(
        e instanceof Error ? e.message : "Failed to switch profile",
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
      flashButton("hvac");
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
      flashButton("thermal");
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
      flashButton("coolant");
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
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 2,
          mb: 2,
          flexWrap: "wrap",
        }}
      >
        <Box
          sx={{ display: "flex", alignItems: "center", gap: 2, minWidth: 0 }}
        >
          <Typography
            variant="h4"
            sx={{ fontWeight: 700, whiteSpace: "nowrap" }}
          >
            E-Habitat Dashboard
          </Typography>
          {anomalyChip}
          <Typography
            variant="body2"
            sx={{ opacity: 0.75, whiteSpace: "nowrap" }}
          >
            {summaryText}
          </Typography>
        </Box>

        <Box
          sx={{ display: "flex", alignItems: "center", gap: 2.5, ml: "auto" }}
        >
          <Tabs
            value={activeTab}
            onChange={(_, v) => setActiveTab(v as number)}
            sx={headerTabsStyle}
          >
            <Tab disableRipple label="Dashboard" />
            <Tab disableRipple label="History" />
          </Tabs>

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
      </Box>

      {activeTab === 0 && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: "320px 1fr",
            gap: 2,
            mt: 2,
          }}
        >
          <Paper
            sx={{ ...panelStyle, display: "flex", flexDirection: "column" }}
          >
            <Typography variant="h6" sx={{ mb: 1 }}>
              Controls Panel
            </Typography>

            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Active profile
              </Typography>
              <Typography
                variant="caption"
                sx={{ opacity: 0.5, display: "block" }}
              >
                Saved sensor parameter sets
              </Typography>

              <TextField
                select
                fullWidth
                size="small"
                value={activeProfileId ?? ""}
                onChange={handleProfileChange}
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
              <Typography
                variant="caption"
                sx={{ opacity: 0.5, display: "block" }}
              >
                Selects node shown in Live Gauges
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

            <Box sx={{ mt: 3 }}>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                  gap: 2,
                }}
              >
                <Box>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    Airflow obstruction
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
                </Box>

                <Box>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    Humidity
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
                </Box>
              </Box>

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
                sx={thermalButtonStyle(buttonFlash.thermal)}
                onClick={doThermalSpike}
              >
                Inject Thermal Spike
              </Button>
              <Button
                sx={warningGhostButtonStyle(buttonFlash.hvac)}
                onClick={doFanFailure}
              >
                HVAC Failure
              </Button>
              <Button
                sx={coolantButtonStyle(buttonFlash.coolant)}
                onClick={doInjectCoolantLeak}
              >
                Inject Coolant Leak
              </Button>
            </Box>

            <Paper sx={infoPanelStyle}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 1,
                  mb: 1.5,
                }}
              >
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Project Concepts
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.55 }}>
                  {infoSlideIndex + 1} / {INFO_SLIDES.length}
                </Typography>
              </Box>

              <Box
                sx={{
                  flex: 1,
                  minHeight: 178,
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                {infoSlide.label ? (
                  <Chip
                    label={infoSlide.label}
                    size="small"
                    sx={{
                      mb: 1.25,
                      color: "#cbd5e1",
                      bgcolor: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.10)",
                    }}
                  />
                ) : null}

                <Typography
                  variant="subtitle1"
                  sx={{ fontWeight: 700, lineHeight: 1.3 }}
                >
                  {infoSlide.title}
                </Typography>

                <Typography
                  variant="body2"
                  sx={{ mt: 1, opacity: 0.82, lineHeight: 1.65 }}
                >
                  {infoSlide.body}
                </Typography>

                <Typography
                  variant="body2"
                  sx={{
                    mt: 1.5,
                    color: "#93c5fd",
                    fontWeight: 600,
                    lineHeight: 1.5,
                  }}
                >
                  {infoSlide.emphasis}
                </Typography>

                <Box
                  sx={{
                    mt: 1.5,
                    pt: 1.5,
                    flex: 1,
                    borderTop: "1px solid rgba(255,255,255,0.10)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    "& svg": {
                      display: "block",
                      width: "100%",
                      maxWidth: "100%",
                      height: "100%",
                      maxHeight: "100%",
                    },
                  }}
                  dangerouslySetInnerHTML={{ __html: infoSlide.diagram }}
                />
              </Box>

              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 1,
                  mt: 1.5,
                }}
              >
                <Button
                  sx={slideArrowButtonStyle}
                  onClick={() =>
                    setInfoSlideIndex((prev) =>
                      prev === 0 ? INFO_SLIDES.length - 1 : prev - 1,
                    )
                  }
                >
                  ‹
                </Button>

                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 0.75,
                    flex: 1,
                  }}
                >
                  {INFO_SLIDES.map((_, index) => (
                    <Box
                      key={index}
                      sx={{
                        width: index === infoSlideIndex ? 18 : 6,
                        height: 6,
                        borderRadius: 999,
                        bgcolor:
                          index === infoSlideIndex
                            ? "rgba(147, 197, 253, 0.95)"
                            : "rgba(255,255,255,0.18)",
                        transition: "all 160ms ease",
                      }}
                    />
                  ))}
                </Box>

                <Button
                  sx={slideArrowButtonStyle}
                  onClick={() =>
                    setInfoSlideIndex((prev) => (prev + 1) % INFO_SLIDES.length)
                  }
                >
                  ›
                </Button>
              </Box>
            </Paper>
          </Paper>

          <Box sx={{ display: "grid", gap: 2 }}>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  xl: "minmax(0, 1fr) 320px",
                },
                gap: 2,
                alignItems: "stretch",
              }}
            >
              <Box sx={{ display: "grid", gap: 2, minWidth: 0 }}>
                <TopologyOverview
                  telemetryByNode={telemetryByNode}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={setSelectedNodeId}
                  centralStatus={centralStatus}
                />

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
              </Box>

              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  minHeight: { xl: "100%" },
                }}
              >
                <Box sx={{ flex: 1, minHeight: 0 }}>
                  <AlertsFeed alerts={alerts} fillHeight />
                </Box>

                <Paper sx={{ ...panelStyle, mt: 2 }}>
                  <Typography variant="h6" sx={{ mb: 1.5 }}>
                    ML Status
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
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
                  <Button
                    variant="outlined"
                    onClick={doReloadMl}
                    sx={{ mt: 1.5 }}
                  >
                    Reload ML model
                  </Button>
                </Paper>
              </Box>
            </Box>

            <Box>
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

const headerTabsStyle = {
  minHeight: 0,
  "& .MuiTabs-flexContainer": {
    gap: 0.5,
  },
  "& .MuiTab-root": {
    minHeight: 0,
    px: 1.25,
    py: 0.5,
    color: "rgba(255,255,255,0.62)",
    textTransform: "none" as const,
    fontWeight: 500,
    "&.Mui-selected": { color: "white" },
  },
  "& .MuiTabs-indicator": {
    backgroundColor: "#3b82f6",
    height: 2,
  },
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

const buttonBaseStyle = {
  borderRadius: "12px",
  px: 2,
  py: 1.1,
  fontWeight: 700,
  letterSpacing: "0.03em",
  textTransform: "none" as const,
  transition:
    "transform 120ms ease, box-shadow 160ms ease, background 160ms ease, border-color 160ms ease",
  "&:hover": {
    transform: "translateY(-1px)",
  },
  "&:active": {
    transform: "scale(0.97)",
  },
};

const thermalButtonStyle = (isFlashing: boolean) => ({
  ...buttonBaseStyle,
  color: "#fff",
  border: "1px solid rgba(249, 115, 22, 0.45)",
  background:
    "linear-gradient(135deg, rgba(249, 115, 22, 0.28), rgba(234, 88, 12, 0.22))",
  boxShadow: isFlashing
    ? "none"
    : "0 0 12px rgba(249, 115, 22, 0.28), inset 0 1px 0 rgba(255,255,255,0.10)",
  backdropFilter: "blur(8px)",
  ...(isFlashing
    ? {
        background:
          "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.18), transparent 32%), linear-gradient(135deg, rgba(251, 146, 60, 0.44), rgba(249, 115, 22, 0.38))",
        borderColor: "rgba(255, 186, 120, 0.7)",
      }
    : {}),
  "&:hover": {
    ...buttonBaseStyle["&:hover"],
    background:
      "linear-gradient(135deg, rgba(251, 146, 60, 0.34), rgba(249, 115, 22, 0.28))",
    borderColor: "rgba(249, 115, 22, 0.6)",
    boxShadow:
      "0 0 16px rgba(249, 115, 22, 0.34), inset 0 1px 0 rgba(255,255,255,0.14)",
  },
  "&:active": {
    ...buttonBaseStyle["&:active"],
    background:
      "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.18), transparent 32%), linear-gradient(135deg, rgba(251, 146, 60, 0.44), rgba(249, 115, 22, 0.38))",
    borderColor: "rgba(255, 186, 120, 0.7)",
    boxShadow: "none",
  },
});

const warningGhostButtonStyle = (isFlashing: boolean) => ({
  ...buttonBaseStyle,
  color: "#c4b5fd",
  border: "1px solid rgba(168, 85, 247, 0.6)",
  background: isFlashing ? "rgba(168, 85, 247, 0.18)" : "transparent",
  boxShadow: isFlashing ? "none" : "0 0 12px rgba(168, 85, 247, 0.25)",
  ...(isFlashing
    ? {
        background:
          "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.16), transparent 32%), rgba(168, 85, 247, 0.18)",
        borderColor: "rgba(196, 181, 253, 0.82)",
      }
    : {}),
  "&:hover": {
    ...buttonBaseStyle["&:hover"],
    background: "rgba(168, 85, 247, 0.10)",
    borderColor: "rgba(168, 85, 247, 0.8)",
    boxShadow: "0 0 16px rgba(168, 85, 247, 0.30)",
  },
  "&:active": {
    ...buttonBaseStyle["&:active"],
    background:
      "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.16), transparent 32%), rgba(168, 85, 247, 0.18)",
    borderColor: "rgba(196, 181, 253, 0.82)",
    boxShadow: "none",
  },
});

const safeGhostButtonStyle = {
  ...buttonBaseStyle,
  color: "#22c55e",
  border: "1px solid rgba(34, 197, 94, 0.6)",
  background: "rgba(34, 197, 94, 0.03)",
  boxShadow: "0 0 12px rgba(34, 197, 94, 0.25)",
  "&:hover": {
    ...buttonBaseStyle["&:hover"],
    background: "rgba(34, 197, 94, 0.10)",
    borderColor: "rgba(34, 197, 94, 0.8)",
    boxShadow: "0 0 16px rgba(34, 197, 94, 0.30)",
  },
};

const coolantButtonStyle = (isFlashing: boolean) => ({
  ...buttonBaseStyle,
  color: "#93c5fd",
  border: "1px solid rgba(59, 130, 246, 0.55)",
  background: isFlashing
    ? "rgba(59, 130, 246, 0.18)"
    : "rgba(59, 130, 246, 0.04)",
  boxShadow: isFlashing ? "none" : "0 0 12px rgba(59, 130, 246, 0.24)",
  ...(isFlashing
    ? {
        background:
          "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.16), transparent 32%), rgba(59, 130, 246, 0.18)",
        borderColor: "rgba(147, 197, 253, 0.82)",
      }
    : {}),
  "&:hover": {
    ...buttonBaseStyle["&:hover"],
    background: "rgba(59, 130, 246, 0.10)",
    borderColor: "rgba(59, 130, 246, 0.78)",
    boxShadow: "0 0 16px rgba(59, 130, 246, 0.30)",
  },
  "&:active": {
    ...buttonBaseStyle["&:active"],
    background:
      "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.16), transparent 32%), rgba(59, 130, 246, 0.18)",
    borderColor: "rgba(147, 197, 253, 0.82)",
    boxShadow: "none",
  },
});

const infoPanelStyle = {
  mt: 2,
  p: 2,
  flex: 1,
  display: "flex",
  flexDirection: "column",
  borderRadius: 3,
  bgcolor: "rgba(255,255,255,0.035)",
  border: "1px solid rgba(255,255,255,0.10)",
  color: "white",
};

const slideArrowButtonStyle = {
  minWidth: 36,
  width: 36,
  height: 36,
  borderRadius: "10px",
  color: "#e2e8f0",
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
  fontSize: "1.15rem",
  lineHeight: 1,
  "&:hover": {
    background: "rgba(255,255,255,0.08)",
  },
};
