from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from rbccps_dashboard.api.routes import components as component_routes
from rbccps_dashboard.api.routes import experiments, home, yaml_configs
from rbccps_dashboard.api.routes import monitoring as monitoring_routes
from rbccps_dashboard.api.routes import training as training_routes
from rbccps_dashboard.api.routes import visualizations as visualization_routes
from rbccps_dashboard.api.routes import attention as attention_routes
from rbccps_dashboard.api.routes import reports as report_routes
from rbccps_dashboard.api.routes import sweeps as sweep_routes
from rbccps_dashboard.api.routes import model_export as model_export_routes
from rbccps_dashboard.api.routes import tracking as tracking_routes
from rbccps_dashboard.api.routes import websocket as ws_routes
from rbccps_dashboard.config import get_settings
from rbccps_dashboard.database import init_db
from rbccps_dashboard.services.monitoring import get_monitoring_service
from rbccps_dashboard.services.training import get_training_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle: start monitoring on boot, cleanup on shutdown."""
    monitoring = get_monitoring_service()
    monitoring.start_polling(interval=1.0)
    logger.info("Monitoring polling started")
    yield
    monitoring.stop_polling()
    training = get_training_service()
    training.shutdown()
    logger.info("Services shut down")


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_directories()
    init_db()

    app = FastAPI(
        title="Nighttime Streetlight Detection Research Dashboard",
        version="0.5.0",
        description="Nighttime Streetlight Detection Dashboard — Full Pipeline.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Phase 1 routers
    app.include_router(home.router, prefix="/api")
    app.include_router(experiments.router, prefix="/api")
    app.include_router(yaml_configs.router, prefix="/api")

    # Phase 2 routers
    app.include_router(training_routes.router, prefix="/api")
    app.include_router(monitoring_routes.router, prefix="/api")
    app.include_router(ws_routes.router, prefix="/api")

    # Phase 3 routers
    app.include_router(visualization_routes.router, prefix="/api")
    app.include_router(attention_routes.router, prefix="/api")
    app.include_router(tracking_routes.router, prefix="/api")

    # Phase 4 routers
    app.include_router(sweep_routes.router, prefix="/api")
    app.include_router(report_routes.router, prefix="/api")

    # Extension routers
    app.include_router(component_routes.router, prefix="/api")
    app.include_router(model_export_routes.router, prefix="/api")

    if settings.frontend_dist.exists():
        app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="dashboard")

    return app


app = create_app()
