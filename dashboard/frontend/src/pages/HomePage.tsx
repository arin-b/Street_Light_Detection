import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import MemoryIcon from "@mui/icons-material/Memory";
import SettingsEthernetIcon from "@mui/icons-material/SettingsEthernet";
import SpeedIcon from "@mui/icons-material/Speed";
import StorageIcon from "@mui/icons-material/Storage";
import { Alert, Grid, Paper, Stack, Typography } from "@mui/material";
import { useEffect } from "react";

import { StatusTile } from "../components/StatusTile";
import { useDashboardStore } from "../store";

export function HomePage() {
  const { summary, experiments, error, loadSummary, loadExperiments } = useDashboardStore();

  useEffect(() => {
    void loadSummary();
    void loadExperiments();
    const interval = window.setInterval(() => {
      void loadSummary();
    }, 5000);
    return () => window.clearInterval(interval);
  }, [loadExperiments, loadSummary]);

  const latest = experiments[0];

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error">{error}</Alert>}
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} lg={3}>
          <StatusTile label="Active Experiments" value={summary?.experiments_active ?? "0"} icon={<SpeedIcon />} />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatusTile
            label="Completed"
            value={summary?.experiments_completed ?? "0"}
            icon={<CheckCircleIcon />}
            tone="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatusTile label="Failed" value={summary?.experiments_failed ?? "0"} icon={<ErrorIcon />} tone="error" />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatusTile label="YAML Configs" value={summary?.yaml_configs ?? "0"} icon={<StorageIcon />} />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatusTile label="CPU" value={`${summary?.cpu_percent ?? 0}%`} icon={<MemoryIcon />} />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatusTile label="RAM" value={`${summary?.ram_percent ?? 0}%`} icon={<SettingsEthernetIcon />} />
        </Grid>
      </Grid>

      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Stack spacing={1}>
          <Typography variant="h6">Latest Experiment</Typography>
          {latest ? (
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
              <Typography>{latest.name}</Typography>
              <Typography color="text.secondary">{latest.status}</Typography>
              <Typography color="text.secondary">{latest.config_path ?? "No YAML linked"}</Typography>
            </Stack>
          ) : (
            <Typography color="text.secondary">No experiments registered yet.</Typography>
          )}
        </Stack>
      </Paper>
    </Stack>
  );
}
