"""Training process management service.

Spawns training subprocesses, captures stdout/stderr into a ring buffer and the
database, and parses Ultralytics metric lines to populate the Metric table.
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
import threading
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from rbccps_dashboard.config import DashboardSettings, get_settings
from rbccps_dashboard.database import SessionLocal
from rbccps_dashboard.models import Experiment, LogEntry, Metric, Run

logger = logging.getLogger(__name__)

# Regex for Ultralytics training progress lines, e.g.:
#   "      3/100      2.35G      1.234      0.567      0.890        16       640:  ..."
_METRIC_LINE_RE = re.compile(
    r"^\s*(?P<epoch>\d+)/(?P<total>\d+)\s+"
    r"[\d.]+G?\s+"
    r"(?P<box_loss>[\d.]+)\s+"
    r"(?P<cls_loss>[\d.]+)\s+"
    r"(?P<dfl_loss>[\d.]+)",
)

# Regex for validation result lines, e.g.:
#   "                 all        123         456      0.789      0.654      0.712      0.456"
_VAL_LINE_RE = re.compile(
    r"^\s*all\s+\d+\s+\d+\s+"
    r"(?P<precision>[\d.]+)\s+"
    r"(?P<recall>[\d.]+)\s+"
    r"(?P<map50>[\d.]+)\s+"
    r"(?P<map50_95>[\d.]+)",
)


class LogBuffer:
    """Thread-safe ring buffer for log lines."""

    def __init__(self, maxlen: int = 2000) -> None:
        self._buf: deque[dict[str, str]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._subscribers: list[Any] = []

    def append(self, entry: dict[str, str]) -> None:
        with self._lock:
            self._buf.append(entry)
        for callback in self._subscribers:
            try:
                callback(entry)
            except Exception:
                pass

    def recent(self, n: int = 200) -> list[dict[str, str]]:
        with self._lock:
            items = list(self._buf)
        return items[-n:]

    def all(self) -> list[dict[str, str]]:
        with self._lock:
            return list(self._buf)

    def subscribe(self, callback: Any) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Any) -> None:
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass


def _classify_level(line: str) -> str:
    """Classify a log line as info, warning, or error."""
    lower = line.lower()
    if "error" in lower or "exception" in lower or "traceback" in lower:
        return "error"
    if "warn" in lower:
        return "warning"
    return "info"


class TrainingService:
    """Manages training subprocess lifecycle."""

    def __init__(self, settings: DashboardSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self._processes: dict[int, subprocess.Popen[str]] = {}
        self._buffers: dict[int, LogBuffer] = {}
        self._threads: dict[int, list[threading.Thread]] = {}
        self._current_epoch: dict[int, int] = {}
        self._total_epochs: dict[int, int] = {}
        self._lock = threading.Lock()

    def launch(self, experiment_id: int, session: Session) -> Run:
        """Create a Run and spawn the training subprocess."""
        experiment = session.get(Experiment, experiment_id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {experiment_id}")

        config = experiment.config_snapshot or {}
        command = self._build_command(config, experiment)

        run = Run(
            experiment_id=experiment.id,
            status="running",
            command=command,
            started_at=datetime.now(UTC),
            output_dir=str(
                self.settings.runs_output_root / f"run_{experiment.id}"
            ),
            metadata_json={"experiment_name": experiment.name},
        )
        session.add(run)
        session.commit()

        experiment.status = "running"
        session.commit()

        buf = LogBuffer(maxlen=self.settings.log_buffer_size)
        self._buffers[run.id] = buf

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.settings.project_root),
                shell=True,
                bufsize=1,
            )
        except Exception as exc:
            run.status = "failed"
            run.finished_at = datetime.now(UTC)
            session.commit()
            raise RuntimeError(f"Failed to start training: {exc}") from exc

        with self._lock:
            self._processes[run.id] = process

        stdout_thread = threading.Thread(
            target=self._read_stream,
            args=(run.id, process.stdout, "stdout"),
            daemon=True,
            name=f"train-stdout-{run.id}",
        )
        stderr_thread = threading.Thread(
            target=self._read_stream,
            args=(run.id, process.stderr, "stderr"),
            daemon=True,
            name=f"train-stderr-{run.id}",
        )
        waiter_thread = threading.Thread(
            target=self._wait_for_completion,
            args=(run.id, process, experiment_id),
            daemon=True,
            name=f"train-wait-{run.id}",
        )

        self._threads[run.id] = [stdout_thread, stderr_thread, waiter_thread]
        stdout_thread.start()
        stderr_thread.start()
        waiter_thread.start()

        logger.info("Started training run %d (PID %d) for experiment %d", run.id, process.pid, experiment_id)
        return run

    def stop(self, run_id: int, session: Session) -> Run:
        """Stop a running training process."""
        run = session.get(Run, run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")

        with self._lock:
            process = self._processes.get(run_id)

        if process and process.poll() is None:
            import signal

            try:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

        run.status = "cancelled"
        run.finished_at = datetime.now(UTC)
        session.commit()

        experiment = session.get(Experiment, run.experiment_id)
        if experiment:
            experiment.status = "cancelled"
            session.commit()

        self._cleanup(run_id)
        return run

    def get_run(self, run_id: int, session: Session) -> Run:
        """Get a run by ID."""
        run = session.get(Run, run_id)
        if run is None:
            raise KeyError(f"Run not found: {run_id}")
        return run

    def list_runs(
        self, session: Session, *, status: str | None = None, experiment_id: int | None = None
    ) -> list[Run]:
        """List runs, optionally filtered by status or experiment."""
        from sqlalchemy import select

        query = select(Run).order_by(Run.created_at.desc())
        if status:
            query = query.where(Run.status == status)
        if experiment_id is not None:
            query = query.where(Run.experiment_id == experiment_id)
        return list(session.scalars(query))

    def delete_run(self, run_id: int, session: Session) -> None:
        """Delete a run record."""
        run = self.get_run(run_id, session)
        if run.status == "running":
            self.stop(run_id, session)
        session.delete(run)
        session.commit()

    def get_logs(self, run_id: int, session: Session, *, limit: int = 500, offset: int = 0) -> list[LogEntry]:
        """Get persisted log entries for a run."""
        from sqlalchemy import select

        query = (
            select(LogEntry)
            .where(LogEntry.run_id == run_id)
            .order_by(LogEntry.id)
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(query))

    def get_buffer(self, run_id: int) -> LogBuffer | None:
        """Get the in-memory log buffer for a run."""
        return self._buffers.get(run_id)

    def get_progress(self, run_id: int) -> dict[str, int]:
        """Get current epoch progress."""
        return {
            "current_epoch": self._current_epoch.get(run_id, 0),
            "total_epochs": self._total_epochs.get(run_id, 0),
        }

    def is_running(self, run_id: int) -> bool:
        """Check if a run's process is still active."""
        with self._lock:
            process = self._processes.get(run_id)
        return process is not None and process.poll() is None

    def _build_command(self, config: dict[str, Any], experiment: Experiment) -> str:
        """Build the training CLI command from experiment config."""
        training = config.get("training", {})
        model_cfg = config.get("model", {})
        dataset_cfg = config.get("dataset", {})

        data = dataset_cfg.get("config", "src/rbccps_od/config/original.yaml")
        model_weights = model_cfg.get("pretrained_weights") or "yolo26m.pt"
        variant = model_cfg.get("variant", "YOLO26m")

        epochs = training.get("epochs", 100)
        batch_size = training.get("batch_size", 16)
        image_size = training.get("image_size", 640)
        device = training.get("device", "auto")
        patience = training.get("patience", 50)
        workers = training.get("workers", 8)
        optimizer = training.get("optimizer", "auto")
        lr0 = training.get("learning_rate", 0.01)

        run_name = re.sub(r"[^a-z0-9]+", "_", experiment.name.lower()).strip("_")
        project_dir = self.settings.runs_output_root

        cmd_parts = [
            sys.executable, "-m", "rbccps_od.training.train",
            f"--model={model_weights}",
            f"--data={data}",
            f"--imgsz={image_size}",
            f"--epochs={epochs}",
            f"--batch={batch_size}",
            f"--device={device}",
            f"--project={project_dir}",
            f"--name={run_name}",
            f"--patience={patience}",
            f"--workers={workers}",
        ]
        self._total_epochs[0] = epochs  # Will be updated per run
        return " ".join(str(p) for p in cmd_parts)

    def _read_stream(self, run_id: int, stream: Any, stream_name: str) -> None:
        """Read lines from a subprocess stream and buffer them."""
        buf = self._buffers.get(run_id)
        if not buf or not stream:
            return

        try:
            for line in stream:
                line = line.rstrip("\n\r")
                if not line:
                    continue

                level = _classify_level(line)
                timestamp = datetime.now(UTC).isoformat()

                entry = {
                    "stream": stream_name,
                    "level": level,
                    "message": line,
                    "timestamp": timestamp,
                }
                buf.append(entry)

                # Parse metrics from stdout
                if stream_name == "stdout":
                    self._parse_metrics(run_id, line)

                # Persist to database (fire-and-forget in a separate session)
                self._persist_log(run_id, level, line, stream_name)

        except Exception:
            logger.exception("Error reading %s for run %d", stream_name, run_id)

    def _parse_metrics(self, run_id: int, line: str) -> None:
        """Extract training metrics from Ultralytics output lines."""
        match = _METRIC_LINE_RE.search(line)
        if match:
            epoch = int(match.group("epoch"))
            total = int(match.group("total"))
            self._current_epoch[run_id] = epoch
            self._total_epochs[run_id] = total

            metrics = {
                "box_loss": float(match.group("box_loss")),
                "cls_loss": float(match.group("cls_loss")),
                "dfl_loss": float(match.group("dfl_loss")),
            }
            self._persist_metrics(run_id, epoch, metrics)
            return

        val_match = _VAL_LINE_RE.search(line)
        if val_match:
            epoch = self._current_epoch.get(run_id, 0)
            metrics = {
                "precision": float(val_match.group("precision")),
                "recall": float(val_match.group("recall")),
                "mAP50": float(val_match.group("map50")),
                "mAP50-95": float(val_match.group("map50_95")),
            }
            self._persist_metrics(run_id, epoch, metrics)

    def _persist_log(self, run_id: int, level: str, message: str, stream: str) -> None:
        """Persist a log entry to the database."""
        try:
            session = SessionLocal()
            try:
                entry = LogEntry(
                    run_id=run_id,
                    level=level,
                    message=message,
                    stream=stream,
                )
                session.add(entry)
                session.commit()
            finally:
                session.close()
        except Exception:
            logger.debug("Failed to persist log for run %d", run_id, exc_info=True)

    def _persist_metrics(self, run_id: int, epoch: int, metrics: dict[str, float]) -> None:
        """Persist parsed metrics to the database."""
        try:
            session = SessionLocal()
            try:
                for name, value in metrics.items():
                    metric = Metric(
                        run_id=run_id,
                        name=name,
                        step=epoch,
                        value=value,
                    )
                    session.add(metric)
                session.commit()
            finally:
                session.close()
        except Exception:
            logger.debug("Failed to persist metrics for run %d", run_id, exc_info=True)

    def _wait_for_completion(self, run_id: int, process: subprocess.Popen[str], experiment_id: int) -> None:
        """Wait for the subprocess to finish and update run status."""
        try:
            return_code = process.wait()
            logger.info("Run %d finished with return code %d", run_id, return_code)

            session = SessionLocal()
            try:
                run = session.get(Run, run_id)
                if run and run.status == "running":
                    run.status = "completed" if return_code == 0 else "failed"
                    run.finished_at = datetime.now(UTC)
                    run.metadata_json = {
                        **run.metadata_json,
                        "return_code": return_code,
                        "final_epoch": self._current_epoch.get(run_id, 0),
                    }
                    session.commit()

                experiment = session.get(Experiment, experiment_id)
                if experiment and experiment.status == "running":
                    experiment.status = "completed" if return_code == 0 else "failed"
                    session.commit()
            finally:
                session.close()

        except Exception:
            logger.exception("Error in completion handler for run %d", run_id)
        finally:
            self._cleanup(run_id)

    def _cleanup(self, run_id: int) -> None:
        """Remove process and threads from registry."""
        with self._lock:
            self._processes.pop(run_id, None)
        self._threads.pop(run_id, None)
        self._current_epoch.pop(run_id, None)
        self._total_epochs.pop(run_id, None)

    def shutdown(self) -> None:
        """Stop all running processes (called on app shutdown)."""
        with self._lock:
            run_ids = list(self._processes.keys())
        for run_id in run_ids:
            process = self._processes.get(run_id)
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    process.kill()


# Module-level singleton
_training_service: TrainingService | None = None


def get_training_service() -> TrainingService:
    """Get or create the singleton TrainingService."""
    global _training_service
    if _training_service is None:
        _training_service = TrainingService()
    return _training_service
