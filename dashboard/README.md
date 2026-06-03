# Nighttime Streetlight Detection Research Dashboard

Phase 1 adds the foundation for the research control center described in the dashboard specification:

- FastAPI backend with OpenAPI docs at `/docs`
- SQLite database for experiment metadata and future run artifacts
- Experiment CRUD with generated YAML experiment files
- YAML editor API that reads and writes existing project YAML files safely
- React + TypeScript + Vite + Material UI frontend for home metrics, experiment management, and YAML editing

## Backend

Install the dashboard dependencies:

```bash
pip install -e ".[dashboard]"
```

Run the API:

```bash
rbccps-dashboard --host 127.0.0.1 --port 8000
```

The default database lives at `.dashboard/dashboard.sqlite3`. Generated experiment YAML files live under `configs/dashboard/experiments/`.

Useful endpoints:

- `GET /api/summary`
- `GET /api/experiments`
- `POST /api/experiments`
- `PATCH /api/experiments/{experiment_id}`
- `DELETE /api/experiments/{experiment_id}`
- `GET /api/yaml-configs`
- `GET /api/yaml-configs/file?path=src/rbccps_od/config/original.yaml`
- `PUT /api/yaml-configs/file`

## Frontend

Run the Vite app in a second terminal:

```bash
cd dashboard/frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to `http://127.0.0.1:8000`.

Build production assets:

```bash
cd dashboard/frontend
npm run build
```

If `dashboard/frontend/dist` exists, the FastAPI app serves it from `/`.

## Docker

```bash
docker compose -f dashboard/docker-compose.yml up --build
```

The compose service exposes the backend on `http://127.0.0.1:8000`.
