from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models.database import Item


def test_catalog_migration_preserves_items(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings().model_copy(
        update={"database_url": f"sqlite:///{tmp_path / 'migration.db'}"}
    )
    monkeypatch.setattr("backend.core.config.get_settings", lambda: settings)
    config = Config("backend/alembic.ini")
    command.upgrade(config, "0001_core")
    engine = create_engine(settings.database_url)
    metadata = MetaData()
    users = Table("users", metadata, autoload_with=engine)
    catalogs = Table("data_catalogs", metadata, autoload_with=engine)
    created = datetime(2026, 1, 1, tzinfo=UTC)
    with engine.begin() as connection:
        connection.execute(
            users.insert().values(
                id=1,
                email="test@example.com",
                username="tester",
                password_hash="unused",
                settings={},
                created_at=created,
                updated_at=created,
            )
        )
        connection.execute(
            catalogs.insert().values(
                id=1,
                user_id=1,
                name="Keep this",
                description="Keep these details",
                file_path="/old/file.csv",
                data_metadata={"num_rows": 10},
                created_at=created,
                updated_at=created,
            )
        )
    command.upgrade(config, "head")
    command.check(config)
    with Session(engine) as session:
        item = session.get(Item, 1)
        assert item is not None
        assert (item.owner_id, item.title, item.description) == (
            1,
            "Keep this",
            "Keep these details",
        )
        assert item.created_at.replace(tzinfo=UTC) == created
        assert item.updated_at.replace(tzinfo=UTC) == created
        session.add(Item(owner_id=1, title="New item"))
        session.commit()
    assert "data_catalogs" not in inspect(engine).get_table_names()
    assert {column["name"] for column in inspect(engine).get_columns("items")} == {
        "id",
        "owner_id",
        "title",
        "description",
        "created_at",
        "updated_at",
    }
    command.downgrade(config, "0001_core")
    with engine.connect() as connection:
        restored = connection.execute(select(catalogs).where(catalogs.c.id == 1)).mappings().one()
        assert restored["name"] == "Keep this"
        assert restored["file_path"] == ""
        assert restored["data_metadata"] == {}
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
