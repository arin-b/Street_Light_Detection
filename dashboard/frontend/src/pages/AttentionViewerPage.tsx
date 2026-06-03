import {
  Alert,
  Box,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { AttentionMap } from "../types";

export function AttentionViewerPage() {
  const [maps, setMaps] = useState<AttentionMap[]>([]);
  const [selectedMapId, setSelectedMapId] = useState<string>("");
  const [opacity, setOpacity] = useState<number>(0.5);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listAttentionMaps()
      .then((data) => {
        setMaps(data);
        if (data.length > 0) {
          setSelectedMapId(data[0].id);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load attention maps"));
  }, []);

  const selectedMap = maps.find((m) => m.id === selectedMapId);

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
      
      <Typography variant="h5" fontWeight={800}>
        🔍 Attention Map Visualizer
      </Typography>

      <Grid container spacing={3}>
        {/* Controls Panel */}
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 2 }}>
            <Stack spacing={4}>
              <Box>
                <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1.5 }}>
                  Select Map Layer
                </Typography>
                <FormControl fullWidth size="small">
                  <InputLabel>Attention Layer</InputLabel>
                  <Select
                    label="Attention Layer"
                    value={selectedMapId}
                    onChange={(e) => setSelectedMapId(e.target.value as string)}
                  >
                    {maps.map((m) => (
                      <MenuItem key={m.id} value={m.id}>
                        {m.layer}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              <Box>
                <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1.5 }}>
                  Overlay Transparency ({Math.round(opacity * 100)}%)
                </Typography>
                <Slider
                  value={opacity}
                  onChange={(_, val) => setOpacity(val as number)}
                  min={0}
                  max={1}
                  step={0.05}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(val) => `${Math.round(val * 100)}%`}
                />
              </Box>
              
              <Alert severity="info" sx={{ mt: 2 }}>
                This is a placeholder for the live attention map extractor. Currently showing pre-computed mock maps.
              </Alert>
            </Stack>
          </Paper>
        </Grid>

        {/* Viewer Panel */}
        <Grid item xs={12} md={8}>
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              borderRadius: 2,
              minHeight: 400,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "background.default",
              position: "relative",
            }}
          >
            {selectedMap ? (
              <Box sx={{ position: "relative", width: "100%", maxWidth: 640, aspectRatio: "16/9", bgcolor: "#000", borderRadius: 1, overflow: "hidden" }}>
                {/* Base Image Mock */}
                <Box sx={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(45deg, #1e1e1e 25%, #2a2a2a 25%, #2a2a2a 50%, #1e1e1e 50%, #1e1e1e 75%, #2a2a2a 75%, #2a2a2a 100%)", backgroundSize: "20px 20px" }} />
                
                {/* Attention Overlay */}
                <Box
                  sx={{
                    position: "absolute",
                    inset: 0,
                    opacity: opacity,
                    background: "radial-gradient(circle, rgba(255,167,38,0.8) 0%, rgba(255,167,38,0) 50%)",
                    mixBlendMode: "screen",
                  }}
                />
                <Typography variant="caption" sx={{ position: "absolute", bottom: 8, left: 8, bgcolor: "rgba(0,0,0,0.6)", px: 1, borderRadius: 1 }}>
                  Preview: {selectedMap.layer}
                </Typography>
              </Box>
            ) : (
              <Typography color="text.secondary">
                No attention maps available.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}
