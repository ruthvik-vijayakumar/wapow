import logging
from api.celery_client import celery_app
from api.services.story_pipeline.service import convert_article_to_story
from api.services.conversion_jobs import update_job, is_worker_paused

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.convert_article_to_story")
def convert_article_to_story_task(article_id: str, force: bool = False, job_id: str | None = None):
    """Celery task to convert raw article to a slide deck story."""
    logger.info(f"Celery executing convert_article_to_story_task for article {article_id}")
    
    if is_worker_paused():
        logger.info("Conversion worker is paused. Reverting job to pending.")
        if job_id:
            update_job(job_id, "pending")
        return {"success": False, "message": "Worker is paused"}

    if job_id:
        update_job(job_id, "processing")

    try:
        result = convert_article_to_story(article_id, force=force)
        if job_id:
            update_job(job_id, "completed", ai_summary=result.get("ai_summary"))
        logger.info(f"Celery convert_article_to_story_task completed for article {article_id}")
        return {"success": True, "article_id": article_id}
    except Exception as e:
        logger.exception(f"Celery convert_article_to_story_task failed for article {article_id}")
        if job_id:
            update_job(job_id, "failed", error=str(e))
        raise e
