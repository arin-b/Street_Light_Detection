import {
  Alert,
  Box,
  Button,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useDashboardStore } from "../store";

export function SweepsPage() {
  const { experiments, loadExperiments } = useDashboardStore();
  const [baseExperimentId, setBaseExperimentId] = useState<number | "">("");
  const [paramKey, setParamKey] = useState("training.learning_rate");
  const [paramValues, setParamValues] = useState("0.01, 0.001");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    void loadExperiments();
  }, [loadExperiments]);

  const handleGenerate = async () => {
    if (!baseExperimentId) {
      setError("Please select a base experiment");
      return;
    }

    try {
      setError(null);
      setSuccess(null);
      setIsSubmitting(true);
      
      const parsedValues = paramValues.split(",").map((v) => {
        const trimmed = v.trim();
        if (!isNaN(Number(trimmed))) {
          return Number(trimmed);
        }
        if (trimmed === "true") return true;
        if (trimmed === "false") return false;
        return trimmed;
      });

      const params = {
        [paramKey]: parsedValues
      };

      const newExps = await api.createSweep(Number(baseExperimentId), params);
      setSuccess(`Successfully generated ${newExps.length} sweep combinations! They are now in your Experiments list.`);
      void loadExperiments();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate sweep");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Stack spacing={3} maxWidth={800} mx="auto">
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" onClose={() => setSuccess(null)}>{success}</Alert>}

      <Typography variant="h5" fontWeight={800}>
        🧪 Hyperparameter Sweeps
      </Typography>

      <Paper variant="outlined" sx={{ p: 3, borderRadius: 2 }}>
        <Stack spacing={3}>
          <Typography variant="subtitle1" fontWeight={700}>
            Grid Search Configuration
          </Typography>
          
          <FormControl fullWidth size="small">
            <InputLabel>Base Experiment</InputLabel>
            <Select
              value={baseExperimentId}
              label="Base Experiment"
              onChange={(e) => setBaseExperimentId(e.target.value as number)}
            >
              {experiments.map((exp) => (
                <MenuItem key={exp.id} value={exp.id}>
                  #{exp.id} - {exp.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                size="small"
                label="Parameter Key (e.g. training.batch_size)"
                value={paramKey}
                onChange={(e) => setParamKey(e.target.value)}
                placeholder="training.learning_rate"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                size="small"
                label="Values (comma separated)"
                value={paramValues}
                onChange={(e) => setParamValues(e.target.value)}
                placeholder="0.01, 0.001"
              />
            </Grid>
          </Grid>
          
          <Box pt={2}>
            <Button
              variant="contained"
              onClick={handleGenerate}
              disabled={isSubmitting || !baseExperimentId}
            >
              Generate Sweep Combinations
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Stack>
  );
}
