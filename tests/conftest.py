"""Global shared testing configurations and fixtures for pytest."""

import pytest


@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    """Automatically forces configurations into safe testing defaults."""
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
