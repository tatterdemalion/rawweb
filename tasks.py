from celery import Celery

import utils

app = Celery('tasks', backend='rpc://',
             broker='amqp://guest:guest@localhost:5672//')


@app.task
def create_web_formats(path, upload_to):
    return utils.create_web_formats(path, upload_to)
