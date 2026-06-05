"""Validates database registries."""

from sqlalchemy import Column, Integer, String

from src.ragforge.db.base import Base


class MockModel(Base):
    __tablename__ = "mock_test_registry"

    id = Column(Integer, primary_key=True)
    name = Column(String)


def test_declarative_base_registration():
    assert "mock_test_registry" in Base.metadata.tables
    assert MockModel.__tablename__ == "mock_test_registry"
