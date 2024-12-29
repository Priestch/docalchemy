def main():
    from celery import Celery

    bee_app = Celery("app")
    bee_app.config_from_object({"broker_url": f"redis://localhost:16377/0"})

    bee_app.send_task("analyser.tasks.analyse_document", args=["361943fe584e2f3332f7bc9e056b11d0.pdf", "docling"])


if __name__ == "__main__":
    main()
