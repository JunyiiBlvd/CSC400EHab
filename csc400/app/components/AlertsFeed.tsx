"use client";

import { Paper, Typography, Box, Chip } from "@mui/material";

export type AlertItem = {
  id: string;
  ts: string;
  level: "info" | "warn" | "crit";
  message: string;
};

export default function AlertsFeed({ alerts }: { alerts: AlertItem[] }) {
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
        Alerts Feed
      </Typography>

      {alerts.length === 0 && (
        <Typography variant="body2" sx={{ opacity: 0.7 }}>
          No active alerts.
        </Typography>
      )}

      <Box sx={{ display: "grid", gap: 1 }}>
        {alerts.map((alert) => (
          <Box
            key={alert.id}
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              p: 1,
              borderRadius: 2,
              bgcolor:
                alert.level === "crit"
                  ? "rgba(255,0,0,0.15)"
                  : alert.level === "warn"
                  ? "rgba(255,165,0,0.15)"
                  : "rgba(0,150,255,0.15)",
            }}
          >
            <Typography variant="body2">
              {alert.message}
            </Typography>

            <Chip
              size="small"
              label={alert.level.toUpperCase()}
              color={
                alert.level === "crit"
                  ? "error"
                  : alert.level === "warn"
                  ? "warning"
                  : "info"
              }
            />
          </Box>
        ))}
      </Box>
    </Paper>
  );
}
