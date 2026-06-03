# backend/app/services/celery_tasks.py
# Celery async tasks for long-running operations

from celery import Celery, Task
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import SessionLocal
from app.models import ImportJob
from app.services.csv_import import CsvImportService, ImportMode
import structlog

logger = structlog.get_logger(__name__)

# Initialize Celery
celery_app = Celery(
    "aidlc",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)


class DatabaseTask(Task):
    """Base task class with database session handling"""

    def __call__(self, *args, **kwargs):
        db = SessionLocal()
        try:
            return self.run(*args, db=db, **kwargs)
        finally:
            db.close()

    def run(self, *args, **kwargs):
        raise NotImplementedError


@celery_app.task(base=DatabaseTask, bind=True)
def execute_csv_import_task(
    self,
    job_id: str,
    file_content: bytes,
    master_type: str,
    import_mode: str,
    user_id: str,
    db: Session = None
):
    """
    Async task to execute CSV import.
    Processes file, creates/updates entities, tracks progress.
    """
    logger.info(
        "csv_import_task_started",
        job_id=job_id,
        master_type=master_type,
        user_id=user_id,
        task_id=self.request.id
    )

    try:
        # Get job
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            logger.error("csv_import_job_not_found", job_id=job_id)
            return {"status": "FAILED", "error": "Job not found"}

        # Update status
        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        db.commit()

        # Execute import
        service = CsvImportService(db)
        mode = ImportMode[import_mode]

        result, updated_job = service.execute_import(
            job_id=job_id,
            file_content=file_content,
            master_type=master_type,
            import_mode=mode,
            user_id=user_id
        )

        logger.info(
            "csv_import_task_completed",
            job_id=job_id,
            created=result.created_count,
            updated=result.updated_count,
            skipped=result.skipped_count,
            errors=result.error_count
        )

        return {
            "status": "COMPLETED",
            "job_id": job_id,
            "created_count": result.created_count,
            "updated_count": result.updated_count,
            "skipped_count": result.skipped_count,
            "error_count": result.error_count
        }

    except Exception as e:
        logger.error(
            "csv_import_task_failed",
            job_id=job_id,
            error=str(e)
        )

        try:
            job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.error_count = 1
                job.error_details = json.dumps([{"error": str(e)}])
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as db_error:
            logger.error("csv_import_job_update_failed", error=str(db_error))

        return {
            "status": "FAILED",
            "job_id": job_id,
            "error": str(e)
        }


@celery_app.task(bind=True)
def update_import_progress(
    self,
    job_id: str,
    processed_rows: int,
    error_count: int
):
    """
    Task to update import progress.
    Called periodically during long-running imports.
    """
    db = SessionLocal()
    try:
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if job:
            job.processed_rows = processed_rows
            job.error_count = error_count
            db.commit()
            logger.info(
                "progress_updated",
                job_id=job_id,
                processed_rows=processed_rows,
                error_count=error_count
            )
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_old_import_jobs(self, days: int = 30):
    """
    Cleanup completed import jobs older than specified days.
    Run periodically via Celery beat.
    """
    from datetime import timedelta
    from sqlalchemy import and_

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(ImportJob).filter(
            and_(
                ImportJob.status.in_(["COMPLETED", "FAILED"]),
                ImportJob.completed_at < cutoff_date
            )
        ).delete()

        db.commit()

        logger.info(
            "cleanup_completed",
            deleted_count=deleted_count,
            days=days
        )

        return {"deleted_count": deleted_count}

    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
        raise
    finally:
        db.close()


# Celery Beat Schedule
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-imports': {
        'task': 'app.services.celery_tasks.cleanup_old_import_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'kwargs': {'days': 30}
    },
}
