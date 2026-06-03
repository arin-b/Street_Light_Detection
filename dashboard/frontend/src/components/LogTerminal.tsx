import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DownloadIcon from "@mui/icons-material/Download";
import FilterListIcon from "@mui/icons-material/FilterList";
import SearchIcon from "@mui/icons-material/Search";
import VerticalAlignBottomIcon from "@mui/icons-material/VerticalAlignBottom";
import {
  Box,
  Chip,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";

import type { LogStreamMessage } from "../types";

interface LogTerminalProps {
  lines: LogStreamMessage[];
  title?: string;
}

const levelColors: Record<string, string> = {
  info: "#e0e0e0",
  warning: "#ffb74d",
  error: "#ef5350",
};

export function LogTerminal({ lines, title = "Live Terminal" }: LogTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState<string | null>(null);

  const scrollToBottom = useCallback(() => {
    if (containerRef.current && autoScroll) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [autoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [lines.length, scrollToBottom]);

  const filteredLines = lines.filter((line) => {
    if (line.type === "heartbeat") return false;
    if (levelFilter && line.level !== levelFilter) return false;
    if (search && !line.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  function handleCopy() {
    const text = filteredLines.map((l) => l.message).join("\n");
    void navigator.clipboard.writeText(text);
  }

  function handleDownload() {
    const text = filteredLines.map((l) => `[${l.timestamp}] [${l.level}] ${l.message}`).join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "training-logs.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  const levelChips: { level: string; label: string }[] = [
    { level: "info", label: "Info" },
    { level: "warning", label: "Warning" },
    { level: "error", label: "Error" },
  ];

  return (
    <Box>
      {/* Toolbar */}
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{ mb: 1, flexWrap: "wrap", gap: 0.5 }}
      >
        <Typography variant="subtitle2" fontWeight={700} sx={{ mr: 1 }}>
          {title}
        </Typography>

        <TextField
          size="small"
          placeholder="Search logs…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{
            width: 200,
            "& .MuiInputBase-root": {
              bgcolor: "rgba(255,255,255,0.06)",
              color: "#e0e0e0",
              fontSize: 13,
            },
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: "text.secondary", fontSize: 18 }} />
              </InputAdornment>
            ),
          }}
        />

        <FilterListIcon sx={{ color: "text.secondary", fontSize: 18, ml: 1 }} />
        {levelChips.map((lc) => (
          <Chip
            key={lc.level}
            label={lc.label}
            size="small"
            variant={levelFilter === lc.level ? "filled" : "outlined"}
            color={
              lc.level === "error" ? "error" : lc.level === "warning" ? "warning" : "default"
            }
            onClick={() => setLevelFilter(levelFilter === lc.level ? null : lc.level)}
            sx={{ fontSize: 11 }}
          />
        ))}

        <Box sx={{ flex: 1 }} />

        <Tooltip title={autoScroll ? "Auto-scroll ON" : "Auto-scroll OFF"}>
          <IconButton
            size="small"
            onClick={() => setAutoScroll(!autoScroll)}
            sx={{ color: autoScroll ? "primary.main" : "text.secondary" }}
          >
            <VerticalAlignBottomIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Copy logs">
          <IconButton size="small" onClick={handleCopy} sx={{ color: "text.secondary" }}>
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Download logs">
          <IconButton size="small" onClick={handleDownload} sx={{ color: "text.secondary" }}>
            <DownloadIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>

      {/* Terminal area */}
      <Box
        ref={containerRef}
        sx={{
          bgcolor: "#0d1117",
          borderRadius: 2,
          p: 2,
          height: 500,
          overflow: "auto",
          fontFamily: "\"JetBrains Mono\", \"Roboto Mono\", Consolas, monospace",
          fontSize: 12.5,
          lineHeight: 1.7,
          border: "1px solid",
          borderColor: "rgba(255,255,255,0.08)",
          "&::-webkit-scrollbar": { width: 6 },
          "&::-webkit-scrollbar-thumb": {
            bgcolor: "rgba(255,255,255,0.15)",
            borderRadius: 3,
          },
        }}
      >
        {filteredLines.length === 0 ? (
          <Typography variant="body2" sx={{ color: "#666", fontStyle: "italic" }}>
            {lines.length === 0 ? "Waiting for log output…" : "No lines match the current filter."}
          </Typography>
        ) : (
          filteredLines.map((line, idx) => (
            <Box
              key={idx}
              component="pre"
              sx={{
                m: 0,
                p: 0,
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                color: levelColors[line.level] ?? "#e0e0e0",
                ...(line.level === "error"
                  ? { bgcolor: "rgba(239,83,80,0.08)", px: 0.5, borderRadius: 0.5 }
                  : {}),
                ...(search &&
                line.message.toLowerCase().includes(search.toLowerCase())
                  ? { bgcolor: "rgba(255,235,59,0.1)" }
                  : {}),
              }}
            >
              <Box
                component="span"
                sx={{ color: "#555", mr: 1, fontSize: 11, userSelect: "none" }}
              >
                {String(idx + 1).padStart(4, " ")}
              </Box>
              {line.message}
            </Box>
          ))
        )}
      </Box>

      {/* Status bar */}
      <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5, px: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {filteredLines.length} / {lines.length} lines
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {autoScroll ? "Auto-scroll enabled" : "Scroll paused"}
        </Typography>
      </Stack>
    </Box>
  );
}
