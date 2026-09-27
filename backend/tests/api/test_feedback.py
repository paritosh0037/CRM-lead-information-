import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.feedback import Feedback

# Setup an in-memory SQLite database for testing
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

@pytest.fixture(name="client")
def client_fixture():
    SQLModel.metadata.create_all(engine)
    client = TestClient(app)
    yield client
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture():
    with Session(engine) as session:
        yield session

def test_accept_recommendation(client: TestClient):
    response = client.post(
        "/api/feedback/L123/accept",
        json={"original_action": "CALL"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "L123"
    assert data["original_action"] == "CALL"
    assert data["override_action"] is None
    assert data["reason"] is None
    assert "timestamp" in data

def test_override_recommendation(client: TestClient):
    response = client.post(
        "/api/feedback/L123/override",
        json={
            "original_action": "CALL",
            "override_action": "EMAIL",
            "reason": "Lead prefers email"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "L123"
    assert data["original_action"] == "CALL"
    assert data["override_action"] == "EMAIL"
    assert data["reason"] == "Lead prefers email"
    assert "timestamp" in data

def test_override_recommendation_invalid_action(client: TestClient):
    response = client.post(
        "/api/feedback/L123/override",
        json={
            "original_action": "CALL",
            "override_action": "INVALID",
            "reason": "Bad action"
        }
    )
    assert response.status_code == 400

def test_override_recommendation_missing_reason(client: TestClient):
    response = client.post(
        "/api/feedback/L123/override",
        json={
            "original_action": "CALL",
            "override_action": "EMAIL",
            "reason": ""
        }
    )
    assert response.status_code == 422

def test_get_feedback(client: TestClient):
    # Create some feedback
    client.post(
        "/api/feedback/L999/accept",
        json={"original_action": "DEMO"}
    )
    
    response = client.get("/api/feedback/L999")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lead_id"] == "L999"
    assert data[0]["original_action"] == "DEMO"
