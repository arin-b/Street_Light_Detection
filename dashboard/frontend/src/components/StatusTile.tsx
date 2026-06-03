import { Paper, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface StatusTileProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  tone?: "default" | "success" | "warning" | "error";
}

const toneColor = {
  default: "primary.main",
  success: "success.main",
  warning: "warning.main",
  error: "error.main"
} as const;

export function StatusTile({ label, value, icon, tone = "default" }: StatusTileProps) {
  return (
    <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, height: "100%" }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
        <Stack spacing={0.5}>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="h5">{value}</Typography>
        </Stack>
        <Stack
          alignItems="center"
          justifyContent="center"
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            bgcolor: "action.hover",
            color: toneColor[tone]
          }}
        >
          {icon}
        </Stack>
      </Stack>
    </Paper>
  );
}
