from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("tasks", broker=settings.celery.BROKER_URL, backend=settings.celery.RESULT_BACKEND_URL or None,
                    include=["app.domain.system.tasks"])

__all__ = [
    "celery_app",
]
