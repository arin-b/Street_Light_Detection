import CheckIcon from "@mui/icons-material/Check";
import SaveIcon from "@mui/icons-material/Save";
import {
  Alert,
  Button,
  Grid,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  TextField,
  Typography
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { useDashboardStore } from "../store";

export function YamlEditorPage() {
  const { yamlConfigs, error, loadYamlConfigs } = useDashboardStore();
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    void loadYamlConfigs();
  }, [loadYamlConfigs]);

  const selected = useMemo(
    () => yamlConfigs.find((config) => config.path === selectedPath) ?? yamlConfigs[0],
    [selectedPath, yamlConfigs]
  );

  useEffect(() => {
    if (!selected) {
      return;
    }
    setSelectedPath(selected.path);
    api
      .readYaml(selected.path)
      .then((document) => {
        setContent(document.content);
        setValidationError(null);
      })
      .catch((requestError: unknown) => {
        setValidationError(requestError instanceof Error ? requestError.message : "Unable to load YAML.");
      });
  }, [selected]);

  async function validate() {
    const result = await api.validateYaml(content);
    setValidationError(result.valid ? null : result.error);
    setMessage(result.valid ? "YAML is valid." : null);
  }

  async function save() {
    if (!selectedPath) {
      return;
    }
    await api.writeYaml(selectedPath, content);
    setMessage("YAML saved.");
    setValidationError(null);
    await loadYamlConfigs();
  }

  return (
    <Stack spacing={3}>
      {(error || message || validationError) && (
        <Alert severity={validationError || error ? "error" : "success"}>{validationError || error || message}</Alert>
      )}
      <Grid container spacing={2}>
        <Grid item xs={12} md={4} lg={3}>
          <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
            <List dense disablePadding>
              {yamlConfigs.map((config) => (
                <ListItemButton
                  key={config.path}
                  selected={config.path === selectedPath}
                  onClick={() => setSelectedPath(config.path)}
                >
                  <ListItemText primary={config.name} secondary={config.path} />
                </ListItemButton>
              ))}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8} lg={9}>
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Stack spacing={2}>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={1} justifyContent="space-between">
                <Stack spacing={0.5}>
                  <Typography variant="h6">YAML Editor</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedPath}
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={1}>
                  <Button variant="outlined" startIcon={<CheckIcon />} onClick={() => void validate()}>
                    Validate
                  </Button>
                  <Button startIcon={<SaveIcon />} onClick={() => void save()}>
                    Save
                  </Button>
                </Stack>
              </Stack>
              <TextField
                fullWidth
                multiline
                minRows={24}
                value={content}
                onChange={(event) => setContent(event.target.value)}
                InputProps={{
                  sx: {
                    fontFamily: "Roboto Mono, Consolas, monospace",
                    fontSize: 14,
                    alignItems: "flex-start"
                  }
                }}
              />
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}
