from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.models.user import User


def test_user_table_generation():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        new_user = User(
            email="dev@example.com",
            hashed_password="a_hashed_string",
            full_name="Yona",
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        assert new_user.id is not None
        assert len(new_user.id) == 36
        assert new_user.created_at is not None
        assert new_user.is_active is True

    finally:
        db.close()

        Base.metadata.drop_all(bind=engine)
