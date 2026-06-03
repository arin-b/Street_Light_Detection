import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import CenterFocusWeakIcon from "@mui/icons-material/CenterFocusWeak";
import DashboardIcon from "@mui/icons-material/Dashboard";
import EditNoteIcon from "@mui/icons-material/EditNote";
import InsightsIcon from "@mui/icons-material/Insights";
import MonitorHeartIcon from "@mui/icons-material/MonitorHeart";
import PlayCircleIcon from "@mui/icons-material/PlayCircle";
import ScienceIcon from "@mui/icons-material/Science";
import TerminalIcon from "@mui/icons-material/Terminal";
import VideoCameraFrontIcon from "@mui/icons-material/VideoCameraFront";
import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import type { ReactNode } from "react";

export type PageKey =
  | "home"
  | "experiments"
  | "yaml"
  | "architecture"
  | "sweeps"
  | "training"
  | "logs"
  | "monitoring"
  | "visualizations"
  | "attention"
  | "tracking";

interface ShellProps {
  page: PageKey;
  onPageChange: (page: PageKey) => void;
  children: ReactNode;
}

const navigation = [
  {
    key: "home" as const,
    label: "Home",
    icon: <DashboardIcon fontSize="small" />,
  },
  {
    key: "experiments" as const,
    label: "Experiments",
    icon: <ScienceIcon fontSize="small" />,
  },
  {
    key: "yaml" as const,
    label: "YAML Editor",
    icon: <EditNoteIcon fontSize="small" />,
  },
  {
    key: "architecture" as const,
    label: "Architecture",
    icon: <AccountTreeIcon fontSize="small" />,
  },
  {
    key: "sweeps" as const,
    label: "Hyper Sweeps",
    icon: <AutoFixHighIcon fontSize="small" />,
  },
  {
    key: "training" as const,
    label: "Training",
    icon: <PlayCircleIcon fontSize="small" />,
  },
  {
    key: "logs" as const,
    label: "Live Logs",
    icon: <TerminalIcon fontSize="small" />,
  },
  {
    key: "monitoring" as const,
    label: "Monitoring",
    icon: <MonitorHeartIcon fontSize="small" />,
  },
  {
    key: "visualizations" as const,
    label: "Visualizations",
    icon: <InsightsIcon fontSize="small" />,
  },
  {
    key: "attention" as const,
    label: "Attention Maps",
    icon: <CenterFocusWeakIcon fontSize="small" />,
  },
  {
    key: "tracking" as const,
    label: "Tracking",
    icon: <VideoCameraFrontIcon fontSize="small" />,
  },
];

export function Shell({ page, onPageChange, children }: ShellProps) {
  const theme = useTheme();
  const compact = useMediaQuery(theme.breakpoints.down("md"));
  const drawerWidth = compact ? 0 : 236;

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        elevation={0}
        position="fixed"
        sx={{
          borderBottom: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
          color: "text.primary",
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar sx={{ minHeight: 64 }}>
          <Stack spacing={0.25}>
            <Typography variant="h6">Nighttime Streetlight Detection</Typography>
            <Typography variant="body2" color="text.secondary">
              Research Dashboard
            </Typography>
          </Stack>
        </Toolbar>
      </AppBar>

      {!compact && (
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: {
              width: drawerWidth,
              boxSizing: "border-box",
              borderRight: "1px solid",
              borderColor: "divider",
            },
          }}
        >
          <Toolbar sx={{ minHeight: 64 }}>
            <Stack spacing={0}>
              <Typography variant="subtitle1" fontWeight={800}>
                RBCCPS
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Phase 3 Workspace
              </Typography>
            </Stack>
          </Toolbar>
          <Divider />
          <Stack sx={{ p: 1.5 }} spacing={0.5}>
            {navigation.map((item) => (
              <Button
                key={item.key}
                startIcon={item.icon}
                onClick={() => onPageChange(item.key)}
                variant={page === item.key ? "contained" : "text"}
                color={page === item.key ? "primary" : "inherit"}
                sx={{
                  justifyContent: "flex-start",
                  py: 0.8,
                  fontSize: 13.5,
                  transition: "all 0.15s ease",
                }}
              >
                {item.label}
              </Button>
            ))}
          </Stack>
        </Drawer>
      )}

      {compact && (
        <Stack
          direction="row"
          spacing={0.5}
          sx={{
            position: "fixed",
            zIndex: theme.zIndex.appBar + 1,
            right: 12,
            top: 14,
            flexWrap: "wrap",
          }}
        >
          {navigation.map((item) => (
            <Button
              key={item.key}
              aria-label={item.label}
              title={item.label}
              onClick={() => onPageChange(item.key)}
              variant={page === item.key ? "contained" : "outlined"}
              sx={{ minWidth: 38, px: 1 }}
            >
              {item.icon}
            </Button>
          ))}
        </Stack>
      )}

      <Box
        component="main"
        sx={{ ml: { md: `${drawerWidth}px` }, pt: 10, px: { xs: 2, md: 3 }, pb: 4 }}
      >
        {children}
      </Box>
    </Box>
  );
}
