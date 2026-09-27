import csv
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.endpoints.auth import get_current_user
from backend.core.config import Settings, get_settings
from backend.core.database import get_db
from backend.core.rate_limit import limiter
from backend.models.database import DataCatalog, User
from backend.models.schemas import DataCatalogResponse
from backend.services.data_service import (
    count_user_datasets,
    get_user_datasets,
    process_and_save_dataset,
)

router = APIRouter(prefix="/data", tags=["Data Catalog"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DataCatalogResponse, status_code=201)
@limiter.limit("20/minute")
def upload_data(
    request: Request,
    name: str = Form(..., min_length=1, max_length=255),
    description: str = Form("", max_length=5000),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DataCatalog:
    location: Path | None = None
    try:
        if not file.filename or Path(file.filename).suffix.lower() != ".csv":
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        # Serialize uploads for this user so concurrent requests cannot exceed the quota.
        db.execute(select(User).where(User.id == current_user.id).with_for_update())
        if count_user_datasets(db, current_user.id) >= settings.max_datasets_per_user:
            raise HTTPException(status_code=403, detail="Dataset limit reached")
        if file.size is not None and file.size > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="File exceeds upload size limit")
        directory = settings.data_dir / "uploads" / str(current_user.id)
        directory.mkdir(parents=True, exist_ok=True)
        location = directory / f"{uuid4().hex}.csv"
        size = 0
        with location.open("xb") as destination:
            while chunk := file.file.read(64 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="File exceeds upload size limit")
                destination.write(chunk)
        return process_and_save_dataset(db, current_user.id, location, name, description)
    except Exception as exc:
        db.rollback()
        if location is not None:
            location.unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise
        if isinstance(exc, (ValueError, UnicodeError, csv.Error)):
            raise HTTPException(status_code=400, detail="Invalid UTF-8 CSV file") from exc
        logger.exception("Dataset upload failed")
        raise HTTPException(status_code=500, detail="Could not save dataset") from exc
    finally:
        file.file.close()


@router.get("/", response_model=list[DataCatalogResponse], include_in_schema=False)
@router.get("/catalog", response_model=list[DataCatalogResponse])
def list_datasets(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[DataCatalog]:
    return get_user_datasets(db, current_user.id)


@router.get("/count")
def get_dataset_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict[str, int]:
    count = count_user_datasets(db, current_user.id)
    limit = settings.max_datasets_per_user
    return {"count": count, "limit": limit, "remaining": max(0, limit - count)}
