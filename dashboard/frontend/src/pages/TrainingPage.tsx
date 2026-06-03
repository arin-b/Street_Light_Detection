import DeleteIcon from "@mui/icons-material/Delete";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import {
  Alert,
  Box,
  Button,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { MetricMiniChart } from "../components/MetricMiniChart";
import { RunStatusBadge } from "../components/RunStatusBadge";
import { useDashboardStore } from "../store";
import type { LogEntry, Run, RunProgress } from "../types";

export function TrainingPage() {
  const { experiments, runs, loadExperiments, loadRuns } = useDashboardStore();
  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<RunProgress | null>(null);
  const [metrics, setMetrics] = useState<LogEntry[]>([]);

  // Metric data extracted from run logs
  const [lossData, setLossData] = useState<{ step: number; value: number }[]>([]);
  const [mapData, setMapData] = useState<{ step: number; value: number }[]>([]);
  const [precisionData, setPrecisionData] = useState<{ step: number; value: number }[]>([]);
  const [recallData, setRecallData] = useState<{ step: number; value: number }[]>([]);

  useEffect(() => {
    void loadExperiments();
    void loadRuns();
  }, [loadExperiments, loadRuns]);

  // Poll active runs for progress
  useEffect(() => {
    const activeRun = runs.find((r) => r.status === "running");
    if (!activeRun) return;

    setSelectedRunId(activeRun.id);

    const interval = window.setInterval(async () => {
      try {
        const prog = await api.getRunProgress(activeRun.id);
        setProgress(prog);
        if (!prog.is_running) {
          void loadRuns();
        }
      } catch {
        /* ignore */
      }
    }, 2000);

    return () => window.clearInterval(interval);
  }, [runs, loadRuns]);

  // Load metrics for selected run
  useEffect(() => {
    if (!selectedRunId) return;

    const loadMetrics = async () => {
      try {
        const logs = await api.getRunLogs(selectedRunId, 2000, 0);
        setMetrics(logs);
        
        // Parse metric values from log messages
        const losses: { step: number; value: number }[] = [];
        const maps: { step: number; value: number }[] = [];
        const precs: { step: number; value: number }[] = [];
        const recs: { step: number; value: number }[] = [];
        
        let epoch = 0;
        for (const log of logs) {
          const epochMatch = log.message.match(/^\s*(\d+)\/\d+/);
          if (epochMatch) epoch = parseInt(epochMatch[1]);
          
          const lossMatch = log.message.match(/[\d.]+G?\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)/);
          if (lossMatch) {
            const totalLoss = parseFloat(lossMatch[1]) + parseFloat(lossMatch[2]) + parseFloat(lossMatch[3]);
            losses.push({ step: epoch, value: totalLoss });
          }

          const valMatch = log.message.match(/all\s+\d+\s+\d+\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)/);
          if (valMatch) {
            precs.push({ step: epoch, value: parseFloat(valMatch[1]) });
            recs.push({ step: epoch, value: parseFloat(valMatch[2]) });
            maps.push({ step: epoch, value: parseFloat(valMatch[3]) });
          }
        }
        
        setLossData(losses);
        setMapData(maps);
        setPrecisionData(precs);
        setRecallData(recs);
      } catch {
        /* ignore */
      }
    };

    void loadMetrics();
    const interval = window.setInterval(loadMetrics, 5000);
    return () => window.clearInterval(interval);
  }, [selectedRunId]);

  const selectedRun = useMemo(
    () => runs.find((r) => r.id === selectedRunId),
    [runs, selectedRunId]
  );

  const launchableExperiments = experiments.filter(
    (e) => e.status === "draft" || e.status === "completed" || e.status === "failed"
  );

  async function handleStart() {
    if (selectedExperimentId == null) return;
    setError(null);
    try {
      const run = await api.startTraining(selectedExperimentId);
      setMessage(`Training started (Run #${run.id})`);
      setSelectedRunId(run.id);
      await loadRuns();
      await loadExperiments();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start training");
    }
  }

  async function handleStop(runId: number) {
    try {
      await api.stopTraining(runId);
      setMessage("Training stopped");
      await loadRuns();
      await loadExperiments();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to stop training");
    }
  }

  async function handleDelete(runId: number) {
    try {
      await api.deleteRun(runId);
      if (selectedRunId === runId) setSelectedRunId(null);
      setMessage("Run deleted");
      await loadRuns();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete run");
    }
  }

  function formatDuration(start: string | null, end: string | null): string {
    if (!start) return "—";
    const s = new Date(start).getTime();
    const e = end ? new Date(end).getTime() : Date.now();
    const diff = Math.max(0, e - s);
    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    const secs = Math.floor((diff % 60000) / 1000);
    if (hours > 0) return `${hours}h ${mins}m`;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
  }

  const activeRuns = runs.filter((r) => r.status === "running");
  const completedRuns = runs.filter((r) => r.status !== "running" && r.status !== "queued");

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
      {message && <Alert severity="success" onClose={() => setMessage(null)}>{message}</Alert>}

      {/* Launch Panel */}
      <Paper
        variant="outlined"
        sx={{
          p: 2.5,
          borderRadius: 2,
          background: "linear-gradient(135deg, rgba(23,107,107,0.04) 0%, rgba(169,91,34,0.04) 100%)",
        }}
      >
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={700}>
            🚀 Launch Training
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="flex-end">
            <FormControl fullWidth size="small" sx={{ maxWidth: 400 }}>
              <InputLabel>Select Experiment</InputLabel>
              <Select
                label="Select Experiment"
                value={selectedExperimentId ?? ""}
                onChange={(e) => setSelectedExperimentId(e.target.value as number)}
              >
                {launchableExperiments.map((exp) => (
                  <MenuItem key={exp.id} value={exp.id}>
                    {exp.name} ({exp.status})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => void handleStart()}
              disabled={selectedExperimentId == null}
              sx={{
                minWidth: 160,
                background: "linear-gradient(135deg, #176b6b 0%, #1a8a8a 100%)",
                "&:hover": { background: "linear-gradient(135deg, #145b5b 0%, #167878 100%)" },
              }}
            >
              Start Training
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        {/* Active Runs */}
        <Grid item xs={12} lg={7}>
          <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
            <Box sx={{ p: 2, borderBottom: "1px solid", borderColor: "divider" }}>
              <Typography variant="subtitle1" fontWeight={700}>
                Training Runs ({runs.length})
              </Typography>
            </Box>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Experiment</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {runs.map((run) => {
                  const expName =
                    experiments.find((e) => e.id === run.experiment_id)?.name ??
                    `Exp #${run.experiment_id}`;
                  return (
                    <TableRow
                      key={run.id}
                      hover
                      selected={selectedRunId === run.id}
                      onClick={() => setSelectedRunId(run.id)}
                      sx={{ cursor: "pointer" }}
                    >
                      <TableCell>#{run.id}</TableCell>
                      <TableCell>{expName}</TableCell>
                      <TableCell>
                        <RunStatusBadge status={run.status} />
                      </TableCell>
                      <TableCell>
                        {formatDuration(run.started_at, run.finished_at)}
                      </TableCell>
                      <TableCell align="right">
                        {run.status === "running" && (
                          <Tooltip title="Stop Training">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleStop(run.id);
                              }}
                            >
                              <StopIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {run.status !== "running" && (
                          <Tooltip title="Delete Run">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleDelete(run.id);
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {runs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Typography color="text.secondary" variant="body2" sx={{ py: 2, textAlign: "center" }}>
                        No training runs yet. Select an experiment and click Start Training.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* Run Detail */}
        <Grid item xs={12} lg={5}>
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            {selectedRun ? (
              <Stack spacing={2}>
                <Typography variant="h6" fontWeight={700}>
                  Run #{selectedRun.id} Details
                </Typography>

                <Stack direction="row" spacing={2} alignItems="center">
                  <RunStatusBadge status={selectedRun.status} size="medium" />
                  <Typography variant="body2" color="text.secondary">
                    {formatDuration(selectedRun.started_at, selectedRun.finished_at)}
                  </Typography>
                </Stack>

                {/* Progress bar */}
                {selectedRun.status === "running" && progress && (
                  <Box>
                    <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                      <Typography variant="body2" fontWeight={600}>
                        Epoch {progress.current_epoch} / {progress.total_epochs || "?"}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {progress.total_epochs
                          ? `${((progress.current_epoch / progress.total_epochs) * 100).toFixed(0)}%`
                          : "—"}
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={
                        progress.total_epochs
                          ? (progress.current_epoch / progress.total_epochs) * 100
                          : 0
                      }
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        bgcolor: "action.hover",
                        "& .MuiLinearProgress-bar": {
                          borderRadius: 4,
                          background: "linear-gradient(90deg, #176b6b, #1a8a8a)",
                        },
                      }}
                    />
                  </Box>
                )}

                {/* Mini metric charts */}
                <Grid container spacing={2}>
                  {lossData.length > 0 && (
                    <Grid item xs={12} sm={6}>
                      <MetricMiniChart title="Total Loss" data={lossData} color="#ef5350" />
                    </Grid>
                  )}
                  {mapData.length > 0 && (
                    <Grid item xs={12} sm={6}>
                      <MetricMiniChart title="mAP50" data={mapData} color="#66bb6a" />
                    </Grid>
                  )}
                  {precisionData.length > 0 && (
                    <Grid item xs={12} sm={6}>
                      <MetricMiniChart title="Precision" data={precisionData} color="#42a5f5" />
                    </Grid>
                  )}
                  {recallData.length > 0 && (
                    <Grid item xs={12} sm={6}>
                      <MetricMiniChart title="Recall" data={recallData} color="#ab47bc" />
                    </Grid>
                  )}
                </Grid>

                {lossData.length === 0 && mapData.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: "italic" }}>
                    {selectedRun.status === "running"
                      ? "Waiting for training metrics…"
                      : "No metric data available for this run."}
                  </Typography>
                )}

                {/* Command */}
                <Box>
                  <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                    Command
                  </Typography>
                  <Box
                    sx={{
                      bgcolor: "#0d1117",
                      color: "#e0e0e0",
                      p: 1.5,
                      borderRadius: 1,
                      fontFamily: "monospace",
                      fontSize: 11,
                      wordBreak: "break-all",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {selectedRun.command || "—"}
                  </Box>
                </Box>
              </Stack>
            ) : (
              <Typography color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
                Select a run to view details
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}
