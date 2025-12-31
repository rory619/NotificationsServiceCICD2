import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_DB_URL,connect_args={"check_same_thread": False},poolclass=StaticPool,)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # cleanup so overrides do not go into other tests
    app.dependency_overrides.clear()


def create_notification(client, payload=None):
    payload = payload or {"user_id": 1, "channel": "email", "message": "hello"}
    r = client.post("/api/notifications", json=payload)
    assert r.status_code == 201
    return r.json()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_notification(client):
    data = create_notification(client)
    assert "id" in data
    assert "status" in data


def test_list_notifications(client):
    create_notification(client)
    r = client.get("/api/notifications?limit=10&offset=0")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_get_notification(client):
    created = create_notification(client)
    notif_id = created["id"]

    r = client.get(f"/api/notifications/{notif_id}")
    assert r.status_code == 200
    assert r.json()["id"] == notif_id


def test_get_notification_404(client):
    r = client.get("/api/notifications/999999")
    assert r.status_code == 404


def test_update_notification(client):
    created = create_notification(client)
    notif_id = created["id"]

    r = client.put(f"/api/notifications/{notif_id}",json={"user_id": 2, "channel": "sms", "message": "updated"},)
    assert r.status_code == 200
    assert r.json()["id"] == notif_id


def test_update_notification_404(client):
    r = client.put("/api/notifications/999999",json={"user_id": 2, "channel": "sms", "message": "updated"},)
    assert r.status_code == 404


def test_delete_notification(client):
    created = create_notification(client)
    notif_id = created["id"]

    r = client.delete(f"/api/notifications/{notif_id}")
    assert r.status_code == 204


def test_delete_notification_404(client):
    r = client.delete("/api/notifications/999999")
    assert r.status_code == 404


