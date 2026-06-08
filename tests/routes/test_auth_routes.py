import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.ragforge.db.base import Base
from src.ragforge.db.session import engine
from src.ragforge.routes.auth_routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def manage_test_db():
    """Ensure database state maps cleanly for every execution turn."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_and_login_api_flow():
    """Verify registration profiles create entries and return credentials."""

    # 1. Test registration route handler execution
    reg_payload = {
        "email": "dev@example.com",
        "password": "password123",
        "full_name": "Yona",
    }

    reg_response = client.post("/auth/register", json=reg_payload)
    assert reg_response.status_code == status.HTTP_201_CREATED
    assert reg_response.json()["email"] == "dev@example.com"

    # 2. Test login token extraction
    login_form_data = {
        "username": "dev@example.com",
        "password": "password123",
    }

    login_response = client.post("/auth/login", data=login_form_data)
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    assert "access_token" in token_data

    # 3. Test profile checking with authentication header
    token = token_data["access_token"]
    header = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/auth/me", headers=header)
    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json()["full_name"] == "Yona"
