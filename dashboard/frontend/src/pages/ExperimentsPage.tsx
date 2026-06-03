import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteIcon from "@mui/icons-material/Delete";
import SaveIcon from "@mui/icons-material/Save";
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { useDashboardStore } from "../store";
import type { Experiment, ExperimentStatus } from "../types";

const statuses: ExperimentStatus[] = ["draft", "queued", "running", "completed", "failed", "cancelled", "archived"];
const modelVariants = ["YOLO26n", "YOLO26s", "YOLO26m", "YOLO26l", "YOLO26x"];

export function ExperimentsPage() {
  const { experiments, yamlConfigs, error, loadExperiments, loadYamlConfigs } = useDashboardStore();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    dataset: "src/rbccps_od/config/original.yaml",
    modelVariant: "YOLO26m",
    epochs: 100,
    batchSize: 16,
    imageSize: 640
  });

  useEffect(() => {
    void loadExperiments();
    void loadYamlConfigs();
  }, [loadExperiments, loadYamlConfigs]);

  const selected = useMemo(
    () => experiments.find((experiment) => experiment.id === selectedId) ?? experiments[0],
    [experiments, selectedId]
  );

  async function createExperiment() {
    if (!form.name.trim()) {
      setMessage("Experiment name is required.");
      return;
    }
    await api.createExperiment({
      name: form.name.trim(),
      description: form.description,
      dataset: form.dataset,
      model_variant: form.modelVariant,
      training: {
        epochs: form.epochs,
        batch_size: form.batchSize,
        image_size: form.imageSize
      }
    });
    setMessage("Experiment created.");
    setForm((current) => ({ ...current, name: "", description: "" }));
    await loadExperiments();
    await loadYamlConfigs();
  }

  async function updateExperiment(experiment: Experiment) {
    await api.updateExperiment(experiment.id, {
      name: experiment.name,
      description: experiment.description,
      status: experiment.status as ExperimentStatus
    });
    setMessage("Experiment saved.");
    await loadExperiments();
  }

  async function duplicateExperiment(experiment: Experiment) {
    await api.duplicateExperiment(experiment.id, `${experiment.name} Copy`);
    setMessage("Experiment duplicated.");
    await loadExperiments();
    await loadYamlConfigs();
  }

  async function deleteExperiment(experiment: Experiment) {
    await api.deleteExperiment(experiment.id);
    setSelectedId(null);
    setMessage("Experiment deleted.");
    await loadExperiments();
  }

  function patchSelected(patch: Partial<Experiment>) {
    if (!selected) {
      return;
    }
    useDashboardStore.setState({
      experiments: experiments.map((experiment) =>
        experiment.id === selected.id ? { ...experiment, ...patch } : experiment
      )
    });
  }

  return (
    <Stack spacing={3}>
      {(error || message) && <Alert severity={error ? "error" : "success"}>{error || message}</Alert>}

      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Stack spacing={2}>
          <Typography variant="h6">New Experiment</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Dataset YAML</InputLabel>
                <Select
                  label="Dataset YAML"
                  value={form.dataset}
                  onChange={(event) => setForm({ ...form, dataset: event.target.value })}
                >
                  {yamlConfigs.map((config) => (
                    <MenuItem key={config.path} value={config.path}>
                      {config.path}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Model Variant</InputLabel>
                <Select
                  label="Model Variant"
                  value={form.modelVariant}
                  onChange={(event) => setForm({ ...form, modelVariant: event.target.value })}
                >
                  {modelVariants.map((variant) => (
                    <MenuItem key={variant} value={variant}>
                      {variant}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Epochs"
                value={form.epochs}
                onChange={(event) => setForm({ ...form, epochs: Number(event.target.value) })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Batch Size"
                value={form.batchSize}
                onChange={(event) => setForm({ ...form, batchSize: Number(event.target.value) })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Image Size"
                value={form.imageSize}
                onChange={(event) => setForm({ ...form, imageSize: Number(event.target.value) })}
              />
            </Grid>
          </Grid>
          <Box>
            <Button startIcon={<SaveIcon />} onClick={() => void createExperiment()}>
              Create
            </Button>
          </Box>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={7}>
          <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>YAML</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {experiments.map((experiment) => (
                  <TableRow
                    key={experiment.id}
                    hover
                    selected={selected?.id === experiment.id}
                    onClick={() => setSelectedId(experiment.id)}
                    sx={{ cursor: "pointer" }}
                  >
                    <TableCell>{experiment.name}</TableCell>
                    <TableCell>
                      <Chip size="small" label={experiment.status} />
                    </TableCell>
                    <TableCell>{experiment.config_path}</TableCell>
                    <TableCell align="right">
                      <IconButton title="Duplicate" onClick={() => void duplicateExperiment(experiment)}>
                        <ContentCopyIcon fontSize="small" />
                      </IconButton>
                      <IconButton title="Delete" onClick={() => void deleteExperiment(experiment)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        <Grid item xs={12} lg={5}>
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            {selected ? (
              <Stack spacing={2}>
                <Typography variant="h6">Experiment Details</Typography>
                <TextField fullWidth label="Name" value={selected.name} onChange={(event) => patchSelected({ name: event.target.value })} />
                <TextField
                  fullWidth
                  label="Description"
                  value={selected.description}
                  onChange={(event) => patchSelected({ description: event.target.value })}
                />
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    label="Status"
                    value={selected.status}
                    onChange={(event) => patchSelected({ status: event.target.value })}
                  >
                    {statuses.map((status) => (
                      <MenuItem key={status} value={status}>
                        {status}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField fullWidth label="Config Path" value={selected.config_path ?? ""} InputProps={{ readOnly: true }} />
                <Button startIcon={<SaveIcon />} onClick={() => void updateExperiment(selected)}>
                  Save
                </Button>
              </Stack>
            ) : (
              <Typography color="text.secondary">No experiment selected.</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}
