from celery import Celery

celery_app = Celery("docalchemy")
celery_app.conf.update(
    broker_url="redis://localhost:16377/0",
)
