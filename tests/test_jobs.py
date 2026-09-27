from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.database import BackgroundJob, JobStatus, User
from backend.services.auth_service import create_access_token
from backend.services.job_service import create_job, run_job


def test_background_example(client: TestClient, auth_headers: dict[str, str], db: Session) -> None:
    response = client.post(
        "/example/async", headers=auth_headers, json={"name": "Tester", "task": "demo"}
    )
    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    job_id = response.json()["job_id"]
    response = client.get(f"/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert "Tester" in response.json()["result"]["result"]
    other = User(email="other@example.com", username="other", password_hash="unused")
    db.add(other)
    db.commit()
    headers = {"Authorization": f"Bearer {create_access_token(other.id)}"}
    assert client.get(f"/jobs/{job_id}", headers=headers).status_code == 404
    assert client.get(f"/jobs/{job_id}").status_code == 401


def test_failed_job_rolls_back(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    job = create_job(db, 1, "test")

    def task(session: Session) -> dict:
        user = session.get(User, 1)
        user.username = "should-rollback"
        session.flush()
        raise RuntimeError("sensitive internal error")

    run_job(job.id, task)
    db.expire_all()
    assert db.get(BackgroundJob, job.id).status == JobStatus.FAILED
    assert db.get(User, 1).username == "tester"
    response = client.get(f"/jobs/{job.id}", headers=auth_headers)
    assert response.json()["error"] == "Task failed"
