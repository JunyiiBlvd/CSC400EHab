"use client";

import { Box, Paper, Typography, Chip } from "@mui/material";
import Sparkline from "./Sparkline";
import type { HistoryByNode, TelemetryByNode } from "../lib/types";

type NodeGridProps = {
  telemetryByNode: TelemetryByNode;
  apiError: string | null;
  historyByNode: HistoryByNode;
  selectedNodeId: string;
  onSelectNode: (nodeId: string) => void;
};

export default function NodeGrid({
  telemetryByNode,
  apiError,
  historyByNode,
  selectedNodeId,
  onSelectNode,
}: NodeGridProps) {
  const nodeIds = ["node-1", "node-2", "node-3"];

  return (
    <Box sx={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 2 }}>
      {nodeIds.map((nodeId, index) => {
        const telemetry = telemetryByNode[nodeId];
        const history = historyByNode[nodeId] ?? [];
        const isAnomaly = telemetry?.is_anomaly === true;
        const isSelected = nodeId === selectedNodeId;

        return (
          <Paper
            key={nodeId}
            sx={{
              ...panelStyle,
              cursor: "pointer",
              border: isSelected
                ? "1px solid rgba(144,202,249,0.85)"
                : "1px solid rgba(255,255,255,0.12)",
              boxShadow: isSelected ? "0 0 0 1px rgba(144,202,249,0.45) inset" : "none",
            }}
            onClick={() => onSelectNode(nodeId)}
          >
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Typography variant="h6">Node {index + 1}</Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {isSelected ? <Chip label="SELECTED" color="primary" size="small" /> : null}
              </Box>
            </Box>

            <Typography variant="body2" sx={{ opacity: 0.7, mt: 0.5 }}>
              {apiError
                ? "Backend offline (no data)"
                : telemetry
                ? `Temp: ${telemetry.temperature.toFixed(2)} °C · CPU: ${(telemetry.cpu_load * 100).toFixed(1)}% · Hum: ${telemetry.humidity.toFixed(1)}% · Air: ${telemetry.airflow.toFixed(2)}`
                : "Waiting for telemetry..."}
            </Typography>

            {telemetry && (
              <Typography variant="caption" sx={{ display: "block", opacity: 0.6, mt: 1 }}>
                Last update: {new Date(telemetry.timestamp).toLocaleTimeString()}
              </Typography>
            )}

            {history.length > 5 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Temperature trend
                </Typography>
                <Sparkline points={history.map((p) => ({ t: Date.parse(p.timestamp), v: p.temperature }))} />

                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  CPU trend
                </Typography>
                <Sparkline points={history.map((p) => ({ t: Date.parse(p.timestamp), v: p.cpu_load }))} />
              </Box>
            )}
          </Paper>
        );
      })}
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
