from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.endpoints.auth import get_current_user
from backend.core.database import get_db
from backend.models.database import User
from backend.models.schemas import JobStatusResponse
from backend.services.job_service import get_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
def job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    job = get_job(db, str(job_id), current_user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse.model_validate(job)
