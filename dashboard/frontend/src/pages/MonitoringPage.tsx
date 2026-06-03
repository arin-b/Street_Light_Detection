import DeviceThermostatIcon from "@mui/icons-material/DeviceThermostat";
import MemoryIcon from "@mui/icons-material/Memory";
import NetworkCheckIcon from "@mui/icons-material/NetworkCheck";
import StorageIcon from "@mui/icons-material/Storage";
import {
  Alert,
  Box,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, createMonitoringSocket } from "../api/client";
import { GaugeChart } from "../components/GaugeChart";
import { useDashboardStore } from "../store";
import type { GPUInfo, SystemMetrics } from "../types";

export function MonitoringPage() {
  const { latestMetrics, metricsHistory, pushMetrics } = useDashboardStore();
  const [gpuInfo, setGpuInfo] = useState<GPUInfo | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Load GPU info once
  useEffect(() => {
    api.gpuInfo().then(setGpuInfo).catch(() => {});
  }, []);

  // Connect monitoring WebSocket
  const connectWs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = createMonitoringSocket(
      (data) => {
        pushMetrics(data as SystemMetrics);
      },
      () => {
        setConnected(false);
        // Auto-reconnect after 3 seconds
        setTimeout(connectWs, 3000);
      },
    );

    ws.onopen = () => {
      setConnected(true);
      setError(null);
    };
    ws.onerror = () => {
      setError("Monitoring WebSocket failed. Retrying…");
    };

    wsRef.current = ws;
  }, [pushMetrics]);

  useEffect(() => {
    connectWs();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connectWs]);

  const m = latestMetrics;
  const gpu = m?.gpu ?? null;

  // History chart data (last ~60 points for display)
  const chartData = metricsHistory.slice(-60).map((point, idx) => ({
    idx,
    cpu: point.cpu_percent,
    ram: point.ram_percent,
    gpu: point.gpu?.percent ?? 0,
  }));

  return (
    <Stack spacing={3}>
      {error && (
        <Alert severity="warning" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h6" fontWeight={700}>
          📊 Monitoring Center
        </Typography>
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
          {connected ? "Live • Updating every 1s" : "Disconnected"}
        </Typography>
      </Stack>

      {/* Gauge Row */}
      <Paper
        variant="outlined"
        sx={{
          p: 3,
          borderRadius: 2,
          background:
            "linear-gradient(135deg, rgba(23,107,107,0.02) 0%, rgba(169,91,34,0.02) 100%)",
        }}
      >
        <Grid container spacing={3} justifyContent="center" alignItems="flex-start">
          <Grid item xs={6} sm={4} md={2}>
            <GaugeChart
              label="CPU"
              value={m?.cpu_percent ?? 0}
              subtitle="Utilization"
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <GaugeChart
              label="RAM"
              value={m?.ram_percent ?? 0}
              subtitle={
                m
                  ? `${(m.ram_used_mb / 1024).toFixed(1)} / ${(m.ram_total_mb / 1024).toFixed(1)} GB`
                  : "—"
              }
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <GaugeChart
              label="Disk"
              value={m?.disk_percent ?? 0}
              subtitle={
                m
                  ? `${m.disk_used_gb.toFixed(0)} / ${m.disk_total_gb.toFixed(0)} GB`
                  : "—"
              }
            />
          </Grid>
          {gpu && (
            <>
              <Grid item xs={6} sm={4} md={2}>
                <GaugeChart
                  label="GPU"
                  value={gpu.percent}
                  color="#ab47bc"
                  subtitle={gpu.name || "NVIDIA GPU"}
                />
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <GaugeChart
                  label="VRAM"
                  value={
                    gpu.vram_total_mb > 0
                      ? (gpu.vram_used_mb / gpu.vram_total_mb) * 100
                      : 0
                  }
                  color="#42a5f5"
                  subtitle={`${(gpu.vram_used_mb / 1024).toFixed(1)} / ${(gpu.vram_total_mb / 1024).toFixed(1)} GB`}
                />
              </Grid>
            </>
          )}
        </Grid>
      </Paper>

      {/* GPU Details */}
      {gpu && (
        <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
          <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>
            GPU Details
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Stack direction="row" spacing={1} alignItems="center">
                <DeviceThermostatIcon
                  sx={{
                    color:
                      gpu.temperature > 80
                        ? "error.main"
                        : gpu.temperature > 60
                          ? "warning.main"
                          : "success.main",
                    fontSize: 20,
                  }}
                />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Temperature
                  </Typography>
                  <Typography variant="body2" fontWeight={700}>
                    {gpu.temperature.toFixed(0)}°C
                  </Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Stack direction="row" spacing={1} alignItems="center">
                <MemoryIcon sx={{ color: "primary.main", fontSize: 20 }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Power Draw
                  </Typography>
                  <Typography variant="body2" fontWeight={700}>
                    {gpu.power_watts.toFixed(0)} W
                  </Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Stack direction="row" spacing={1} alignItems="center">
                <StorageIcon sx={{ color: "secondary.main", fontSize: 20 }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Clock Speed
                  </Typography>
                  <Typography variant="body2" fontWeight={700}>
                    {gpu.clock_mhz.toFixed(0)} MHz
                  </Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Stack direction="row" spacing={1} alignItems="center">
                <NetworkCheckIcon sx={{ color: "info.main", fontSize: 20 }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Fan Speed
                  </Typography>
                  <Typography variant="body2" fontWeight={700}>
                    {gpu.fan_percent.toFixed(0)}%
                  </Typography>
                </Box>
              </Stack>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Network */}
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>
          Network I/O
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              Upload (TX)
            </Typography>
            <Typography variant="h6" fontWeight={700}>
              {m?.net_sent_mbps?.toFixed(2) ?? "0.00"} MB/s
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              Download (RX)
            </Typography>
            <Typography variant="h6" fontWeight={700}>
              {m?.net_recv_mbps?.toFixed(2) ?? "0.00"} MB/s
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Historical Chart */}
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>
          Utilization History (last 60 seconds)
        </Typography>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="gradCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#42a5f5" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#42a5f5" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradRam" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#66bb6a" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#66bb6a" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradGpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ab47bc" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ab47bc" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
            <XAxis dataKey="idx" hide />
            <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} width={45} />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                fontSize: 12,
                border: "1px solid rgba(0,0,0,0.1)",
              }}
              formatter={(value: any, name: any) => [
                `${Number(value).toFixed(1)}%`,
                String(name).toUpperCase(),
              ]}
            />
            <Area
              type="monotone"
              dataKey="cpu"
              stroke="#42a5f5"
              strokeWidth={2}
              fill="url(#gradCpu)"
              dot={false}
              animationDuration={200}
            />
            <Area
              type="monotone"
              dataKey="ram"
              stroke="#66bb6a"
              strokeWidth={2}
              fill="url(#gradRam)"
              dot={false}
              animationDuration={200}
            />
            {gpu && (
              <Area
                type="monotone"
                dataKey="gpu"
                stroke="#ab47bc"
                strokeWidth={2}
                fill="url(#gradGpu)"
                dot={false}
                animationDuration={200}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
        <Stack direction="row" spacing={3} justifyContent="center" sx={{ mt: 1 }}>
          <Typography variant="caption" sx={{ color: "#42a5f5", fontWeight: 600 }}>
            ● CPU
          </Typography>
          <Typography variant="caption" sx={{ color: "#66bb6a", fontWeight: 600 }}>
            ● RAM
          </Typography>
          {gpu && (
            <Typography variant="caption" sx={{ color: "#ab47bc", fontWeight: 600 }}>
              ● GPU
            </Typography>
          )}
        </Stack>
      </Paper>

      {/* GPU Info Card */}
      {gpuInfo?.available && (
        <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
          <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>
            GPU Device Info
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary">
                Device Name
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {gpuInfo.name}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary">
                Driver Version
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {gpuInfo.driver_version}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary">
                VRAM Total
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {(gpuInfo.vram_total_mb / 1024).toFixed(1)} GB
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Stack>
  );
}
