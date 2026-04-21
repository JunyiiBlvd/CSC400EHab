"use client";

import { Paper, Typography, Box, Chip } from "@mui/material";
import type { AlertItem } from "../lib/types";

export default function AlertsFeed({
  alerts,
  maxHeight,
  fillHeight = false,
}: {
  alerts: AlertItem[];
  maxHeight?: number | string;
  fillHeight?: boolean;
}) {
  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 3,
        bgcolor: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.12)",
        color: "white",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        height: fillHeight ? "100%" : "auto",
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

      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1,
          flex: fillHeight ? 1 : "0 1 auto",
          minHeight: 0,
          maxHeight: fillHeight ? "none" : maxHeight,
          overflowY: fillHeight || maxHeight ? "auto" : "visible",
          pr: fillHeight || maxHeight ? 0.5 : 0,
        }}
      >
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
            <Typography variant="body2">{alert.message}</Typography>

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
