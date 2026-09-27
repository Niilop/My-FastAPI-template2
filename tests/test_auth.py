from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models.database import User
from backend.services.auth_service import create_access_token


def test_registration_login_and_profile(client: TestClient, db: Session) -> None:
    payload = {
        "email": "Test@EXAMPLE.com",
        "username": "tester",
        "password": "a-long-test-password",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "password_hash" not in response.json()
    user = db.scalar(select(User))
    assert user.password_hash.startswith("$argon2id$")
    for identifier in ("tester", "TEST@example.com"):
        response = client.post(
            "/auth/login", data={"username": identifier, "password": payload["password"]}
        )
        assert response.status_code == 200
        profile = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"}
        )
        assert profile.status_code == 200
        assert profile.json()["id"] == user.id


@pytest.mark.parametrize("duplicate", [{"email": "TESTER@example.com"}, {"username": "tester"}])
def test_duplicate_registration(
    client: TestClient, auth_headers: dict[str, str], duplicate: dict[str, str]
) -> None:
    payload = {
        "email": "other@example.com",
        "username": "other",
        "password": "a-long-test-password",
    }
    payload.update(duplicate)
    assert client.post("/auth/register", json=payload).status_code == 409
    assert client.get("/auth/me", headers=auth_headers).status_code == 200


@pytest.mark.parametrize(
    "updates",
    [
        {"password": "short"},
        {"password": "x" * 129},
        {"username": "a@b.com"},
        {"email": "invalid"},
        {"username": ""},
    ],
)
def test_registration_validation(client: TestClient, updates: dict[str, str]) -> None:
    payload = {
        "email": "test@example.com",
        "username": "tester",
        "password": "a-long-test-password",
    }
    payload.update(updates)
    assert client.post("/auth/register", json=payload).status_code == 422


@pytest.mark.parametrize("identifier", ["tester", "missing"])
def test_wrong_credentials(
    client: TestClient, auth_headers: dict[str, str], identifier: str
) -> None:
    response = client.post("/auth/login", data={"username": identifier, "password": "wrong"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_tokens(client: TestClient, auth_headers: dict[str, str]) -> None:
    key = get_settings().secret_key.get_secret_value()
    tokens = [
        "invalid",
        create_access_token(1, timedelta(seconds=-1)),
        create_access_token(999),
        jwt.encode({"sub": "1"}, key, algorithm="HS256"),
        jwt.encode({"sub": "not-an-id", "iat": 1, "exp": 9999999999}, key, algorithm="HS256"),
        jwt.encode({"sub": "1", "iat": 1, "exp": 9999999999}, "x" * 40, algorithm="HS256"),
    ]
    for token in tokens:
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    assert client.get("/auth/me").status_code == 401


def test_login_rate_limit(client: TestClient) -> None:
    for _ in range(10):
        assert (
            client.post(
                "/auth/login", data={"username": "missing", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post("/auth/login", data={"username": "missing", "password": "wrong"}).status_code
        == 429
    )
