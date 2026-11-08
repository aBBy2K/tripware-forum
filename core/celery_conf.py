import os
from celery import Celery
from config import REDIS_PORT, REDIS_PASSWORD

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_URL = f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"

celery = Celery(
    "worker",
    broker=REDIS_URL,
    include=["core.celery.tasks"]
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)