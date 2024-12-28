FROM python:3.12-slim

WORKDIR /app

RUN pip install celery redis docling

COPY ./src/app/infrastructure/storage.py /app/analyser/storage_service.py
COPY ./src/app/analyser /app/analyser

CMD ["celery", "-A", "analyser.tasks:app", "worker", "--loglevel=debug"]