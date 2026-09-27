from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models.database import DataCatalog
from backend.services.auth_service import create_access_token


def upload(client: TestClient, headers: dict[str, str], content: bytes = b"a,b\n1,\n") -> Response:
    return client.post(
        "/data/upload",
        headers=headers,
        data={"name": "Dataset"},
        files={"file": ("../../same.csv", content, "text/csv")},
    )


def test_upload_isolated_and_no_overwrite(
    client: TestClient, auth_headers: dict[str, str], db: Session, tmp_path: Path
) -> None:
    for _ in range(2):
        response = upload(client, auth_headers)
        assert response.status_code == 201
        assert "file_path" not in response.json()
        assert response.json()["data_metadata"] == {
            "columns": ["a", "b"],
            "num_cols": 2,
            "num_rows": 1,
            "missing_values": {"a": 0, "b": 1},
        }
    catalogs = list(db.scalars(select(DataCatalog)))
    assert len({row.file_path for row in catalogs}) == 2
    assert all(Path(row.file_path).is_relative_to(tmp_path / "uploads" / "1") for row in catalogs)
    assert all(Path(row.file_path).read_bytes() == b"a,b\n1,\n" for row in catalogs)
    assert len(client.get("/data/catalog", headers=auth_headers).json()) == 2
    response = client.post(
        "/auth/register",
        json={
            "email": "other@example.com",
            "username": "other",
            "password": "another-long-password",
        },
    )
    other = {"Authorization": f"Bearer {create_access_token(response.json()['id'])}"}
    assert client.get("/data/catalog", headers=other).json() == []
    assert client.get("/data/count", headers=other).json()["count"] == 0


@pytest.mark.parametrize("content", [b"", b"a,a\n1,2", b"a,b\n1", b"\xff", b'a,b\n"unclosed'])
def test_bad_csv_cleanup(
    client: TestClient, auth_headers: dict[str, str], tmp_path: Path, content: bytes
) -> None:
    assert upload(client, auth_headers, content).status_code == 400
    assert not list(tmp_path.rglob("*.csv"))
    assert client.get("/data/catalog", headers=auth_headers).json() == []


def test_size_and_count_limits(
    client: TestClient, auth_headers: dict[str, str], tmp_path: Path
) -> None:
    settings = get_settings().model_copy(
        update={"data_dir": tmp_path, "max_upload_bytes": 8, "max_datasets_per_user": 1}
    )
    client.app.dependency_overrides[get_settings] = lambda: settings
    assert upload(client, auth_headers, b"a,b\n123,456\n").status_code == 413
    assert not list(tmp_path.rglob("*.csv"))
    assert upload(client, auth_headers).status_code == 201
    assert upload(client, auth_headers).status_code == 403
    assert client.get("/data/count", headers=auth_headers).json() == {
        "count": 1,
        "limit": 1,
        "remaining": 0,
    }


def test_upload_requires_auth(client: TestClient) -> None:
    assert upload(client, {}).status_code == 401


@pytest.mark.parametrize("at_upload_limit", [False, True])
def test_large_csv_field(
    client: TestClient, auth_headers: dict[str, str], at_upload_limit: bool
) -> None:
    max_bytes = get_settings().max_upload_bytes
    field_size = max_bytes - len(b"text\n\n") if at_upload_limit else 131_073
    content = b"text\n" + b"x" * field_size + b"\n"
    response = upload(client, auth_headers, content)
    assert response.status_code == 201
    assert response.json()["data_metadata"] == {
        "columns": ["text"],
        "num_cols": 1,
        "num_rows": 1,
        "missing_values": {"text": 0},
    }
    if at_upload_limit:
        assert upload(client, auth_headers, content + b"\n").status_code == 413


def test_failed_commit_cleans_up(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_commit(session: Session) -> None:
        session.flush()
        raise RuntimeError("private database details")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = upload(client, auth_headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Could not save dataset"}
    assert not list(tmp_path.rglob("*.csv"))
    assert client.get("/data/catalog", headers=auth_headers).json() == []
