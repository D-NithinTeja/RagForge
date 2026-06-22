import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ragforge.db.base import Base
from src.ragforge.db.session import engine
from src.ragforge.routes.auth_routes import router as auth_router
from src.ragforge.routes.conversation_routes import router as conversation_router
from src.ragforge.services.auth_service import create_access_token

app = FastAPI()
app.include_router(conversation_router)
app.include_router(auth_router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def db_lifecycle():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_and_list_conversations_api_gateways():
    register = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Yona",
        },
    )

    assert register.status_code == 201

    response = client.post(
        "/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test creation endpoint
    create_res = client.post(
        "/conversations", json={"title": "Scalability Talk"}, headers=headers
    )
    assert create_res.status_code == 201
    assert "id" in create_res.json()
    assert create_res.json()["title"] == "Scalability Talk"

    # 2. Test active listing endpoints
    list_res = client.get("/conversations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
