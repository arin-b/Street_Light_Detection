import type {
  ArtifactSummary,
  AttentionMap,
  DashboardSummary,
  Experiment,
  ExperimentCreate,
  ExperimentStatus,
  GPUInfo,
  LogEntry,
  Run,
  RunProgress,
  SystemMetrics,
  TrackingVideoSummary,
  YAMLConfigRead,
  YAMLConfigSummary,
  YAMLValidationResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

// ---------------------------------------------------------------------------
// WebSocket helpers
// ---------------------------------------------------------------------------

function wsBase(): string {
  const loc = window.location;
  const proto = loc.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${loc.host}${API_BASE}`;
}

export function createLogSocket(
  runId: number,
  onMessage: (data: unknown) => void,
  onClose?: () => void,
): WebSocket {
  const ws = new WebSocket(`${wsBase()}/ws/logs/${runId}`);
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      /* ignore malformed */
    }
  };
  ws.onclose = () => onClose?.();
  ws.onerror = () => onClose?.();
  return ws;
}

export function createMonitoringSocket(
  onMessage: (data: unknown) => void,
  onClose?: () => void,
): WebSocket {
  const ws = new WebSocket(`${wsBase()}/ws/monitoring`);
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      /* ignore malformed */
    }
  };
  ws.onclose = () => onClose?.();
  ws.onerror = () => onClose?.();
  return ws;
}

// ---------------------------------------------------------------------------
// REST API
// ---------------------------------------------------------------------------

export const api = {
  // Phase 1 — Dashboard
  summary: () => request<DashboardSummary>("/summary"),
  experiments: () => request<Experiment[]>("/experiments"),
  createExperiment: (payload: ExperimentCreate) =>
    request<Experiment>("/experiments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateExperiment: (
    id: number,
    payload: Partial<{
      name: string;
      description: string;
      status: ExperimentStatus;
      tags: string[];
      config_path: string | null;
      config: Record<string, unknown>;
    }>,
  ) =>
    request<Experiment>(`/experiments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteExperiment: (id: number) =>
    request<void>(`/experiments/${id}`, {
      method: "DELETE",
    }),
  duplicateExperiment: (id: number, name: string) =>
    request<Experiment>(`/experiments/${id}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  // Phase 1 — YAML
  yamlConfigs: () => request<YAMLConfigSummary[]>("/yaml-configs"),
  readYaml: (path: string) =>
    request<YAMLConfigRead>(
      `/yaml-configs/file?path=${encodeURIComponent(path)}`,
    ),
  writeYaml: (path: string, content: string) =>
    request<YAMLConfigRead>("/yaml-configs/file", {
      method: "PUT",
      body: JSON.stringify({ path, content }),
    }),
  validateYaml: (content: string) =>
    request<YAMLValidationResponse>("/yaml-configs/validate", {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  // Phase 2 — Training runs
  listRuns: (params?: { status?: string; experiment_id?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.experiment_id != null)
      searchParams.set("experiment_id", String(params.experiment_id));
    const qs = searchParams.toString();
    return request<Run[]>(`/runs${qs ? `?${qs}` : ""}`);
  },
  getRun: (runId: number) => request<Run>(`/runs/${runId}`),
  startTraining: (experimentId: number) =>
    request<Run>(`/runs/${experimentId}/start`, { method: "POST" }),
  stopTraining: (runId: number) =>
    request<Run>(`/runs/${runId}/stop`, { method: "POST" }),
  deleteRun: (runId: number) =>
    request<void>(`/runs/${runId}`, { method: "DELETE" }),
  getRunLogs: (runId: number, limit = 500, offset = 0) =>
    request<LogEntry[]>(
      `/runs/${runId}/logs?limit=${limit}&offset=${offset}`,
    ),
  getRunProgress: (runId: number) =>
    request<RunProgress>(`/runs/${runId}/progress`),

  // Phase 2 — Monitoring
  monitoringSnapshot: () => request<SystemMetrics>("/monitoring/snapshot"),
  monitoringHistory: (minutes = 5) =>
    request<Record<string, unknown>[]>(
      `/monitoring/history?minutes=${minutes}`,
    ),
  gpuInfo: () => request<GPUInfo>("/monitoring/gpu-info"),

  // Phase 3 — Visualizations & Tracking
  compareRuns: (runIds: number[]) => {
    const searchParams = new URLSearchParams();
    runIds.forEach((id) => searchParams.append("run_ids", String(id)));
    return request<Record<string, Record<string, number>[]>>(`/visualizations/compare?${searchParams.toString()}`);
  },
  listRunArtifacts: (runId: number) =>
    request<ArtifactSummary[]>(`/visualizations/${runId}/artifacts`),
  getArtifactUrl: (runId: number, filename: string) =>
    `${API_BASE}/visualizations/${runId}/artifacts/${encodeURIComponent(filename)}`,

  listAttentionMaps: (imageId?: string) => {
    const qs = imageId ? `?image_id=${encodeURIComponent(imageId)}` : "";
    return request<AttentionMap[]>(`/attention/maps${qs}`);
  },

  listTrackingVideos: () => request<TrackingVideoSummary[]>("/tracking/videos"),
  getTrackingVideoUrl: (filename: string) =>
    `${API_BASE}/tracking/videos/${encodeURIComponent(filename)}`,
  getTrackingTrajectories: (filename: string) =>
    request<Record<string, unknown>>(`/tracking/trajectories/${encodeURIComponent(filename)}`),

  // Phase 4 — Sweeps & Reports
  createSweep: (baseExperimentId: number, parameters: Record<string, any[]>) =>
    request<Experiment[]>("/sweeps", {
      method: "POST",
      body: JSON.stringify({ base_experiment_id: baseExperimentId, parameters }),
    }),
  getReportUrl: (runId: number) => `${API_BASE}/reports/${runId}/pdf`,
};
