from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from backend.api.endpoints.auth import get_current_user
from backend.core.database import get_db
from backend.core.rate_limit import limiter
from backend.models.database import User
from backend.models.schemas import ExampleRequest, ExampleResponse, JobSubmitResponse
from backend.services.example_service import run_example_logic
from backend.services.job_service import create_job, run_job

router = APIRouter(prefix="/example", tags=["Example"])


@router.post("/", response_model=ExampleResponse)
def run_example(body: ExampleRequest) -> ExampleResponse:
    return ExampleResponse(result=run_example_logic(body))


@router.post("/async", response_model=JobSubmitResponse, status_code=202)
@limiter.limit("10/minute")
def run_example_async(
    request: Request,
    body: ExampleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobSubmitResponse:
    job = create_job(db, current_user.id, "example")
    background_tasks.add_task(run_job, job.id, lambda session: {"result": run_example_logic(body)})
    return JobSubmitResponse(job_id=job.id, status=job.status)
