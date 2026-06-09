"""Document metadata service layer."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.ragforge.models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentService:
    def create_document(
        self,
        db: Session,
        doc_id: str,
        filename: str,
        content_type: str,
        user_id: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> Document:
        doc = Document(
            id=doc_id,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            doc_type=Document.get_doc_type(content_type),
            file_path=file_path,
            file_size=file_size,
            status=DocumentStatus.UPLOADED,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(
            "Successfully provisioned document tracking record: %s for user context: %s",
            doc_id,
            user_id,
        )
        return doc

    def list_documents(
        self,
        db: Session,
        user_id: str,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        query = (
            db.query(Document)
            .filter(
                Document.user_id == user_id,
                Document.status != DocumentStatus.DELETED,
            )
            .order_by(Document.created_at.desc())
        )

        total = query.count()

        if page is not None and limit is not None:
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
        else:
            page = 1
            limit = total

        documents = query.all()

        return {
            "files": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "created_at": doc.created_at.isoformat(),
                    "type": doc.doc_type.value,
                    "file_size": doc.file_size,
                    "page_count": doc.page_count,
                    "chunk_count": doc.chunk_count,
                    "image_count": doc.image_count,
                    "table_count": doc.table_count,
                }
                for doc in documents
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    def get_document(self, db: Session, doc_id: str, user_id: str) -> Optional[dict]:
        doc = (
            db.query(Document)
            .filter(
                Document.id == doc_id,
                Document.user_id == user_id,
                Document.status != DocumentStatus.DELETED,
            )
            .first()
        )
        if not doc:
            return None

        return {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status.value,
            "created_at": doc.created_at.isoformat(),
            "type": doc.doc_type.value,
            "file_size": doc.file_size,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "image_count": doc.image_count,
            "table_count": doc.table_count,
        }

    def delete_document(self, db: Session, doc_id: str, user_id: str) -> bool:
        doc = (
            db.query(Document)
            .filter(Document.id == doc_id, Document.user_id == user_id)
            .first()
        )
        if not doc:
            return False

        db.delete(doc)
        db.commit()
        logger.info(
            "Successfully dropped document inventory metadata reference: %s for user: %s",
            doc_id,
            user_id,
        )
        return True


document_service: DocumentService = DocumentService()
