import csv
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.database import DataCatalog


def profile_csv(file_path: Path) -> dict[str, Any]:
    with file_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        columns = next(reader, [])
        if not columns or any(not column.strip() for column in columns):
            raise ValueError("CSV must contain non-empty column names")
        if len(set(columns)) != len(columns):
            raise ValueError("CSV column names must be unique")
        missing = dict.fromkeys(columns, 0)
        rows = 0
        for row in reader:
            if len(row) != len(columns):
                raise ValueError("Every CSV row must have the same number of columns as the header")
            rows += 1
            for column, value in zip(columns, row, strict=True):
                if not value.strip():
                    missing[column] += 1
    return {
        "num_rows": rows,
        "num_cols": len(columns),
        "columns": columns,
        "missing_values": missing,
    }


def process_and_save_dataset(
    db: Session, user_id: int, file_path: Path, name: str, description: str
) -> DataCatalog:
    catalog = DataCatalog(
        user_id=user_id,
        name=name,
        file_path=str(file_path),
        description=description,
        data_metadata=profile_csv(file_path),
    )
    db.add(catalog)
    db.commit()
    return catalog


def get_user_datasets(db: Session, user_id: int) -> list[DataCatalog]:
    return list(
        db.scalars(
            select(DataCatalog)
            .where(DataCatalog.user_id == user_id)
            .order_by(DataCatalog.id.desc())
        )
    )


def count_user_datasets(db: Session, user_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(DataCatalog).where(DataCatalog.user_id == user_id)
        )
        or 0
    )
