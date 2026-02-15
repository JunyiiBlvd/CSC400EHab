"use client";
import { Box, Paper, Typography } from "@mui/material";

export default function Home() {
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
        </Paper>

        {/* Right Panel */}
        <Box sx={{ display: "grid", gap: 2 }}>
          {/* Alerts */}
          <Paper sx={panelStyle}>
            <Typography variant="h6">Alerts Feed</Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Alerts will appear here when anomalies occur.
            </Typography>
          </Paper>

          {/* Comparison */}
          <Paper sx={panelStyle}>
            <Typography variant="h6">Central vs Edge Comparison</Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Latency + message volume metrics go here.
            </Typography>
          </Paper>

          {/* Nodes */}
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
                <Typography variant="body2" sx={{ opacity: 0.7 }}>
                  Temperature / Humidity / Airflow
                </Typography>
              </Paper>
            ))}
          </Box>
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
