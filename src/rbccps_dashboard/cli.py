from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RBCCPS research dashboard backend.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3030)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    if args.project_root:
        os.environ["RBCCPS_PROJECT_ROOT"] = args.project_root
    if args.database_url:
        os.environ["RBCCPS_DASHBOARD_DATABASE_URL"] = args.database_url

    import uvicorn

    uvicorn.run(
        "rbccps_dashboard.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
