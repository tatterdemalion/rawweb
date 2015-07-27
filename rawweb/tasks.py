from celery import Celery

from rawweb import utils

app = Celery('tasks', backend='rpc://',
             broker='amqp://guest:guest@localhost:5672//')


@app.task
def create_web_formats(path, upload_to, created_path):
    return utils.create_web_formats(path, upload_to, created_path)
