import {
  Alert,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";

import { createLogSocket } from "../api/client";
import { LogTerminal } from "../components/LogTerminal";
import { useDashboardStore } from "../store";
import type { LogStreamMessage } from "../types";

export function LiveLogsPage() {
  const { runs, loadRuns } = useDashboardStore();
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [lines, setLines] = useState<LogStreamMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  // Auto-select the latest running run
  useEffect(() => {
    if (selectedRunId == null) {
      const runningRun = runs.find((r) => r.status === "running");
      if (runningRun) {
        setSelectedRunId(runningRun.id);
      } else if (runs.length > 0) {
        setSelectedRunId(runs[0].id);
      }
    }
  }, [runs, selectedRunId]);

  const connectWs = useCallback((runId: number) => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setLines([]);
    setConnected(false);
    setError(null);

    const ws = createLogSocket(
      runId,
      (data) => {
        const msg = data as LogStreamMessage;
        if (msg.type === "heartbeat") return;
        setLines((prev) => [...prev, msg]);
      },
      () => {
        setConnected(false);
      },
    );

    ws.onopen = () => setConnected(true);
    ws.onerror = () => setError("WebSocket connection failed. Is the backend running?");
    wsRef.current = ws;
  }, []);

  // Connect/reconnect when run selection changes
  useEffect(() => {
    if (selectedRunId == null) return;
    connectWs(selectedRunId);
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [selectedRunId, connectWs]);

  const selectedRun = runs.find((r) => r.id === selectedRunId);

  return (
    <Stack spacing={3}>
      {error && (
        <Alert severity="warning" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Run Selector */}
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          borderRadius: 2,
          background:
            "linear-gradient(135deg, rgba(13,17,23,0.03) 0%, rgba(23,107,107,0.03) 100%)",
        }}
      >
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems="center"
        >
          <Typography variant="h6" fontWeight={700}>
            📟 Live Terminal
          </Typography>
          <FormControl size="small" sx={{ minWidth: 300 }}>
            <InputLabel>Select Run</InputLabel>
            <Select
              label="Select Run"
              value={selectedRunId ?? ""}
              onChange={(e) => setSelectedRunId(e.target.value as number)}
            >
              {runs.map((run) => (
                <MenuItem key={run.id} value={run.id}>
                  Run #{run.id} — {run.status}
                  {run.metadata_json?.experiment_name
                    ? ` (${run.metadata_json.experiment_name})`
                    : ""}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ ml: "auto" }}>
            <Typography
              variant="caption"
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.5,
                color: connected ? "success.main" : "text.secondary",
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: connected ? "#66bb6a" : "#bdbdbd",
                  display: "inline-block",
                }}
              />
              {connected ? "Connected" : "Disconnected"}
            </Typography>
          </Stack>
        </Stack>
      </Paper>

      {/* Terminal */}
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        {selectedRunId ? (
          <LogTerminal
            lines={lines}
            title={
              selectedRun
                ? `Run #${selectedRun.id} — ${selectedRun.status}`
                : "Live Terminal"
            }
          />
        ) : (
          <Typography
            color="text.secondary"
            sx={{ py: 8, textAlign: "center" }}
          >
            No runs available. Start a training run to view live logs.
          </Typography>
        )}
      </Paper>
    </Stack>
  );
}
