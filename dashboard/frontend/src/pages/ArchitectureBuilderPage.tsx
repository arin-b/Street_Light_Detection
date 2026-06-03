import { useCallback, useState } from "react";
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
  Box,
  Button,
  Paper,
  Stack,
  Typography,
  Divider,
} from "@mui/material";

const initialNodes = [
  { id: "1", position: { x: 250, y: 5 }, data: { label: "Input" }, type: "input" },
];
const initialEdges: Edge[] = [];

export function ArchitectureBuilderPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const addNode = (label: string) => {
    const newNode = {
      id: `${Date.now()}`,
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      data: { label },
      type: "default",
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const handleExport = () => {
    const architecture = {
      nodes: nodes.map(n => ({ id: n.id, type: n.data.label })),
      edges: edges.map(e => ({ source: e.source, target: e.target }))
    };
    alert(JSON.stringify(architecture, null, 2));
  };

  return (
    <Stack spacing={2} sx={{ height: "calc(100vh - 120px)" }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h5" fontWeight={800}>
          🏗️ Architecture Builder
        </Typography>
        <Button variant="contained" onClick={handleExport}>
          Export Config (JSON)
        </Button>
      </Stack>

      <Box sx={{ display: "flex", flexGrow: 1, gap: 2 }}>
        {/* Toolbox Sidebar */}
        <Paper variant="outlined" sx={{ width: 250, p: 2, display: "flex", flexDirection: "column", gap: 1 }}>
          <Typography variant="subtitle2" fontWeight={700}>Components</Typography>
          <Divider sx={{ mb: 1 }} />
          <Button variant="outlined" size="small" onClick={() => addNode("Backbone")}>+ Backbone</Button>
          <Button variant="outlined" size="small" onClick={() => addNode("PAN/FPN")}>+ PAN/FPN</Button>
          <Button variant="outlined" size="small" onClick={() => addNode("CSE")}>+ CSE Attention</Button>
          <Button variant="outlined" size="small" onClick={() => addNode("Geometry Attention")}>+ Geometry Attention</Button>
          <Button variant="outlined" size="small" onClick={() => addNode("Detection Head")}>+ Detection Head</Button>
        </Paper>

        {/* Canvas Area */}
        <Paper variant="outlined" sx={{ flexGrow: 1, position: "relative" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
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

        {/* Properties Sidebar */}
        {selectedNodeId && (
          <Paper variant="outlined" sx={{ width: 250, p: 2 }}>
            <Typography variant="subtitle2" fontWeight={700}>Properties</Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              Selected Node ID: {selectedNodeId}
            </Typography>
            {/* Note: This is a simplified property editor. In a real application, you would map form inputs to the specific node's data. */}
            <Typography variant="caption" color="warning.main" display="block" sx={{ mt: 2 }}>
              Parameter editing will be implemented in future iterations based on YOLO26 schema.
            </Typography>
          </Paper>
        )}
      </Box>
    </Stack>
  );
}
