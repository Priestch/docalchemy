from celery import Celery

app = Celery("app")
app.config_from_object({"broker_url": f"redis://localhost:16377/0"})
