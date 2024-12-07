from celery import Celery

app = Celery('app1', broker='redis://redis:6379/0')

@app.task
def add(x, y):
    return x + y