FROM python:3.12-slim

WORKDIR /app

COPY ./src/app/analyser/docling.py /app/celery_app.py

RUN pip install celery redis

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]