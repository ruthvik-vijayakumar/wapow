from celery import Celery, signals
from celery.result import AsyncResult
from kombu import Queue

from scraper.config import settings
from scraper.utils.dashboard_logging import configure_dashboard_logging

celery_app = Celery(
    "wapow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

configure_dashboard_logging()


@signals.after_setup_logger.connect
def _attach_dashboard_logger(logger=None, **kwargs):
    configure_dashboard_logging(logger=logger)


@signals.after_setup_task_logger.connect
def _attach_dashboard_task_logger(logger=None, **kwargs):
    configure_dashboard_logging(logger=logger)

# Optional configuration settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="celery",
    task_queues=(
        Queue("celery"),
        Queue("rss"),
        Queue("conversion"),
    ),
    task_routes={
        "tasks.run_rss_scrape": {"queue": "rss"},
        "tasks.convert_article_to_story": {"queue": "conversion"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    task_reject_on_worker_lost=False,
    task_ignore_result=True,
    task_store_errors_even_if_ignored=False,
    result_expires=3600,
)


def forget_task_result(task_id: str | None) -> None:
    if not task_id:
        return
    try:
        AsyncResult(task_id, app=celery_app).forget()
    except Exception:
        pass


@signals.task_postrun.connect
def _forget_completed_task(task_id=None, **kwargs):
    forget_task_result(task_id)


@signals.task_revoked.connect
def _forget_revoked_task(request=None, **kwargs):
    forget_task_result(getattr(request, "id", None))

# Force task registration by importing the jobs module
import scraper.tasks.jobs  # noqa
