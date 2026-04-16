"use client";

import { Box, Chip, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useRef, useState } from "react";

import type { Telemetry, TelemetryByNode } from "../lib/types";

const NODE_IDS = ["node-1", "node-2", "node-3"] as const;

const COLORS = {
  background: "#0b1220",
  panel: "#111a2b",
  border: "#22314d",
  textPrimary: "#e6edf3",
  textSecondary: "#9fb3c8",
  edge: "#22d3ee",
  edgeGlow: "rgba(34, 211, 238, 0.35)",
  edgeNode: "#67e8f9",
  central: "#f59e0b",
  centralGlow: "rgba(245, 158, 11, 0.30)",
  centralNode: "#fbbf24",
  healthy: "#22c55e",
  warning: "#f59e0b",
  anomaly: "#ef4444",
} as const;

type Point = {
  x: number;
  y: number;
};

type CentralNodeStatus = {
  edge_latency_ms: number | null;
  central_latency_ms: number | null;
  latency_delta_ms: number | null;
  bytes_edge: number | null;
  bytes_central: number | null;
  last_updated: number | null;
};

type TopologyOverviewProps = {
  telemetryByNode: TelemetryByNode;
  selectedNodeId: string;
  onSelectNode: (nodeId: string) => void;
  centralStatus?: Record<string, CentralNodeStatus>;
};

const VIEWBOX = {
  width: 1280,
  height: 400,
};

const NODE_POINTS: Record<(typeof NODE_IDS)[number], Point> = {
  "node-1": { x: 200, y: 130 },
  "node-2": { x: 630, y: 92 },
  "node-3": { x: 1060, y: 130 },
};

const HUB_POINT: Point = { x: 640, y: 286 };
const ALERT_POINT: Point = { x: 640, y: 362 };

function fmtMs(value: number | null | undefined): string {
  return value == null ? "—" : `${value.toFixed(1)} ms`;
}

function fmtRatio(edge: number | null | undefined, central: number | null | undefined): string {
  if (edge == null || central == null || edge <= 0) return "—";
  return `${((central / edge) * 100).toFixed(1)}%`;
}

function getNodeStatus(telemetry?: Telemetry): "healthy" | "warning" | "anomaly" {
  if (!telemetry) return "healthy";
  if (telemetry.is_anomaly) return "anomaly";

  if (
    telemetry.cpu_load > 0.85 ||
    telemetry.temperature > 21.5 ||
    telemetry.humidity > 55 ||
    telemetry.airflow < 1.5
  ) {
    return "warning";
  }

  return "healthy";
}

function getStatusColor(status: "healthy" | "warning" | "anomaly") {
  if (status === "anomaly") return COLORS.anomaly;
  if (status === "warning") return COLORS.warning;
  return COLORS.healthy;
}

function getEdgeControl(nodeId: (typeof NODE_IDS)[number]): Point {
  if (nodeId === "node-1") return { x: 360, y: 164 };
  if (nodeId === "node-2") return { x: 520, y: 224 };
  return { x: 920, y: 164 };
}

function getEdgeEndControl(nodeId: (typeof NODE_IDS)[number]): Point {
  if (nodeId === "node-1") return { x: 500, y: 346 };
  if (nodeId === "node-2") return { x: 920, y: 320 };
  return { x: 780, y: 346 };
}

function getHubIngressControl(nodeId: (typeof NODE_IDS)[number]): Point {
  if (nodeId === "node-1") return { x: 212, y: 260 };
  if (nodeId === "node-2") return { x: 702, y: 170 };
  return { x: 1048, y: 260 };
}

function MetricCard({
  nodeId,
  isSelected,
  status,
}: {
  nodeId: string;
  isSelected: boolean;
  status: CentralNodeStatus | undefined;
}) {
  return (
    <Box
      sx={{
        p: 1.5,
        borderRadius: 2.5,
        bgcolor: isSelected ? "rgba(34, 211, 238, 0.08)" : "rgba(255,255,255,0.03)",
        border: isSelected
          ? "1px solid rgba(34, 211, 238, 0.28)"
          : "1px solid rgba(255,255,255,0.08)",
        minHeight: 104,
      }}
    >
      <Typography
        variant="caption"
        sx={{
          display: "block",
          color: isSelected ? COLORS.textPrimary : COLORS.textSecondary,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          mb: 1,
        }}
      >
        {nodeId}
      </Typography>

      <Stack spacing={0.45}>
        <Typography variant="body2" sx={{ color: COLORS.textPrimary }}>
          Edge {fmtMs(status?.edge_latency_ms)}
        </Typography>
        <Typography variant="body2" sx={{ color: COLORS.textPrimary }}>
          Central {fmtMs(status?.central_latency_ms)}
        </Typography>
        <Typography variant="body2" sx={{ color: COLORS.textSecondary }}>
          Delta {fmtMs(status?.latency_delta_ms)}
        </Typography>
        <Typography variant="body2" sx={{ color: COLORS.textSecondary }}>
          BW (central/edge) {fmtRatio(status?.bytes_edge, status?.bytes_central)}
        </Typography>
      </Stack>
    </Box>
  );
}

export default function TopologyOverview({
  telemetryByNode,
  selectedNodeId,
  onSelectNode,
  centralStatus = {},
}: TopologyOverviewProps) {
  const [now, setNow] = useState(0);
  const edgePathRefs = useRef<Record<string, SVGPathElement | null>>({});
  const centralIngressRefs = useRef<Record<string, SVGPathElement | null>>({});
  const centralEgressRef = useRef<SVGPathElement | null>(null);

  useEffect(() => {
    setNow(performance.now());
    const id = window.setInterval(() => setNow(performance.now()), 40);
    return () => window.clearInterval(id);
  }, []);

  const activeNodeIds = useMemo(
    () => NODE_IDS.filter((nodeId) => telemetryByNode[nodeId]),
    [telemetryByNode],
  );

  const anomalyCount = activeNodeIds.filter(
    (nodeId) => telemetryByNode[nodeId]?.is_anomaly === true,
  ).length;

  const edgePaths = useMemo(
    () =>
      Object.fromEntries(
        NODE_IDS.map((nodeId) => {
          const start = NODE_POINTS[nodeId];
          const control1 = getEdgeControl(nodeId);
          const control2 = getEdgeEndControl(nodeId);
          return [
            nodeId,
            `M ${start.x} ${start.y} C ${control1.x} ${control1.y}, ${control2.x} ${control2.y}, ${ALERT_POINT.x} ${ALERT_POINT.y}`,
          ];
        }),
      ) as Record<(typeof NODE_IDS)[number], string>,
    [],
  );

  const centralIngressPaths = useMemo(
    () =>
      Object.fromEntries(
        NODE_IDS.map((nodeId) => {
          const start = NODE_POINTS[nodeId];
          const control1 = getHubIngressControl(nodeId);
          const control2 = {
            x: HUB_POINT.x + (start.x < HUB_POINT.x ? -94 : 94),
            y: HUB_POINT.y - 46,
          };
          return [
            nodeId,
            `M ${start.x} ${start.y} C ${control1.x} ${control1.y}, ${control2.x} ${control2.y}, ${HUB_POINT.x} ${HUB_POINT.y}`,
          ];
        }),
      ) as Record<(typeof NODE_IDS)[number], string>,
    [],
  );

  const centralEgressPath = useMemo(
    () =>
      `M ${HUB_POINT.x} ${HUB_POINT.y} C ${HUB_POINT.x} ${HUB_POINT.y + 26}, ${ALERT_POINT.x} ${ALERT_POINT.y - 26}, ${ALERT_POINT.x} ${ALERT_POINT.y}`,
    [],
  );

  function getPathPoint(
    pathEl: SVGPathElement | null,
    progress: number,
  ): Point | null {
    if (!pathEl) return null;
    const length = pathEl.getTotalLength();
    const point = pathEl.getPointAtLength(length * Math.max(0, Math.min(progress, 1)));
    return { x: point.x, y: point.y };
  }

  return (
    <Paper
      sx={{
        position: "relative",
        p: 2.25,
        borderRadius: 3.5,
        bgcolor: COLORS.panel,
        color: COLORS.textPrimary,
        overflow: "hidden",
        border: `1px solid ${COLORS.border}`,
        backgroundImage: `
          radial-gradient(circle at 18% 20%, rgba(34, 211, 238, 0.18), transparent 26%),
          radial-gradient(circle at 50% 88%, rgba(245, 158, 11, 0.14), transparent 24%),
          radial-gradient(circle at 96% 36%, rgba(239, 68, 68, 0.12), transparent 16%),
          linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0))
        `,
        boxShadow:
          "inset 0 1px 0 rgba(255,255,255,0.05), 0 24px 60px rgba(0,0,0,0.22)",
      }}
    >
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 0%, rgba(255,255,255,0.03), transparent 45%)",
          pointerEvents: "none",
        }}
      />

      <Box
        sx={{
          position: "relative",
          zIndex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 2,
          mb: 1.75,
        }}
      >
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: "0.01em" }}>
            Distributed Detection Architecture
          </Typography>
          <Typography variant="body2" sx={{ color: COLORS.textSecondary, mt: 0.5 }}>
            Edge inference stays with the nodes. Central polling routes below.
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", justifyContent: "flex-end" }}>
          <Chip
            label={`${activeNodeIds.length}/3 live`}
            size="small"
            sx={{
              color: COLORS.textPrimary,
              bgcolor: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.10)",
            }}
          />
          <Chip
            label={`${anomalyCount} anomaly`}
            size="small"
            sx={{
              color: COLORS.textPrimary,
              bgcolor: "rgba(239, 68, 68, 0.12)",
              border: "1px solid rgba(239, 68, 68, 0.22)",
            }}
          />
          <Chip
            label="Edge"
            size="small"
            sx={{
              color: COLORS.textPrimary,
              bgcolor: "rgba(34, 211, 238, 0.14)",
              border: "1px solid rgba(34, 211, 238, 0.28)",
            }}
          />
          <Chip
            label="Central"
            size="small"
            sx={{
              color: COLORS.textPrimary,
              bgcolor: "rgba(245, 158, 11, 0.14)",
              border: "1px solid rgba(245, 158, 11, 0.28)",
            }}
          />
        </Stack>
      </Box>

      <Box
        sx={{
          position: "relative",
          zIndex: 1,
          width: "100%",
          overflowX: "auto",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <svg
          viewBox="0 0 1280 400"
          width="100%"
          height="400"
          role="img"
          aria-label="E-Habitat topology showing distributed edge inference and routed central detection"
          preserveAspectRatio="xMidYMid meet"
          style={{ display: "block", minWidth: 980, marginInline: "auto" }}
        >
          <defs>
            <pattern id="topology-dot-field" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="10" cy="10" r="1.2" fill="rgba(159, 179, 200, 0.08)" />
            </pattern>
            <radialGradient id="stage-cyan-glow" cx="44%" cy="28%" r="48%">
              <stop offset="0%" stopColor="rgba(34, 211, 238, 0.08)" />
              <stop offset="65%" stopColor="rgba(34, 211, 238, 0.025)" />
              <stop offset="100%" stopColor="rgba(34, 211, 238, 0)" />
            </radialGradient>
            <radialGradient id="stage-amber-glow" cx="58%" cy="78%" r="34%">
              <stop offset="0%" stopColor="rgba(245, 158, 11, 0.05)" />
              <stop offset="100%" stopColor="rgba(245, 158, 11, 0)" />
            </radialGradient>
            <radialGradient id="ground-glow" cx="50%" cy="100%" r="44%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.04)" />
              <stop offset="55%" stopColor="rgba(255,255,255,0.015)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0)" />
            </radialGradient>
            <filter id="edge-glow" x="-200%" y="-200%" width="500%" height="500%">
              <feGaussianBlur stdDeviation="9" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="central-glow" x="-200%" y="-200%" width="500%" height="500%">
              <feGaussianBlur stdDeviation="9" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="packet-glow" x="-240%" y="-240%" width="580%" height="580%">
              <feGaussianBlur stdDeviation="12" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <rect
            x="0"
            y="0"
            width={VIEWBOX.width}
            height={VIEWBOX.height}
            fill={COLORS.background}
          />
          <rect
            x="0"
            y="0"
            width={VIEWBOX.width}
            height={VIEWBOX.height}
            fill="url(#topology-dot-field)"
          />
          <rect
            x="0"
            y="0"
            width={VIEWBOX.width}
            height={VIEWBOX.height}
            fill="url(#stage-cyan-glow)"
          />
          <rect
            x="0"
            y="0"
            width={VIEWBOX.width}
            height={VIEWBOX.height}
            fill="url(#stage-amber-glow)"
          />
          <ellipse cx="640" cy="374" rx="520" ry="44" fill="url(#ground-glow)" opacity="0.95" />

          <g>
            <ellipse cx="640" cy="104" rx="500" ry="62" fill="rgba(34, 211, 238, 0.035)" />
            <path
              d="M 134 106 C 296 76, 466 70, 640 94 C 816 118, 982 122, 1146 108"
              fill="none"
              stroke="rgba(34, 211, 238, 0.12)"
              strokeWidth="1.1"
              strokeLinecap="round"
              strokeDasharray="1 12"
            />
            <text
              x="144"
              y="62"
              fill={COLORS.textSecondary}
              fontSize="14"
              fontWeight="600"
              style={{ letterSpacing: "0.18em", textTransform: "uppercase" }}
            >
              NODE-LOCAL INFERENCE
            </text>
          </g>

          <ellipse cx="640" cy="338" rx="430" ry="30" fill="rgba(0,0,0,0.22)" />

          {NODE_IDS.map((nodeId, index) => {
            const start = NODE_POINTS[nodeId];
            const telemetry = telemetryByNode[nodeId];
            const isSelected = nodeId === selectedNodeId;
            const status = getNodeStatus(telemetry);
            const statusColor = getStatusColor(status);
            const pulse = 0.35 + 0.35 * (0.5 + 0.5 * Math.sin((now + index * 220) / 220));

            const edgeCycleMs = 1800;
            const edgeTravelMs = 200;
            const edgeOffsets = [0, 0, 0];
            const edgePhase = (now + edgeOffsets[index]) % edgeCycleMs;
            const edgeActive = edgePhase <= edgeTravelMs;
            const edgeProgress = Math.min(edgePhase / edgeTravelMs, 1);
            const edgePacket = getPathPoint(
              edgePathRefs.current[nodeId],
              edgeProgress,
            );

            const centralCycleMs = 2400;
            const ingressMs = 600;
            const pauseMs = 200;
            const egressMs = 400;
            const centralOffsets = [180, 760, 1340];
            const centralPhase = (now + centralOffsets[index]) % centralCycleMs;
            const ingressActive = centralPhase <= ingressMs;
            const pauseActive =
              centralPhase > ingressMs && centralPhase <= ingressMs + pauseMs;
            const egressActive =
              centralPhase > ingressMs + pauseMs &&
              centralPhase <= ingressMs + pauseMs + egressMs;

            const ingressProgress = Math.min(centralPhase / ingressMs, 1);
            const egressProgress = Math.min(
              (centralPhase - ingressMs - pauseMs) / egressMs,
              1,
            );

            const centralIngressPacket = getPathPoint(
              centralIngressRefs.current[nodeId],
              ingressProgress,
            );
            const centralEgressPacket = getPathPoint(
              centralEgressRef.current,
              Math.max(0, egressProgress),
            );

            return (
              <g key={nodeId}>
                <path
                  d={edgePaths[nodeId]}
                  fill="none"
                  stroke="rgba(34, 211, 238, 0.07)"
                  strokeWidth={isSelected ? 4.2 : 3.1}
                  strokeLinecap="round"
                />
                <path
                  ref={(el) => {
                    edgePathRefs.current[nodeId] = el;
                  }}
                  d={edgePaths[nodeId]}
                  fill="none"
                  stroke={COLORS.edge}
                  strokeOpacity={isSelected ? 0.68 : 0.18}
                  strokeWidth={isSelected ? 2.5 : 1.35}
                  strokeLinecap="round"
                  filter="url(#edge-glow)"
                />

                <path
                  d={centralIngressPaths[nodeId]}
                  fill="none"
                  stroke="rgba(245, 158, 11, 0.07)"
                  strokeWidth={isSelected ? 4.2 : 3.1}
                  strokeLinecap="round"
                />
                <path
                  ref={(el) => {
                    centralIngressRefs.current[nodeId] = el;
                  }}
                  d={centralIngressPaths[nodeId]}
                  fill="none"
                  stroke={COLORS.central}
                  strokeOpacity={isSelected ? 0.56 : 0.16}
                  strokeWidth={isSelected ? 2.35 : 1.3}
                  strokeLinecap="round"
                  filter="url(#central-glow)"
                />

                <g opacity={0.96}>
                  <rect
                    x={start.x - 28}
                    y={start.y - 58}
                    width="56"
                    height="18"
                    rx="9"
                    fill="rgba(34, 211, 238, 0.10)"
                    stroke="rgba(34, 211, 238, 0.28)"
                    strokeWidth="1"
                  />
                  <text
                    x={start.x}
                    y={start.y - 46}
                    fill={COLORS.edgeNode}
                    fontSize="7.5"
                    fontWeight="700"
                    textAnchor="middle"
                    style={{ letterSpacing: "0.12em", textTransform: "uppercase" }}
                  >
                    LOCAL IF
                  </text>
                  <line
                    x1={start.x}
                    y1={start.y - 40}
                    x2={start.x}
                    y2={start.y - 28}
                    stroke="rgba(34, 211, 238, 0.28)"
                    strokeWidth="1"
                    strokeDasharray="2 3"
                  />
                  <rect
                    x={start.x + 22}
                    y={start.y - 58}
                    width="24"
                    height="18"
                    rx="9"
                    fill="rgba(239, 68, 68, 0.12)"
                    stroke="rgba(239, 68, 68, 0.42)"
                    strokeWidth="1.2"
                  />
                  <circle
                    cx={start.x + 30}
                    cy={start.y - 49}
                    r="3"
                    fill={COLORS.anomaly}
                  />
                  <text
                    x={start.x + 39}
                    y={start.y - 46}
                    fill={COLORS.textPrimary}
                    fontSize="6.5"
                    fontWeight="700"
                    textAnchor="middle"
                    style={{ letterSpacing: "0.04em" }}
                  >
                    OUT
                  </text>
                  <line
                    x1={start.x + 20}
                    y1={start.y - 49}
                    x2={start.x + 22}
                    y2={start.y - 49}
                    stroke="rgba(239, 68, 68, 0.42)"
                    strokeWidth="1"
                  />
                  <circle
                    cx={start.x}
                    cy={start.y}
                    r={isSelected ? 48 : 43}
                    fill={isSelected ? "rgba(34, 211, 238, 0.10)" : "rgba(255,255,255,0.02)"}
                    stroke={isSelected ? "rgba(103, 232, 249, 0.36)" : "rgba(34, 49, 77, 0.92)"}
                    strokeWidth="1.4"
                  />
                  <circle
                    cx={start.x}
                    cy={start.y}
                    r={isSelected ? 31 : 28}
                    fill="rgba(10, 15, 28, 0.98)"
                    stroke={isSelected ? COLORS.edgeNode : "rgba(159, 179, 200, 0.22)"}
                    strokeWidth={isSelected ? 2.1 : 1.4}
                  />
                  <circle
                    cx={start.x}
                    cy={start.y}
                    r={isSelected ? 17 : 15}
                    fill={statusColor}
                  />
                  <text
                    x={start.x}
                    y={start.y + 4}
                    fill={COLORS.textPrimary}
                    fontSize="9"
                    fontWeight="800"
                    textAnchor="middle"
                    style={{ fontFamily: "monospace", letterSpacing: "0.04em" }}
                  >
                    IF
                  </text>
                  <circle
                    cx={start.x}
                    cy={start.y}
                    r={isSelected ? 24 : 21}
                    fill="none"
                    stroke={statusColor}
                    strokeOpacity={isSelected ? 0.8 : 0.34}
                    strokeWidth="1.6"
                  />
                  <circle
                    cx={start.x}
                    cy={start.y}
                    r={isSelected ? 35 : 31}
                    fill="none"
                    stroke={COLORS.edge}
                    strokeOpacity={isSelected ? 0.26 + pulse * 0.32 : 0.05 + pulse * 0.08}
                    strokeWidth="1.4"
                  />
                </g>

                <g
                  onClick={() => onSelectNode(nodeId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelectNode(nodeId);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select ${nodeId}`}
                  style={{ cursor: "pointer", outline: "none" }}
                >
                  <circle
                    cx={start.x}
                    cy={start.y}
                    r={isSelected ? 48 : 43}
                    fill="transparent"
                  />
                  <text
                    x={start.x}
                    y={start.y + 66}
                    fill={isSelected ? COLORS.textPrimary : COLORS.textSecondary}
                    fontSize="15"
                    fontWeight="600"
                    textAnchor="middle"
                    style={{ letterSpacing: "0.18em", textTransform: "uppercase" }}
                  >
                    {nodeId}
                  </text>
                </g>

                {edgeActive && telemetry && edgePacket && (
                  <g filter="url(#packet-glow)">
                    <circle
                      cx={edgePacket.x}
                      cy={edgePacket.y}
                      r={isSelected ? 14 : 11}
                      fill={COLORS.edgeGlow}
                    />
                    <circle
                      cx={edgePacket.x}
                      cy={edgePacket.y}
                      r={isSelected ? 5.6 : 4.5}
                      fill={COLORS.edge}
                    />
                  </g>
                )}

                {ingressActive && telemetry && centralIngressPacket && (
                  <g filter="url(#packet-glow)">
                    <circle
                      cx={centralIngressPacket.x}
                      cy={centralIngressPacket.y}
                      r={isSelected ? 14 : 11}
                      fill={COLORS.centralGlow}
                    />
                    <circle
                      cx={centralIngressPacket.x}
                      cy={centralIngressPacket.y}
                      r={isSelected ? 5.6 : 4.5}
                      fill={COLORS.central}
                    />
                  </g>
                )}

                {pauseActive && telemetry && (
                  <g filter="url(#packet-glow)">
                    <circle cx={HUB_POINT.x} cy={HUB_POINT.y} r="17" fill={COLORS.centralGlow} />
                    <circle cx={HUB_POINT.x} cy={HUB_POINT.y} r="5" fill={COLORS.central} />
                  </g>
                )}

                {egressActive && telemetry && index === 1 && centralEgressPacket && (
                  <g filter="url(#packet-glow)">
                    <circle
                      cx={centralEgressPacket.x}
                      cy={centralEgressPacket.y}
                      r={14}
                      fill={COLORS.centralGlow}
                    />
                    <circle
                      cx={centralEgressPacket.x}
                      cy={centralEgressPacket.y}
                      r={5.4}
                      fill={COLORS.central}
                    />
                  </g>
                )}
              </g>
            );
          })}

          <path
            d={centralEgressPath}
            fill="none"
            stroke="rgba(245, 158, 11, 0.07)"
            strokeWidth="3.1"
            strokeLinecap="round"
          />
          <path
            ref={centralEgressRef}
            d={centralEgressPath}
            fill="none"
            stroke={COLORS.central}
            strokeOpacity="0.18"
            strokeWidth="1.35"
            strokeLinecap="round"
            filter="url(#central-glow)"
          />

          <g>
            <text
              x={590}
              y={254}
              fill={COLORS.textSecondary}
              fontSize="14"
              fontWeight="600"
              textAnchor="middle"
              style={{ letterSpacing: "0.18em", textTransform: "uppercase" }}
            >
              CENTRAL SERVER
            </text>
            <circle cx={HUB_POINT.x} cy={HUB_POINT.y} r="38" fill="rgba(245, 158, 11, 0.03)" />
            <circle
              cx={HUB_POINT.x}
              cy={HUB_POINT.y}
              r="28"
              fill="rgba(11, 18, 32, 0.98)"
              stroke="rgba(245, 158, 11, 0.24)"
              strokeWidth="1.5"
            />
            <circle
              cx={HUB_POINT.x}
              cy={HUB_POINT.y}
              r="15"
              fill="rgba(245, 158, 11, 0.10)"
              stroke="rgba(251, 191, 36, 0.75)"
              strokeWidth="1.5"
            />
            <circle cx={HUB_POINT.x} cy={HUB_POINT.y} r="6" fill={COLORS.centralNode} />
            <text
              x={HUB_POINT.x}
              y={HUB_POINT.y + 4}
              fill={COLORS.textPrimary}
              fontSize="9"
              fontWeight="800"
              textAnchor="middle"
              style={{ fontFamily: "monospace", letterSpacing: "0.04em" }}
            >
              IF
            </text>
          </g>

          <g>
            <text
              x={ALERT_POINT.x}
              y={335}
              fill={COLORS.textSecondary}
              fontSize="12"
              textAnchor="middle"
              style={{ letterSpacing: "0.18em", textTransform: "uppercase" }}
            >
              ANOMALY OUTPUT
            </text>
            <circle cx={ALERT_POINT.x} cy={ALERT_POINT.y} r="32" fill="rgba(239, 68, 68, 0.07)" />
            <circle
              cx={ALERT_POINT.x}
              cy={ALERT_POINT.y}
              r="24"
              fill="none"
              stroke="rgba(239, 68, 68, 0.18)"
              strokeWidth="1.2"
            />
            <circle
              cx={ALERT_POINT.x}
              cy={ALERT_POINT.y}
              r="18"
              fill="rgba(11, 18, 32, 0.98)"
              stroke="rgba(239, 68, 68, 0.42)"
              strokeWidth="1.8"
            />
            <circle
              cx={ALERT_POINT.x}
              cy={ALERT_POINT.y}
              r="10"
              fill="rgba(239, 68, 68, 0.18)"
              stroke={COLORS.anomaly}
              strokeWidth="1.6"
            />
            <path
              d={`M ${ALERT_POINT.x} ${ALERT_POINT.y - 4} L ${ALERT_POINT.x} ${ALERT_POINT.y + 3}`}
              stroke={COLORS.textPrimary}
              strokeWidth="2"
              strokeLinecap="round"
            />
            <circle cx={ALERT_POINT.x} cy={ALERT_POINT.y + 6} r="1.8" fill={COLORS.textPrimary} />
          </g>
        </svg>
      </Box>

      <Box
        sx={{
          position: "relative",
          zIndex: 1,
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            lg: "repeat(3, minmax(0, 1fr))",
          },
          gap: 1.5,
          mt: 1.5,
        }}
      >
        {NODE_IDS.map((nodeId) => (
          <MetricCard
            key={nodeId}
            nodeId={nodeId}
            isSelected={selectedNodeId === nodeId}
            status={centralStatus[nodeId]}
          />
        ))}
      </Box>
    </Paper>
  );
}
