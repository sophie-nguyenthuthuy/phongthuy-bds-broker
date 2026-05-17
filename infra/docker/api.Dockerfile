# syntax=docker/dockerfile:1.7
# ─── Build stage ─────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 libpangoft2-1.0-0 \
    libcairo2 libffi-dev libgdk-pixbuf-2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4.27 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* LICENSE README.md ./
COPY apps/api/pyproject.toml apps/api/README.md apps/api/
COPY packages/ontology/pyproject.toml packages/ontology/README.md packages/ontology/
COPY apps/api/src apps/api/src
COPY apps/api/alembic apps/api/alembic
COPY apps/api/alembic.ini apps/api/alembic.ini
COPY packages/ontology/src packages/ontology/src
COPY packages/ontology/data packages/ontology/data

RUN uv pip install --system --no-cache \
    ./packages/ontology \
    ./apps/api

# ─── Runtime stage ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps/api/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 \
    libcairo2 libffi8 libgdk-pixbuf-2.0-0 shared-mime-info \
    fonts-noto fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/alembic /usr/local/bin/alembic

WORKDIR /app
COPY --chown=app:app apps/api /app/apps/api
COPY --chown=app:app packages/ontology /app/packages/ontology

USER app
EXPOSE 8000
WORKDIR /app/apps/api

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/healthz').read()" || exit 1

CMD ["uvicorn", "phongthuy_bds.main:app", "--host", "0.0.0.0", "--port", "8000"]
