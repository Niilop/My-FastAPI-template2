import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.database import Item, User
from backend.services.auth_service import create_access_token


def test_item_lifecycle(client: TestClient, auth_headers: dict[str, str], db: Session) -> None:
    assert client.get("/items", headers=auth_headers).json() == {"items": [], "total": 0}
    response = client.post(
        "/items",
        headers=auth_headers,
        json={"title": "  Plan a set  ", "description": "A reusable example"},
    )
    assert response.status_code == 201
    item = response.json()
    assert item["title"] == "Plan a set"
    assert item["owner_id"] == 1
    path = f"/items/{item['id']}"
    assert client.get(path, headers=auth_headers).json() == item
    response = client.put(path, headers=auth_headers, json={"title": "Renamed", "description": ""})
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert response.json()["description"] == ""
    assert client.get("/items", headers=auth_headers).json()["total"] == 1
    response = client.delete(path, headers=auth_headers)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(path, headers=auth_headers).status_code == 404
    assert db.get(Item, item["id"]) is None


def test_item_ownership(client: TestClient, auth_headers: dict[str, str], db: Session) -> None:
    other = User(email="other@example.com", username="other", password_hash="unused")
    db.add(other)
    db.commit()
    other_headers = {"Authorization": f"Bearer {create_access_token(other.id)}"}
    item = client.post("/items", headers=auth_headers, json={"title": "Private"}).json()
    path = f"/items/{item['id']}"
    assert client.get("/items", headers=other_headers).json() == {"items": [], "total": 0}
    assert client.get(path, headers=other_headers).status_code == 404
    assert client.put(path, headers=other_headers, json={"title": "Stolen"}).status_code == 404
    assert client.delete(path, headers=other_headers).status_code == 404
    assert client.get(path, headers=auth_headers).json()["title"] == "Private"


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/items", None),
        ("POST", "/items", {"title": "Test"}),
        ("GET", "/items/1", None),
        ("PUT", "/items/1", {"title": "Test"}),
        ("DELETE", "/items/1", None),
    ],
)
def test_items_require_auth(client: TestClient, method: str, path: str, body: dict | None) -> None:
    assert client.request(method, path, json=body).status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 256},
        {"title": None},
        {"title": "Test", "description": "x" * 5001},
        {"title": "Test", "description": None},
        {"title": "Test", "owner_id": 999},
    ],
)
def test_item_validation(client: TestClient, auth_headers: dict[str, str], body: dict) -> None:
    item = client.post("/items", headers=auth_headers, json={"title": "Original"}).json()
    assert client.post("/items", headers=auth_headers, json=body).status_code == 422
    path = f"/items/{item['id']}"
    assert client.put(path, headers=auth_headers, json=body).status_code == 422
    assert client.get(path, headers=auth_headers).json()["title"] == "Original"


def test_item_pagination(client: TestClient, auth_headers: dict[str, str], db: Session) -> None:
    db.add_all(Item(owner_id=1, title=f"Item {i}") for i in range(25))
    db.commit()
    page = client.get("/items?limit=20", headers=auth_headers).json()
    assert page["total"] == 25
    assert len(page["items"]) == 20
    second = client.get("/items?limit=20&offset=20", headers=auth_headers).json()
    assert len(second["items"]) == 5
    assert {item["id"] for item in page["items"]}.isdisjoint(item["id"] for item in second["items"])
    for query in ("limit=101", "limit=0", "offset=-1"):
        assert client.get(f"/items?{query}", headers=auth_headers).status_code == 422


def test_missing_items(client: TestClient, auth_headers: dict[str, str]) -> None:
    for method in ("GET", "PUT", "DELETE"):
        response = client.request(
            method,
            "/items/999",
            headers=auth_headers,
            json={"title": "Missing"} if method == "PUT" else None,
        )
        assert response.status_code == 404


def test_csv_routes_removed(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.post("/data/upload", headers=auth_headers).status_code == 404
    assert client.get("/data/catalog", headers=auth_headers).status_code == 404
