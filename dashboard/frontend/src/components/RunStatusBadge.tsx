import { Chip } from "@mui/material";
import { keyframes } from "@mui/system";

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
`;

const statusConfig: Record<
  string,
  { color: "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"; animated?: boolean }
> = {
  queued: { color: "info" },
  running: { color: "warning", animated: true },
  completed: { color: "success" },
  failed: { color: "error" },
  cancelled: { color: "default" },
  draft: { color: "default" },
};

interface RunStatusBadgeProps {
  status: string;
  size?: "small" | "medium";
}

export function RunStatusBadge({ status, size = "small" }: RunStatusBadgeProps) {
  const config = statusConfig[status] ?? { color: "default" as const };

  return (
    <Chip
      size={size}
      label={status}
      color={config.color}
      variant="filled"
      sx={{
        fontWeight: 600,
        textTransform: "capitalize",
        letterSpacing: 0.5,
        ...(config.animated
          ? { animation: `${pulse} 1.5s ease-in-out infinite` }
          : {}),
      }}
    />
  );
}
