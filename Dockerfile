FROM python:3.12-slim AS base

ARG PIP_INDEX_URL
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /workspace

COPY pyproject.toml README.md /workspace/
RUN mkdir -p /workspace/src/app && touch /workspace/src/app/__init__.py

# Install core deps only (cached until pyproject.toml changes)
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 -e "."

FROM base AS docling
# OpenCV (loaded by docling's tableformer via `import cv2`) dynamically links
# against libxcb.so.1; the slim base image lacks it, which crashed every run
# that exercised the table-detection code path. Mirrors the mineru stage below.
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    libxcb1 libgl1 libglib2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*
# Install docling extras (cached until pyproject.toml changes)
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 -e ".[docling]"
# Copy real source (frequent changes, but no pip re-download)
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.docling", "--loglevel=debug"]

FROM base AS mineru
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} HTTPS_PROXY=${HTTPS_PROXY}
# System deps for OpenCV (needed by mineru pipeline backend)
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    libxcb1 libgl1 libglib2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 -e ".[mineru]"
RUN mkdir -p /app/cache
ENV HF_HOME=/app/cache/huggingface HF_HUB_CACHE=/app/cache/huggingface/hub
# Pre-download pipeline models (timeout 300s for ~500MB) — best-effort; skipped if no network.
# At runtime the ./cache bind mount overrides this, so models auto-download on first use.
RUN timeout 300 mineru-models-download -s huggingface -m pipeline 2>/dev/null \
    || (echo "[INFO] Removing incomplete model snapshot for clean auto-download at runtime" \
        && rm -rf /app/cache/huggingface/hub/models--opendatalab--PDF-Extract-Kit-1.0/snapshots/*/models/Layout 2>/dev/null \
        && echo "[INFO] model pre-download failed, will auto-download at runtime")
ENV HTTP_PROXY= HTTPS_PROXY=
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.mineru", "--loglevel=debug"]

FROM base AS opendataloader
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 -e ".[opendataloader]"
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.opendataloader", "--loglevel=debug"]

FROM base AS surya
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 -e ".[surya]"
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.surya", "--loglevel=debug"]
