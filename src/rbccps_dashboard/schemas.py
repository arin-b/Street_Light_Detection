from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ExperimentStatus = Literal["draft", "queued", "running", "completed", "failed", "cancelled", "archived"]


class ExperimentBase(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str = ""
    status: ExperimentStatus = "draft"
    config_path: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    dataset: str | None = None
    model_variant: str = "YOLO26m"
    training: dict[str, Any] = Field(default_factory=dict)


class ExperimentCreate(ExperimentBase):
    pass


class ExperimentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
    status: ExperimentStatus | None = None
    config_path: str | None = None
    config: dict[str, Any] | None = None
    tags: list[str] | None = None
    dataset: str | None = None
    model_variant: str | None = None
    training: dict[str, Any] | None = None


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    status: str
    config_path: str | None
    config_snapshot: dict[str, Any]
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class ExperimentDuplicate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None


class YAMLConfigSummary(BaseModel):
    path: str
    name: str
    size_bytes: int
    modified_at: datetime


class YAMLConfigRead(BaseModel):
    path: str
    content: str
    parsed: Any
    modified_at: datetime


class YAMLConfigUpdate(BaseModel):
    path: str
    content: str


class YAMLValidationRequest(BaseModel):
    content: str


class YAMLValidationResponse(BaseModel):
    valid: bool
    parsed: Any = None
    error: str | None = None


class DashboardSummary(BaseModel):
    experiments_total: int
    experiments_active: int
    experiments_completed: int
    experiments_failed: int
    yaml_configs: int
    cpu_percent: float | None = None
    ram_percent: float | None = None


# ---------------------------------------------------------------------------
# Run schemas
# ---------------------------------------------------------------------------

RunStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


class RunCreate(BaseModel):
    experiment_id: int


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    status: str
    command: str
    started_at: datetime | None
    finished_at: datetime | None
    output_dir: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class LogEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    level: str
    message: str
    stream: str
    created_at: datetime


class LogStreamMessage(BaseModel):
    """Single log line sent over WebSocket."""
    stream: str = "stdout"
    level: str = "info"
    message: str
    timestamp: str


# ---------------------------------------------------------------------------
# System monitoring schemas
# ---------------------------------------------------------------------------

class GPUMetrics(BaseModel):
    index: int = 0
    name: str = ""
    percent: float = 0.0
    vram_used_mb: float = 0.0
    vram_free_mb: float = 0.0
    vram_total_mb: float = 0.0
    temperature: float = 0.0
    power_watts: float = 0.0
    clock_mhz: float = 0.0
    fan_percent: float = 0.0


class SystemMetrics(BaseModel):
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    net_sent_mbps: float = 0.0
    net_recv_mbps: float = 0.0
    gpu: GPUMetrics | None = None
    timestamp: str = ""


class GPUInfo(BaseModel):
    available: bool = False
    name: str = ""
    driver_version: str = ""
    vram_total_mb: float = 0.0

