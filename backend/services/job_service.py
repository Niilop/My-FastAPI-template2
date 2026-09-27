import logging
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.database import BackgroundJob, JobStatus

logger = logging.getLogger(__name__)


def create_job(db: Session, user_id: int, job_type: str) -> BackgroundJob:
    job = BackgroundJob(id=str(uuid4()), user_id=user_id, job_type=job_type)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str, user_id: int) -> BackgroundJob | None:
    return db.scalar(
        select(BackgroundJob).where(BackgroundJob.id == job_id, BackgroundJob.user_id == user_id)
    )


def run_job(job_id: str, task: Callable[[Session], dict[str, Any]]) -> None:
    """Run a short in-process task with its own database session."""
    with SessionLocal() as db:
        job = db.get(BackgroundJob, job_id)
        if job is None:
            return
        try:
            job.status = JobStatus.RUNNING
            db.commit()
            job.result = task(db)
            job.status = JobStatus.COMPLETED
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Background job %s failed", job_id)
            job.status = JobStatus.FAILED
            job.error = "Task failed"
            db.commit()
