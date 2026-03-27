FROM python:3.12-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install backend dependencies
COPY backend/pyproject.toml backend/uv.lock ./backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ ./

# Copy pre-built frontend (run `make build` before deploying)
COPY frontend/build /app/frontend/build

# Data directory lives on a persistent Fly volume
RUN mkdir -p /data && ln -s /data /app/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
