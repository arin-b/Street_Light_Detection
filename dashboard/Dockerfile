FROM node:20-slim AS frontend
WORKDIR /frontend
COPY dashboard/frontend/package.json dashboard/frontend/tsconfig.json dashboard/frontend/vite.config.ts dashboard/frontend/index.html ./
COPY dashboard/frontend/src ./src
RUN npm install
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
COPY dashboard ./dashboard
COPY --from=frontend /frontend/dist ./dashboard/frontend/dist
RUN pip install --no-cache-dir -e ".[dashboard]"
EXPOSE 8000
CMD ["rbccps-dashboard", "--host", "0.0.0.0", "--port", "8000"]
