import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.routes.auth_routes import router as auth_router
from src.ragforge.routes.file_routes import router as file_router
from src.ragforge.routes.process_routes import router as process_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(file_router)
app.include_router(process_router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def run_db_lifecycle():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_file_upload_routing_and_status_polling():
    """Verify that multi-part form data uploads successfully and hooks into the processing routing paths."""
    db = SessionLocal()

    # Generate authorization
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

    # 1. Test multipart file upload route execution
    file_payload = {
        "file": ("manual.txt", b"System instruction index contexts data.", "text/plain")
    }
    response = client.post("/files/upload", files=file_payload, headers=headers)

    assert response.status_code == 201
    file_id = response.json()["file_id"]

    # 2. Test status polling router verification pass
    status_response = client.get(f"/files/status/{file_id}", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "uploaded"

    # Clean up physical test artifacts off local folders
    client.delete(f"/files/delete?file_id={file_id}", headers=headers)
    db.close()
