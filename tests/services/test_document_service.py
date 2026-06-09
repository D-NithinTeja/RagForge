import uuid

from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.services.document_service import document_service


def test_document_metadata_ledger_operations():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user_uuid = str(uuid.uuid4)

    try:
        # 1. Verify record creation
        doc1 = document_service.create_document(
            db,
            doc_id=str(uuid.uuid4()),
            filename="testing1.md",
            content_type="text/markdown",
            user_id=user_uuid,
            file_size=2048,
        )
        doc2 = document_service.create_document(
            db,
            doc_id=str(uuid.uuid4()),
            filename="testing2.csv",
            content_type="text/csv",
            user_id=user_uuid,
            file_size=4096,
        )

        assert doc1.id is not None
        assert doc2.filename == "testing2.csv"

        # 2. Test pagination
        list_payload = document_service.list_documents(
            db, user_id=user_uuid, page=1, limit=1
        )
        assert list_payload["total"] == 2
        assert len(list_payload["files"]) == 1
        assert list_payload["files"][0]["filename"] == "testing2.csv"  # Ordered desc

        # 3. Test parameter parsing
        fetched_dict = document_service.get_document(
            db, doc_id=doc1.id, user_id=user_uuid
        )
        assert fetched_dict is not None
        assert fetched_dict["file_size"] == 2048

        # 4. Clean up rows
        assert (
            document_service.delete_document(db, doc_id=doc1.id, user_id=user_uuid)
            is True
        )
        assert (
            document_service.get_document(db, doc_id=doc1.id, user_id=user_uuid) is None
        )

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
