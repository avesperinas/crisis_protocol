# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
# Installed via pip rather than copied from ghcr.io/astral-sh/uv — ghcr.io is
# unreachable from some networks/registries; Docker Hub (python:3.12-slim) is
# the only registry this build actually depends on.
RUN pip install --no-cache-dir uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependencies only — cached across rebuilds as long as these two files don't change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

# --- dev: bind-mounted source, autoreload ---
FROM base AS dev
CMD ["uv", "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# --- prod: no reload, no bind mount, non-root ---
FROM base AS prod
# /app/data must exist (with the right owner) *before* compose mounts the
# named volume there — otherwise Docker creates it as root on first run and
# appuser can't write the sqlite file into it.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
