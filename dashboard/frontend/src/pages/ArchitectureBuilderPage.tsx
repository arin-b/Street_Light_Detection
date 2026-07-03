import { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import DownloadIcon from "@mui/icons-material/Download";

import { api } from "../api/client";

// ---------------------------------------------------------------------------
// Built-in component palette
// ---------------------------------------------------------------------------

const BUILTIN_COMPONENTS = [
  "Backbone",
  "PAN/FPN",
  "CSE",
  "Geometry Attention",
  "Negative Attention",
  "Detection Head",
  "Tracking",
];

const initialNodes = [
  { id: "1", position: { x: 250, y: 5 }, data: { label: "Input" }, type: "input" },
];
const initialEdges: Edge[] = [];

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export function ArchitectureBuilderPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // User-defined components from the backend
  const [userComponents, setUserComponents] = useState<
    { name: string; filename: string }[]
  >([]);

  // "New Component" dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newCompName, setNewCompName] = useState("");
  const [newCompCode, setNewCompCode] = useState(
    `import torch\nimport torch.nn as nn\n\n\nclass MyCustomLayer(nn.Module):\n    def __init__(self):\n        super().__init__()\n        # TODO: define layers\n\n    def forward(self, x: torch.Tensor) -> torch.Tensor:\n        # TODO: implement forward\n        return x\n`,
  );
  const [dialogError, setDialogError] = useState<string | null>(null);

  // Export result dialog
  const [codePreview, setCodePreview] = useState<string | null>(null);

  // Feedback messages
  const [feedback, setFeedback] = useState<{
    severity: "success" | "error";
    msg: string;
  } | null>(null);

  // Load user components on mount
  useEffect(() => {
    api
      .listComponents()
      .then(setUserComponents)
      .catch(() => {});
  }, []);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const addNode = (label: string) => {
    const newNode = {
      id: `${Date.now()}`,
      position: {
        x: Math.random() * 300 + 50,
        y: Math.random() * 300 + 50,
      },
      data: { label },
      type: "default",
    };
    setNodes((nds) => nds.concat(newNode));
  };

  // ---- Save new component ----
  const handleSaveComponent = async () => {
    const name = newCompName.trim();
    if (!name) {
      setDialogError("Name is required");
      return;
    }
    try {
      setDialogError(null);
      const saved = await api.saveComponent(name, newCompCode);
      setUserComponents((prev) => [...prev, saved]);
      setDialogOpen(false);
      setNewCompName("");
      setFeedback({ severity: "success", msg: `Component "${saved.name}" saved!` });
    } catch (e) {
      setDialogError(e instanceof Error ? e.message : "Save failed");
    }
  };

  // ---- Delete user component ----
  const handleDeleteComponent = async (name: string) => {
    try {
      await api.deleteComponent(name);
      setUserComponents((prev) => prev.filter((c) => c.name !== name));
      setFeedback({ severity: "success", msg: `Component "${name}" deleted` });
    } catch (e) {
      setFeedback({
        severity: "error",
        msg: e instanceof Error ? e.message : "Delete failed",
      });
    }
  };

  // ---- Export model ----
  const handleExportModel = async () => {
    try {
      setFeedback(null);
      const code = await api.exportModel(
        nodes.map((n) => ({
          id: n.id,
          type: n.type,
          data: n.data,
          position: n.position,
        })),
        edges.map((e) => ({ source: e.source, target: e.target })),
      );
      setCodePreview(code);
    } catch (e) {
      setFeedback({
        severity: "error",
        msg: e instanceof Error ? e.message : "Export failed",
      });
    }
  };

  // ---- Download code as .py file ----
  const handleDownloadCode = () => {
    if (!codePreview) return;
    const blob = new Blob([codePreview], { type: "text/x-python" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "custom_yolo_model.py";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Stack spacing={2} sx={{ height: "calc(100vh - 120px)" }}>
      {/* Feedback */}
      {feedback && (
        <Alert
          severity={feedback.severity}
          onClose={() => setFeedback(null)}
        >
          {feedback.msg}
        </Alert>
      )}

      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h5" fontWeight={800}>
          🏗️ Architecture Builder
        </Typography>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExportModel}
        >
          Export Model
        </Button>
      </Stack>

      {/* Main layout */}
      <Box sx={{ display: "flex", flexGrow: 1, gap: 2 }}>
        {/* ---- Toolbox Sidebar ---- */}
        <Paper
          variant="outlined"
          sx={{
            width: 260,
            p: 2,
            display: "flex",
            flexDirection: "column",
            gap: 0.5,
            overflowY: "auto",
          }}
        >
          <Typography variant="subtitle2" fontWeight={700}>
            Built-in Components
          </Typography>
          <Divider sx={{ mb: 0.5 }} />
          {BUILTIN_COMPONENTS.map((c) => (
            <Button
              key={c}
              variant="outlined"
              size="small"
              sx={{ justifyContent: "flex-start", textTransform: "none" }}
              onClick={() => addNode(c)}
            >
              + {c}
            </Button>
          ))}

          <Divider sx={{ my: 1 }} />
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
          >
            <Typography variant="subtitle2" fontWeight={700}>
              User Components
            </Typography>
            <Tooltip title="New Component">
              <IconButton size="small" onClick={() => setDialogOpen(true)}>
                <AddCircleOutlineIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>

          {userComponents.length === 0 ? (
            <Typography variant="caption" color="text.secondary" sx={{ px: 1 }}>
              No custom components yet
            </Typography>
          ) : (
            userComponents.map((uc) => (
              <Stack
                key={uc.name}
                direction="row"
                alignItems="center"
                spacing={0.5}
              >
                <Button
                  variant="outlined"
                  size="small"
                  color="secondary"
                  sx={{
                    flexGrow: 1,
                    justifyContent: "flex-start",
                    textTransform: "none",
                  }}
                  onClick={() => addNode(uc.name)}
                >
                  + {uc.name}
                </Button>
                <IconButton
                  size="small"
                  onClick={() => handleDeleteComponent(uc.name)}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Stack>
            ))
          )}
        </Paper>

        {/* ---- Canvas ---- */}
        <Paper variant="outlined" sx={{ flexGrow: 1, position: "relative" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            deleteKeyCode={["Backspace", "Delete"]}
            onSelectionChange={(params) => {
              if (params.nodes.length > 0) {
                setSelectedNodeId(params.nodes[0].id);
              } else {
                setSelectedNodeId(null);
              }
            }}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background gap={12} size={1} />
          </ReactFlow>
        </Paper>

        {/* ---- Properties Sidebar ---- */}
        {selectedNodeId && (
          <Paper variant="outlined" sx={{ width: 250, p: 2 }}>
            <Typography variant="subtitle2" fontWeight={700}>
              Properties
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              Node: {nodes.find((n) => n.id === selectedNodeId)?.data?.label ?? selectedNodeId}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              ID: {selectedNodeId}
            </Typography>
          </Paper>
        )}
      </Box>

      {/* ---- New Component Dialog ---- */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>New Custom Component</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {dialogError && <Alert severity="error">{dialogError}</Alert>}
            <TextField
              label="Component Name (e.g. CustomConv)"
              value={newCompName}
              onChange={(e) => setNewCompName(e.target.value)}
              size="small"
              fullWidth
              helperText="Alphanumeric + underscores, must start with a letter"
            />
            <TextField
              label="Python Code"
              value={newCompCode}
              onChange={(e) => setNewCompCode(e.target.value)}
              multiline
              minRows={12}
              maxRows={24}
              fullWidth
              InputProps={{
                sx: { fontFamily: "monospace", fontSize: 13 },
              }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveComponent}>
            Save Component
          </Button>
        </DialogActions>
      </Dialog>

      {/* ---- Code Preview Dialog ---- */}
      <Dialog
        open={codePreview !== null}
        onClose={() => setCodePreview(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Generated Model Code</DialogTitle>
        <DialogContent>
          <Box
            component="pre"
            sx={{
              bgcolor: "#1e1e1e",
              color: "#d4d4d4",
              p: 2,
              borderRadius: 1,
              overflow: "auto",
              maxHeight: 500,
              fontSize: 13,
              fontFamily: "monospace",
              whiteSpace: "pre-wrap",
            }}
          >
            {codePreview}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCodePreview(null)}>Close</Button>
          <Button variant="contained" onClick={handleDownloadCode}>
            Download .py
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
