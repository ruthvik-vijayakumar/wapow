from celery import Celery
from scraper.config import settings

celery_app = Celery(
    "wapow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Optional configuration settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Force task registration by importing the jobs module
import scraper.tasks.jobs  # noqa
