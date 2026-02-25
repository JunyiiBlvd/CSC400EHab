"use client";

import { Box, Paper, Typography } from "@mui/material";
import { Gauge } from "@mui/x-charts/Gauge";

export default function NodeGauges({
  temperature,
  cpuLoad,
  nodeId = "node-1",
}: {
  temperature: number;
  cpuLoad: number; // 0..1
  nodeId?: string;
}) {
  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 3,
        bgcolor: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.12)",
        color: "white",
      }}
    >
      <Typography variant="h6" sx={{ mb: 2 }}>
        Live Gauges · {nodeId}
      </Typography>

      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
        <Box>
          <Typography variant="caption" sx={{ opacity: 0.75 }}>
            Temperature (°C)
          </Typography>
          <Gauge value={temperature} valueMin={0} valueMax={100} height={150} />
          <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.85 }}>
            {temperature.toFixed(2)} °C
          </Typography>
        </Box>

        <Box>
          <Typography variant="caption" sx={{ opacity: 0.75 }}>
            CPU (%)
          </Typography>
          <Gauge value={cpuLoad * 100} valueMin={0} valueMax={100} height={150} />
          <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.85 }}>
            {(cpuLoad * 100).toFixed(1)}%
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
}
