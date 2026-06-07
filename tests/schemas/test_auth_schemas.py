import pytest
from pydantic import ValidationError

from src.ragforge.schemas.auth import RegisterRequest


def test_register_request_valid_data():
    payload = {
        "email": "dev@example.com",
        "password": "a_secure_password",
        "full_name": "Yona",
    }

    request = RegisterRequest(**payload)
    assert request.email == "dev@example.com"


def test_register_request_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(email="wrong-format", password="a_secure_password")


def test_register_request_password_too_short():
    with pytest.raises(ValidationError):
        RegisterRequest(email="dev@example.com", password="short")
