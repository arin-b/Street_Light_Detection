import { CssBaseline, ThemeProvider } from "@mui/material";
import { useState } from "react";

import { Shell, type PageKey } from "./components/Shell";
import { ArchitectureBuilderPage } from "./pages/ArchitectureBuilderPage";
import { AttentionViewerPage } from "./pages/AttentionViewerPage";
import { ExperimentsPage } from "./pages/ExperimentsPage";
import { HomePage } from "./pages/HomePage";
import { LiveLogsPage } from "./pages/LiveLogsPage";
import { MonitoringPage } from "./pages/MonitoringPage";
import { SweepsPage } from "./pages/SweepsPage";
import { TrackingViewerPage } from "./pages/TrackingViewerPage";
import { TrainingPage } from "./pages/TrainingPage";
import { VisualizationPage } from "./pages/VisualizationPage";
import { YamlEditorPage } from "./pages/YamlEditorPage";
import { theme } from "./theme";

function pageView(page: PageKey) {
  switch (page) {
    case "experiments":
      return <ExperimentsPage />;
    case "yaml":
      return <YamlEditorPage />;
    case "architecture":
      return <ArchitectureBuilderPage />;
    case "sweeps":
      return <SweepsPage />;
    case "training":
      return <TrainingPage />;
    case "logs":
      return <LiveLogsPage />;
    case "monitoring":
      return <MonitoringPage />;
    case "visualizations":
      return <VisualizationPage />;
    case "attention":
      return <AttentionViewerPage />;
    case "tracking":
      return <TrackingViewerPage />;
    default:
      return <HomePage />;
  }
}

export default function App() {
  const [page, setPage] = useState<PageKey>("home");

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Shell page={page} onPageChange={setPage}>
        {pageView(page)}
      </Shell>
    </ThemeProvider>
  );
}
