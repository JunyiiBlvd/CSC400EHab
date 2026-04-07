"use client";

import { Box, Paper, Typography, Chip } from "@mui/material";
import { Gauge } from "@mui/x-charts/Gauge";

export default function NodeGauges({
  temperature,
  cpuLoad,
  humidity,
  airflow,
  isAnomaly = false,
  nodeId = "node-1",
}: {
  temperature: number;
  cpuLoad: number; // Range: 0..1
  humidity?: number;
  airflow?: number;
  isAnomaly?: boolean;
  nodeId?: string;
}) {
  const showHumidity = typeof humidity === "number";
  const showAirflow = typeof airflow === "number";
  const cols =
    showHumidity || showAirflow ? "repeat(4, 1fr)" : "repeat(2, 1fr)";

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
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Typography variant="h6">Live Gauges · {nodeId}</Typography>
        {isAnomaly ? (
          <Chip label="ANOMALY" color="error" size="small" />
        ) : (
          <Chip label="Normal" size="small" />
        )}
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: cols, gap: 2 }}>
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
          <Gauge
            value={cpuLoad * 100}
            valueMin={0}
            valueMax={100}
            height={150}
          />
          <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.85 }}>
            {(cpuLoad * 100).toFixed(1)}%
          </Typography>
        </Box>

        {showHumidity && (
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.75 }}>
              Humidity (%)
            </Typography>
            <Gauge value={humidity!} valueMin={0} valueMax={100} height={150} />
            <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.85 }}>
              {humidity!.toFixed(1)}%
            </Typography>
          </Box>
        )}

        {showAirflow && (
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.75 }}>
              Airflow
            </Typography>
            <Gauge value={airflow!} valueMin={0} valueMax={2.5} height={150} />
            <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.85 }}>
              {airflow!.toFixed(2)}
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}
