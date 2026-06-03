import {
  Alert,
  Box,
  Button,
  Card,
  CardMedia,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  OutlinedInput,
  Paper,
  Select,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "../api/client";
import { useDashboardStore } from "../store";
import type { ArtifactSummary } from "../types";

const COLORS = [
  "#42a5f5",
  "#66bb6a",
  "#ffa726",
  "#ab47bc",
  "#ef5350",
  "#26c6da",
];

export function VisualizationPage() {
  const { runs, loadRuns } = useDashboardStore();
  const [selectedRunIds, setSelectedRunIds] = useState<number[]>([]);
  const [tab, setTab] = useState(0);
  const [comparisonData, setComparisonData] = useState<Record<string, Record<string, number>[]>>({});
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  // Load comparison data when selected runs change
  useEffect(() => {
    if (selectedRunIds.length === 0) {
      setComparisonData({});
      return;
    }
    api.compareRuns(selectedRunIds)
      .then(setComparisonData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load comparison data"));
  }, [selectedRunIds]);

  // Load artifacts when the single run selection changes (we just pick the first selected run for artifacts)
  useEffect(() => {
    if (selectedRunIds.length === 0) {
      setArtifacts([]);
      return;
    }
    // Only show artifacts for the primary selected run to avoid clutter
    const primaryRunId = selectedRunIds[0];
    api.listRunArtifacts(primaryRunId)
      .then(setArtifacts)
      .catch(() => setArtifacts([]));
  }, [selectedRunIds]);

  const handleRunSelect = (event: any) => {
    const value = event.target.value;
    setSelectedRunIds(typeof value === "string" ? value.split(",").map(Number) : value);
  };

  const activeRuns = runs.filter((r) => r.status === "completed" || r.status === "failed" || r.status === "running");

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}

      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Stack direction="row" spacing={3} alignItems="center">
          <Typography variant="h6" fontWeight={700}>
            📈 Visualization Center
          </Typography>
          <FormControl sx={{ minWidth: 300, maxWidth: 500 }} size="small">
            <InputLabel>Select Runs to Compare</InputLabel>
            <Select
              multiple
              value={selectedRunIds}
              onChange={handleRunSelect}
              input={<OutlinedInput label="Select Runs to Compare" />}
              renderValue={(selected) => (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={`Run #${value}`} size="small" />
                  ))}
                </Box>
              )}
            >
              {activeRuns.map((run) => (
                <MenuItem key={run.id} value={run.id}>
                  Run #{run.id} — {String(run.metadata_json?.experiment_name || "Unknown")}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      {selectedRunIds.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 4, textAlign: "center", borderRadius: 2 }}>
          <Typography color="text.secondary">
            Select one or more runs above to view metrics and artifacts.
          </Typography>
        </Paper>
      ) : (
        <Box>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: 1, borderColor: "divider", mb: 2 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="Metrics Comparison" />
              <Tab label={`Artifacts (Run #${selectedRunIds[0]})`} />
            </Tabs>
            {selectedRunIds.length === 1 && (
              <Button
                variant="outlined"
                color="secondary"
                size="small"
                onClick={() => window.open(api.getReportUrl(selectedRunIds[0]), "_blank")}
              >
                📄 Download PDF Report
              </Button>
            )}
          </Box>

          {/* Metrics Comparison Tab */}
          {tab === 0 && (
            <Grid container spacing={3}>
              {Object.keys(comparisonData).length === 0 ? (
                <Grid item xs={12}>
                  <Typography color="text.secondary" sx={{ fontStyle: "italic" }}>
                    No metric data available for the selected runs.
                  </Typography>
                </Grid>
              ) : (
                Object.entries(comparisonData).map(([metricName, data]) => (
                  <Grid item xs={12} lg={6} key={metricName}>
                    <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                      <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 2 }}>
                        {metricName}
                      </Typography>
                      <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                          <XAxis dataKey="step" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} domain={["auto", "auto"]} width={45} />
                          <Tooltip
                            contentStyle={{ borderRadius: 8, fontSize: 12, border: "1px solid rgba(255,255,255,0.1)", background: "#1e1e1e" }}
                            labelFormatter={(l) => `Epoch ${l}`}
                          />
                          <Legend wrapperStyle={{ fontSize: 12 }} />
                          {selectedRunIds.map((runId, idx) => (
                            <Line
                              key={runId}
                              type="monotone"
                              dataKey={`run_${runId}`}
                              name={`Run #${runId}`}
                              stroke={COLORS[idx % COLORS.length]}
                              strokeWidth={2}
                              dot={false}
                              activeDot={{ r: 4 }}
                            />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    </Paper>
                  </Grid>
                ))
              )}
            </Grid>
          )}

          {/* Artifacts Tab */}
          {tab === 1 && (
            <Grid container spacing={2}>
              {artifacts.length === 0 ? (
                <Grid item xs={12}>
                  <Typography color="text.secondary" sx={{ fontStyle: "italic" }}>
                    No image artifacts found in the output directory for Run #{selectedRunIds[0]}.
                  </Typography>
                </Grid>
              ) : (
                artifacts.map((artifact) => (
                  <Grid item xs={12} sm={6} md={4} key={artifact.filename}>
                    <Card variant="outlined" sx={{ borderRadius: 2 }}>
                      <CardMedia
                        component="img"
                        height="200"
                        image={api.getArtifactUrl(selectedRunIds[0], artifact.filename)}
                        alt={artifact.filename}
                        sx={{ objectFit: "contain", bgcolor: "#000", cursor: "pointer" }}
                        onClick={() => window.open(api.getArtifactUrl(selectedRunIds[0], artifact.filename), "_blank")}
                      />
                      <Box sx={{ p: 1, borderTop: "1px solid", borderColor: "divider", bgcolor: "background.default" }}>
                        <Typography variant="caption" fontWeight={600} noWrap>
                          {artifact.filename}
                        </Typography>
                        <Typography variant="caption" display="block" color="text.secondary" sx={{ textTransform: "capitalize" }}>
                          {artifact.category.replace("_", " ")}
                        </Typography>
                      </Box>
                    </Card>
                  </Grid>
                ))
              )}
            </Grid>
          )}
        </Box>
      )}
    </Stack>
  );
}
