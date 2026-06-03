import {
  Alert,
  Box,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { TrackingVideoSummary } from "../types";

export function TrackingViewerPage() {
  const [videos, setVideos] = useState<TrackingVideoSummary[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<TrackingVideoSummary | null>(null);
  const [trajectories, setTrajectories] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listTrackingVideos()
      .then((data) => {
        setVideos(data);
        if (data.length > 0) {
          setSelectedVideo(data[0]);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load tracking videos"));
  }, []);

  useEffect(() => {
    if (selectedVideo?.has_trajectories) {
      api.getTrackingTrajectories(selectedVideo.filename)
        .then(setTrajectories)
        .catch(() => setTrajectories(null));
    } else {
      setTrajectories(null);
    }
  }, [selectedVideo]);

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}

      <Typography variant="h5" fontWeight={800}>
        🎥 Tracking Viewer
      </Typography>

      <Grid container spacing={3}>
        {/* Video List Sidebar */}
        <Grid item xs={12} md={3}>
          <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
            <Box sx={{ p: 2, bgcolor: "background.default", borderBottom: "1px solid", borderColor: "divider" }}>
              <Typography variant="subtitle2" fontWeight={700}>
                Available Videos ({videos.length})
              </Typography>
            </Box>
            <List disablePadding sx={{ maxHeight: 600, overflow: "auto" }}>
              {videos.length === 0 ? (
                <ListItem>
                  <ListItemText secondary="No tracking videos found." />
                </ListItem>
              ) : (
                videos.map((video) => (
                  <Box key={video.filename}>
                    <ListItem
                      button
                      selected={selectedVideo?.filename === video.filename}
                      onClick={() => setSelectedVideo(video)}
                    >
                      <ListItemText
                        primary={video.filename}
                        secondary={`${(video.size_bytes / (1024 * 1024)).toFixed(2)} MB • ${video.has_trajectories ? "Has Metadata" : "No Metadata"}`}
                        primaryTypographyProps={{ variant: "body2", fontWeight: 600, noWrap: true }}
                        secondaryTypographyProps={{ variant: "caption" }}
                      />
                    </ListItem>
                    <Divider />
                  </Box>
                ))
              )}
            </List>
          </Paper>
        </Grid>

        {/* Video Player Area */}
        <Grid item xs={12} md={9}>
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, minHeight: 400 }}>
            {selectedVideo ? (
              <Stack spacing={2}>
                <Typography variant="h6" fontWeight={600}>
                  {selectedVideo.filename}
                </Typography>

                <Box sx={{ width: "100%", bgcolor: "#000", borderRadius: 1, overflow: "hidden" }}>
                  <video
                    key={selectedVideo.filename} // Force re-render when video changes
                    controls
                    autoPlay
                    style={{ width: "100%", maxHeight: 600, display: "block" }}
                    src={api.getTrackingVideoUrl(selectedVideo.filename)}
                  >
                    Your browser does not support the video tag.
                  </video>
                </Box>

                {trajectories && (
                  <Box sx={{ p: 2, bgcolor: "background.default", borderRadius: 1 }}>
                    <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
                      Trajectory Metadata
                    </Typography>
                    <Box component="pre" sx={{ m: 0, fontSize: 11, color: "text.secondary", maxHeight: 150, overflow: "auto" }}>
                      {JSON.stringify(trajectories, null, 2)}
                    </Box>
                  </Box>
                )}
              </Stack>
            ) : (
              <Box sx={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center" }}>
                <Typography color="text.secondary">Select a video from the list to view</Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}
