def main():

    from celery import Celery

    bee_app = Celery('bee')
    bee_app.config_from_object({
        'broker_url':f'redis://localhost:63798/0'
    })

    bee_app.send_task("celery_app.add", args=[1, 2])


if __name__ == "__main__":
    main()
