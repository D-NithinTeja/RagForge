from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.models.message import MessageRole
from src.ragforge.services.conversation_service import conversation_service


def test_conversation_service_turn_management():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user_uuid = "usr-owner-789"

    try:
        # 1. Verify workspace creation tracking records
        conv = conversation_service.create_conversation(db, user_id=user_uuid)
        assert conv.id is not None

        # 2. Add message turn blocks and verify parameter cascades
        msg = conversation_service.add_message(
            db,
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="Extract points regarding pipeline scalability options.",
            user_id=user_uuid,
        )

        assert msg.id is not None
        assert conv.title.startswith("Extract points")

        # 3. Assert format conversions build compliant dictionary sets for LangChain loops
        history = conversation_service.get_history(
            db, conversation_id=conv.id, user_id=user_uuid
        )
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert "scalability" in history[0]["content"]

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
