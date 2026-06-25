from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.models.conversation import Conversation
from src.ragforge.models.message import Message, MessageRole


def test_chat_memory_relational_mechanics():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Instantiate parent session
        conv = Conversation()
        db.add(conv)
        db.commit()
        db.refresh(conv)

        # Verify initial state
        assert conv.is_active is True
        assert conv.message_count == 0

        # 2. Add an initial prompt message and verify auto-titling
        user_prompt = "What are the core parameters of the layout ingestion module?"
        conv.set_title_from_first_message(user_prompt)
        conv.update_last_message()

        msg1 = Message(
            conversation_id=conv.id, role=MessageRole.USER, content=user_prompt
        )
        db.add(msg1)
        db.commit()

        assert conv.title == "What are the core parameters of the layout ingesti..."
        assert conv.message_count == 1

        # 3. Add an AI assistant answer
        conv.update_last_message()
        msg2 = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="The layout module parses blocks into text and table types.",
        )
        db.add(msg2)
        db.commit()

        assert conv.messages.count() == 2
        assert msg2.is_assistant is True

        # 4. Verify cascade integrity constraints: Dropping session clears message histories safely
        db.delete(conv)
        db.commit()

        remaining_messages = (
            db.query(Message).filter(Message.conversation_id == conv.id).all()
        )
        assert len(remaining_messages) == 0

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
