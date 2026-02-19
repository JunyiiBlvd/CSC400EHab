"use client";

import { Box, Paper, Typography } from "@mui/material";
import Sparkline from "./Sparkline";


type Telemetry = {
  node_id: string;
  timestamp: string;
  temperature: number;
  cpu_load: number;
};

type NodeGridProps = {
  telemetry: Telemetry | null;
  apiError: string | null;
  node1Text: string;
  history: Telemetry[];
};

export default function NodeGrid({ telemetry, apiError, node1Text, history }: NodeGridProps) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: 2,
      }}
    >
      {[1, 2, 3].map((node) => (
        <Paper key={node} sx={panelStyle}>
          <Typography variant="h6">Node {node}</Typography>

          <Typography variant="body2" sx={{ opacity: 0.7, mt: 0.5 }}>
            {node === 1
              ? node1Text
              : apiError
              ? "Backend offline (no data)"
              : "Temperature / Humidity / Airflow"}
          </Typography>

          {node === 1 && telemetry && (
            <Typography variant="caption" sx={{ display: "block", opacity: 0.6, mt: 1 }}>
              Last update: {new Date(telemetry.timestamp).toLocaleTimeString()}
            </Typography>
          )}

          {node === 1 && history.length > 5 && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Temperature trend
            </Typography>
            <Sparkline
              points={history.map((p) => ({
                t: Date.parse(p.timestamp),
                v: p.temperature,
              }))}
            />


            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              CPU trend
            </Typography>
            <Sparkline
              points={history.map((p) => ({
                t: Date.parse(p.timestamp),
                v: p.cpu_load,
              }))}
            />

          </Box>
        )}

        </Paper>
      ))}
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
