# syntax=docker/dockerfile:1.7
# ---- builder: resolve + install deps into a venv with uv ---------------------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# psycopg2 (non-binary) compiles from source → needs libpq + a compiler.
# These stay in the builder only; the runtime image gets just the .so it needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first, from the lockfile, without the project itself —
# this layer is cached until uv.lock/pyproject.toml change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- runtime: slim image, no build tools, non-root -------------------------
FROM python:3.13-slim-bookworm AS runtime

# libpq5 is psycopg2's only runtime dependency.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

USER app
EXPOSE 8080

# Default = web. compose overrides command for worker / migrate.
CMD ["gunicorn", "app:app", "-c", "gunicorn_config.py"]
