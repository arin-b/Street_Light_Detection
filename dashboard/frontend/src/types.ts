export type ExperimentStatus =
  | "draft"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "archived";

export interface Experiment {
  id: number;
  name: string;
  description: string;
  status: ExperimentStatus | string;
  config_path: string | null;
  config_snapshot: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ExperimentCreate {
  name: string;
  description?: string;
  status?: ExperimentStatus;
  config_path?: string | null;
  dataset?: string | null;
  model_variant?: string;
  training?: Record<string, unknown>;
}

export interface DashboardSummary {
  experiments_total: number;
  experiments_active: number;
  experiments_completed: number;
  experiments_failed: number;
  yaml_configs: number;
  cpu_percent: number | null;
  ram_percent: number | null;
}

export interface YAMLConfigSummary {
  path: string;
  name: string;
  size_bytes: number;
  modified_at: string;
}

export interface YAMLConfigRead {
  path: string;
  content: string;
  parsed: unknown;
  modified_at: string;
}

export interface YAMLValidationResponse {
  valid: boolean;
  parsed: unknown;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Phase 2 — Training runs
// ---------------------------------------------------------------------------

export type RunStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export interface Run {
  id: number;
  experiment_id: number;
  status: RunStatus | string;
  command: string;
  started_at: string | null;
  finished_at: string | null;
  output_dir: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface RunProgress {
  current_epoch: number;
  total_epochs: number;
  is_running: boolean;
}

export interface LogEntry {
  id: number;
  run_id: number;
  level: string;
  message: string;
  stream: string;
  created_at: string;
}

export interface LogStreamMessage {
  type?: string; // "heartbeat" for keep-alive
  stream: string;
  level: string;
  message: string;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Phase 2 — Monitoring
// ---------------------------------------------------------------------------

export interface GPUMetrics {
  index: number;
  name: string;
  percent: number;
  vram_used_mb: number;
  vram_free_mb: number;
  vram_total_mb: number;
  temperature: number;
  power_watts: number;
  clock_mhz: number;
  fan_percent: number;
}

export interface SystemMetrics {
  cpu_percent: number;
  ram_percent: number;
  ram_used_mb: number;
  ram_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  net_sent_mbps: number;
  net_recv_mbps: number;
  gpu: GPUMetrics | null;
  timestamp: string;
}

export interface GPUInfo {
  available: boolean;
  name: string;
  driver_version: string;
  vram_total_mb: number;
}

// ---------------------------------------------------------------------------
// Phase 3 — Visualizations & Tracking
// ---------------------------------------------------------------------------

export interface ArtifactSummary {
  filename: string;
  category: "predictions" | "labels" | "confusion_matrix" | "results_plot" | "curves" | "other";
}

export interface TrackingVideoSummary {
  filename: string;
  has_trajectories: boolean;
  size_bytes: number;
}

export interface TrackedObject {
  id: number;
  frame: number;
  bbox: [number, number, number, number];
  confidence: number;
  class_id: number;
}

export interface AttentionMap {
  id: string;
  layer: string;
  url: string;
}
