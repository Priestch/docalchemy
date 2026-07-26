FROM python:3.12-slim AS base

ARG PIP_INDEX_URL
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /workspace

COPY pyproject.toml README.md /workspace/
COPY docker/requirements/base.txt /tmp/base.req.txt
RUN mkdir -p /workspace/src/app && touch /workspace/src/app/__init__.py

# Install fully pinned core deps from the compiled lockfile (reproducible — no
# live PyPI re-resolution), then the project itself without re-resolving.
# Regenerate with: uv pip compile pyproject.toml
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 --requirement /tmp/base.req.txt \
    && pip install --no-deps -e "."

FROM base AS docling
# OpenCV (loaded by docling's tableformer via `import cv2`) dynamically links
# against libxcb.so.1; the slim base image lacks it, which crashed every run
# that exercised the table-detection code path. Mirrors the mineru stage below.
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    libxcb1 libgl1 libglib2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*
# Install fully pinned deps from the compiled lockfile (reproducible).
# Regenerate with: uv pip compile --extra docling pyproject.toml
COPY docker/requirements/docling.txt /tmp/docling.req.txt
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 --requirement /tmp/docling.req.txt
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
COPY docker/requirements/mineru.txt /tmp/mineru.req.txt
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 --requirement /tmp/mineru.req.txt
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
# opendataloader_pdf shells out to a JAR; it needs a JVM on PATH.
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    default-jdk-headless \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
COPY docker/requirements/opendataloader.txt /tmp/opendataloader.req.txt
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 --requirement /tmp/opendataloader.req.txt
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.opendataloader", "--loglevel=debug"]

FROM base AS surya
# Install fully pinned deps from the compiled lockfile (reproducible — no live
# PyPI re-resolution). Regenerate with: uv pip compile --extra surya pyproject.toml
COPY docker/requirements/surya.txt /tmp/surya.req.txt
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 --requirement /tmp/surya.req.txt
# surya >=0.20 runs recognition through an llamacpp backend that spawns the
# upstream `llama-server` binary (CPU path when no GPU). It is not pip-installable,
# so pull the prebuilt release and point surya at it via LLAMA_CPP_BINARY.
# The .so libs ship alongside the binary, hence LD_LIBRARY_PATH.
ARG LLAMA_CPP_TAG=b9754
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
        curl ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/llama.cpp \
    && curl -fsSL -o /tmp/llama.tar.gz \
        "https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_CPP_TAG}/llama-${LLAMA_CPP_TAG}-bin-ubuntu-x64.tar.gz" \
    && tar -xzf /tmp/llama.tar.gz -C /opt/llama.cpp \
    && rm /tmp/llama.tar.gz \
    && ln -sfn "/opt/llama.cpp/llama-${LLAMA_CPP_TAG}" /opt/llama.cpp/dist
ENV LLAMA_CPP_BINARY=/opt/llama.cpp/dist/llama-server
ENV LD_LIBRARY_PATH=/opt/llama.cpp/dist
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.surya", "--loglevel=debug"]

FROM base AS franken_ocr
# focr is a pure-Rust, CPU-only OCR binary (unlimited-ocr VLM). It is NOT pip-
# installable; pull the prebuilt linux x86_64 release and SHA-verify it. The
# ~3.9 GB model is intentionally NOT baked in — it lives in the shared cache
# mount (FOCR_MODEL_DIR=/app/cache/franken_ocr/models), fetched once, shared
# across rebuilds. Regenerate the pip lock with:
#   uv pip compile --extra franken_ocr pyproject.toml
ARG FOCR_VERSION=v0.3.0
ARG FOCR_SHA256=d7bc376055927e5e839c76d5bdfe4bbb1b9da6cb7720c31094715878e2b54309
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
        curl ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL --retry 5 --retry-delay 3 -o /usr/local/bin/focr \
        "https://github.com/Dicklesworthstone/franken_ocr/releases/download/${FOCR_VERSION}/focr-x86_64-unknown-linux-gnu" \
    && echo "${FOCR_SHA256}  /usr/local/bin/focr" | sha256sum -c - \
    && chmod +x /usr/local/bin/focr
COPY docker/requirements/franken_ocr.txt /tmp/franken_ocr.req.txt
RUN --mount=type=cache,id=pip,target=/root/.cache/pip,sharing=shared \
    pip install --default-timeout=120 --requirement /tmp/franken_ocr.req.txt
ENV FOCR_BINARY=/usr/local/bin/focr
ENV FOCR_MODEL_DIR=/app/cache/franken_ocr/models
COPY src /workspace/src
CMD ["celery", "-A", "app.infrastructure.workers.celery_app:celery_app", "worker", "-Q", "analysis.franken_ocr", "--loglevel=debug"]
