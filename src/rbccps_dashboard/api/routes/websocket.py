"""WebSocket endpoints for real-time log streaming and system monitoring."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from rbccps_dashboard.services.monitoring import get_monitoring_service
from rbccps_dashboard.services.training import get_training_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ---------------------------------------------------------------------------
# Log streaming WebSocket
# ---------------------------------------------------------------------------

@router.websocket("/ws/logs/{run_id}")
async def ws_logs(websocket: WebSocket, run_id: int) -> None:
    """Stream log lines for a specific training run.

    On connect, sends the last 200 lines from the ring buffer, then pushes
    new lines as they arrive via a subscriber callback.
    """
    await websocket.accept()
    service = get_training_service()
    buf = service.get_buffer(run_id)

    queue: asyncio.Queue[dict] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_new_line(entry: dict) -> None:
        """Called from the reader thread — schedule into the async loop."""
        loop.call_soon_threadsafe(queue.put_nowait, entry)

    try:
        # Send recent history
        if buf:
            for entry in buf.recent(200):
                await websocket.send_text(json.dumps(entry))
            buf.subscribe(on_new_line)

        # Stream new lines
        while True:
            try:
                entry = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_text(json.dumps(entry))
            except asyncio.TimeoutError:
                # Send a heartbeat to keep the connection alive
                await websocket.send_text(json.dumps({"type": "heartbeat"}))

    except WebSocketDisconnect:
        logger.debug("Log WebSocket disconnected for run %d", run_id)
    except Exception:
        logger.debug("Log WebSocket error for run %d", run_id, exc_info=True)
    finally:
        if buf:
            buf.unsubscribe(on_new_line)


# ---------------------------------------------------------------------------
# System monitoring WebSocket
# ---------------------------------------------------------------------------

@router.websocket("/ws/monitoring")
async def ws_monitoring(websocket: WebSocket) -> None:
    """Stream system metrics at ~1 second intervals.

    Uses the MonitoringService polling loop via a subscriber callback.
    Falls back to direct polling if the background loop is not running.
    """
    await websocket.accept()
    service = get_monitoring_service()

    queue: asyncio.Queue[dict] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_snapshot(metrics: object) -> None:
        """Called from the monitoring thread."""
        try:
            data = metrics.model_dump() if hasattr(metrics, "model_dump") else {}
            loop.call_soon_threadsafe(queue.put_nowait, data)
        except Exception:
            pass

    service.subscribe(on_snapshot)

    try:
        # If background polling is not running, start it
        if not service._running:
            service.start_polling(interval=1.0)

        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=5.0)
                await websocket.send_text(json.dumps(data))
            except asyncio.TimeoutError:
                # Fallback: take a snapshot directly
                snapshot = service.snapshot()
                await websocket.send_text(snapshot.model_dump_json())

    except WebSocketDisconnect:
        logger.debug("Monitoring WebSocket disconnected")
    except Exception:
        logger.debug("Monitoring WebSocket error", exc_info=True)
    finally:
        service.unsubscribe(on_snapshot)
