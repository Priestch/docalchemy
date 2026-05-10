FROM python:3.12-slim

WORKDIR /workspace

RUN pip install celery redis docling "advanced-alchemy[uuid]" litestar asyncpg

COPY src /workspace/src
COPY docker/pyproject.docling.toml /workspace/pyproject.toml

RUN pip install -e .

CMD ["celery", "-A", "app.analyser.tasks:app", "worker", "--loglevel=debug"]