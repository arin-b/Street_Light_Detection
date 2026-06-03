import { create } from "zustand";

import { api } from "./api/client";
import type {
  DashboardSummary,
  Experiment,
  Run,
  SystemMetrics,
  YAMLConfigSummary,
} from "./types";

interface DashboardState {
  // Phase 1
  summary: DashboardSummary | null;
  experiments: Experiment[];
  yamlConfigs: YAMLConfigSummary[];
  loading: boolean;
  error: string | null;
  loadSummary: () => Promise<void>;
  loadExperiments: () => Promise<void>;
  loadYamlConfigs: () => Promise<void>;

  // Phase 2 — Training
  runs: Run[];
  activeRunId: number | null;
  loadRuns: () => Promise<void>;
  setActiveRunId: (id: number | null) => void;

  // Phase 2 — Monitoring
  latestMetrics: SystemMetrics | null;
  metricsHistory: SystemMetrics[];
  pushMetrics: (m: SystemMetrics) => void;
}

function friendlyError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected dashboard error";
}

const MAX_HISTORY = 300; // ~5 minutes at 1s intervals

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Phase 1
  summary: null,
  experiments: [],
  yamlConfigs: [],
  loading: false,
  error: null,
  loadSummary: async () => {
    set({ loading: true, error: null });
    try {
      set({ summary: await api.summary(), loading: false });
    } catch (error) {
      set({ error: friendlyError(error), loading: false });
    }
  },
  loadExperiments: async () => {
    set({ loading: true, error: null });
    try {
      set({ experiments: await api.experiments(), loading: false });
    } catch (error) {
      set({ error: friendlyError(error), loading: false });
    }
  },
  loadYamlConfigs: async () => {
    set({ loading: true, error: null });
    try {
      set({ yamlConfigs: await api.yamlConfigs(), loading: false });
    } catch (error) {
      set({ error: friendlyError(error), loading: false });
    }
  },

  // Phase 2 — Training
  runs: [],
  activeRunId: null,
  loadRuns: async () => {
    try {
      set({ runs: await api.listRuns() });
    } catch (error) {
      set({ error: friendlyError(error) });
    }
  },
  setActiveRunId: (id) => set({ activeRunId: id }),

  // Phase 2 — Monitoring
  latestMetrics: null,
  metricsHistory: [],
  pushMetrics: (m) => {
    const history = [...get().metricsHistory, m].slice(-MAX_HISTORY);
    set({ latestMetrics: m, metricsHistory: history });
  },
}));
