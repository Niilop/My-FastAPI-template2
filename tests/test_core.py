import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from backend.core.config import Settings
from backend.core.database import get_db


def test_health_and_routes(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert not any(path.startswith(("/chat", "/rag", "/llm", "/metrics")) for path in paths)
    assert client.post("/example/", json={"name": "Tester", "task": "test"}).status_code == 200


def test_database_unavailable(client: TestClient) -> None:
    class Unavailable:
        def execute(self, statement) -> None:
            raise OperationalError("SELECT 1", {}, Exception("internal connection details"))

    client.app.dependency_overrides[get_db] = lambda: Unavailable()
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


@pytest.mark.parametrize("value", ["http://one,http://two", '["http://one", "http://two"]'])
def test_cors_parsing(value: str) -> None:
    assert Settings(_env_file=None, cors_origins=value).cors_origins == ["http://one", "http://two"]


@pytest.mark.parametrize("secret", ["", "short", "your-secret-key-change-this-in-production"])
def test_secret_validation(secret: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key=secret)


def test_cors_preflight(client: TestClient) -> None:
    headers = {"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"}
    assert (
        client.options("/auth/login", headers=headers).headers["access-control-allow-origin"]
        == headers["Origin"]
    )
    headers["Origin"] = "http://untrusted.example"
    assert client.options("/auth/login", headers=headers).status_code == 400
