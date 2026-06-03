"""System resource monitoring service.

Collects CPU, RAM, disk, network, and GPU metrics using psutil and pynvml.
Provides both one-shot snapshots and a background polling loop that
broadcasts metrics to WebSocket subscribers.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime
from typing import Any

import psutil

from rbccps_dashboard.schemas import GPUInfo, GPUMetrics, SystemMetrics

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GPU helpers (graceful degradation when pynvml is unavailable)
# ---------------------------------------------------------------------------

_nvml_initialized = False


def _init_nvml() -> bool:
    """Try to initialize NVML. Returns True on success."""
    global _nvml_initialized
    if _nvml_initialized:
        return True
    try:
        import pynvml

        pynvml.nvmlInit()
        _nvml_initialized = True
        return True
    except Exception:
        return False


def _shutdown_nvml() -> None:
    global _nvml_initialized
    if _nvml_initialized:
        try:
            import pynvml

            pynvml.nvmlShutdown()
        except Exception:
            pass
        _nvml_initialized = False


def _gpu_snapshot() -> GPUMetrics | None:
    """Capture a GPU metrics snapshot for the first device."""
    if not _init_nvml():
        return None
    try:
        import pynvml

        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode()

        try:
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except Exception:
            temp = 0.0

        try:
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW → W
        except Exception:
            power = 0.0

        try:
            clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
        except Exception:
            clock = 0.0

        try:
            fan = pynvml.nvmlDeviceGetFanSpeed(handle)
        except Exception:
            fan = 0.0

        return GPUMetrics(
            index=0,
            name=name,
            percent=float(util.gpu),
            vram_used_mb=mem.used / (1024 * 1024),
            vram_free_mb=mem.free / (1024 * 1024),
            vram_total_mb=mem.total / (1024 * 1024),
            temperature=float(temp),
            power_watts=float(power),
            clock_mhz=float(clock),
            fan_percent=float(fan),
        )
    except Exception:
        logger.debug("GPU snapshot failed", exc_info=True)
        return None


def _gpu_info() -> GPUInfo:
    """Get static GPU device information."""
    if not _init_nvml():
        return GPUInfo(available=False)
    try:
        import pynvml

        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode()
        driver = pynvml.nvmlSystemGetDriverVersion()
        if isinstance(driver, bytes):
            driver = driver.decode()
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return GPUInfo(
            available=True,
            name=name,
            driver_version=driver,
            vram_total_mb=mem.total / (1024 * 1024),
        )
    except Exception:
        return GPUInfo(available=False)


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

_last_net: tuple[float, float, float] | None = None  # (sent, recv, time)


def _net_rates() -> tuple[float, float]:
    """Calculate network TX/RX rates in MB/s since last call."""
    global _last_net
    counters = psutil.net_io_counters()
    now = time.monotonic()
    if _last_net is None:
        _last_net = (counters.bytes_sent, counters.bytes_recv, now)
        return 0.0, 0.0
    prev_sent, prev_recv, prev_time = _last_net
    dt = max(now - prev_time, 0.001)
    sent_rate = (counters.bytes_sent - prev_sent) / dt / (1024 * 1024)
    recv_rate = (counters.bytes_recv - prev_recv) / dt / (1024 * 1024)
    _last_net = (counters.bytes_sent, counters.bytes_recv, now)
    return max(sent_rate, 0.0), max(recv_rate, 0.0)


# ---------------------------------------------------------------------------
# MonitoringService
# ---------------------------------------------------------------------------


class MonitoringService:
    """Captures system metrics and optionally polls in the background."""

    def __init__(self) -> None:
        self._subscribers: list[Any] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def snapshot(self) -> SystemMetrics:
        """Take a single metrics snapshot."""
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net_sent, net_recv = _net_rates()
        gpu = _gpu_snapshot()

        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=None),
            ram_percent=vm.percent,
            ram_used_mb=vm.used / (1024 * 1024),
            ram_total_mb=vm.total / (1024 * 1024),
            disk_percent=disk.percent,
            disk_used_gb=disk.used / (1024 ** 3),
            disk_total_gb=disk.total / (1024 ** 3),
            net_sent_mbps=net_sent,
            net_recv_mbps=net_recv,
            gpu=gpu,
            timestamp=datetime.now(UTC).isoformat(),
        )

    def gpu_info(self) -> GPUInfo:
        """Get static GPU information."""
        return _gpu_info()

    def gpu_available(self) -> bool:
        """Check if an NVIDIA GPU is accessible."""
        return _gpu_info().available

    def subscribe(self, callback: Any) -> None:
        """Register a callback for periodic snapshots."""
        with self._lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Any) -> None:
        """Remove a periodic snapshot callback."""
        with self._lock:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

    def start_polling(self, interval: float = 1.0) -> None:
        """Start a background thread that polls metrics at the given interval."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            args=(interval,),
            daemon=True,
            name="monitoring-poll",
        )
        self._thread.start()
        logger.info("Monitoring polling started (interval=%.1fs)", interval)

    def stop_polling(self) -> None:
        """Stop the background polling thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        _shutdown_nvml()

    def _poll_loop(self, interval: float) -> None:
        """Background loop that captures snapshots and notifies subscribers."""
        while self._running:
            try:
                metrics = self.snapshot()
                with self._lock:
                    subscribers = list(self._subscribers)
                for callback in subscribers:
                    try:
                        callback(metrics)
                    except Exception:
                        logger.debug("Monitoring subscriber error", exc_info=True)
            except Exception:
                logger.debug("Monitoring poll error", exc_info=True)
            time.sleep(interval)


# Module-level singleton
_monitoring_service: MonitoringService | None = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the singleton MonitoringService."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
