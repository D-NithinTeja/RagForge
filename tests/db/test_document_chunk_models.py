"""Validates relational document ingestion and chunk metadata database states."""

from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.models.chunk import Chunk, ChunkType
from src.ragforge.models.document import Document, DocumentStatus, DocumentType


def test_document_chunk_relational_lifecycle():
    """Verify that document structures handle child records and cascade constraints."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create a document row
        doc = Document(
            filename="testing.pdf",
            content_type="application/pdf",
            doc_type=Document.get_doc_type("application/pdf"),
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)

        assert doc.status == DocumentStatus.UPLOADED
        assert doc.doc_type == DocumentType.PDF

        # 2. Append multiple chunks to the dynamic relationship list
        chunk1 = Chunk(
            document_id=doc.id, chunk_type=ChunkType.HEADING, position=0, page_number=1
        )
        chunk2 = Chunk(
            document_id=doc.id, chunk_type=ChunkType.TEXT, position=1, page_number=1
        )
        db.add_all([chunk1, chunk2])
        db.commit()

        # Test state updates
        doc.mark_processing()
        db.commit()
        assert doc.status == DocumentStatus.PROCESSING

        # Assert chunks are properly tracked via parent relationship parameters
        assert doc.chunks.count() == 2

        # 3. Test cascade delete functionality: Dropping the doc must clear all chunks
        db.delete(doc)
        db.commit()
        remaining_chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).all()
        assert len(remaining_chunks) == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
