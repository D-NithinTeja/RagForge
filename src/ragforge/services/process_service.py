from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.ragforge.core.exceptions import StorageFileNotFoundError
from src.ragforge.db.session import SessionLocal
from src.ragforge.models.document import Document, DocumentStatus
from src.ragforge.services.file_service import file_service
from src.ragforge.services.ingestion_service import ingest_document_pipeline

if TYPE_CHECKING:
    from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class ProcessService:
    def __init__(self) -> None:
        self._status_dir: Path = file_service.upload_dir / "status"
        self._status_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Pipeline status tracking node mounted at: %s", self._status_dir)

    def _status_path(self, file_id: str) -> Path:
        return self._status_dir / f"{file_id}.json"

    def _write_status(
        self,
        file_id: str,
        status_value: DocumentStatus,
        error: Optional[str] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "file_id": file_id,
            "status": status_value.value,
        }

        if error is not None:
            payload["error"] = error

        path = self._status_path(file_id)
        with path.open("w", encoding="utf-8") as f:
            f.write(json.dumps(payload))
        logger.debug(
            "Disk state-machine token updated for %s -> %s", file_id, status_value.value
        )

    def get_status(self, file_id: str) -> Dict[str, Any]:
        path = self._status_path(file_id)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                logger.warning(
                    "Malformed JSON log token discovered for target file: %s", file_id
                )

        # Fallback check to verify if the uploaded file container physically exists on disk
        file_path = file_service.get_file_path(file_id)
        if file_path is None:
            raise StorageFileNotFoundError(
                f"Requested file asset reference absent: '{file_id}'"
            )

        return {
            "file_id": file_id,
            "status": DocumentStatus.UPLOADED.value,
        }

    def _update_document_status(
        self,
        file_id: str,
        status: DocumentStatus,
        error: Optional[str] = None,
        chunk_count: int = 0,
        image_count: Optional[int] = None,
        table_count: Optional[int] = None,
    ) -> None:
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == file_id).first()
            if doc:
                if status == DocumentStatus.PROCESSED:
                    doc.mark_processed(
                        chunk_count=chunk_count,
                        image_count=image_count,
                        table_count=table_count,
                    )
                elif status == DocumentStatus.FAILED:
                    doc.mark_failed(error or "Pipeline terminated unexpectedly")
                elif status == DocumentStatus.PROCESSING:
                    doc.mark_processing()
                else:
                    doc.status = status
                db.commit()
        except Exception:
            logger.exception(
                "Relational database status modification tracking failed for asset: %s",
                file_id,
            )
            db.rollback()
        finally:
            db.close()

    def _run_pipeline(self, file_id: str, file_path: str, user_id: str) -> None:
        """Execute the structural ingestion pipeline inside an un-blocking thread wrapper."""
        logger.info(
            "Background thread worker context starting ingestion run for asset: %s",
            file_id,
        )
        try:
            # Trigger our complete layout extraction, summarization, and vector storage steps
            result = ingest_document_pipeline(
                file_path, user_id=user_id, document_id=file_id
            )

            # Mark lifecycle states complete across tracking registries on success
            self._write_status(file_id, DocumentStatus.PROCESSED)
            self._update_document_status(
                file_id,
                DocumentStatus.PROCESSED,
                chunk_count=result["chunk_count"],
                image_count=result["image_count"],
                table_count=result["table_count"],
            )
            logger.info(
                "Asynchronous ingestion execution thread completed successfully for file: %s",
                file_id,
            )

        except Exception as exc:
            logger.exception(
                "Terminal error encountered inside background ingestion loop for file: %s",
                file_id,
            )
            error_message = str(exc)
            self._write_status(file_id, DocumentStatus.FAILED, error_message)
            self._update_document_status(file_id, DocumentStatus.FAILED, error_message)

    def process_file_async(
        self,
        file_id: str,
        background_tasks: BackgroundTasks,
        user_id: str,
    ) -> Dict[str, Any]:
        """Advance tracking states to processing and append the pipeline task to the async worker queue."""
        file_path = file_service.get_file_path(file_id)
        if file_path is None:
            raise StorageFileNotFoundError(
                f"Target ingestion storage asset file absent: '{file_id}'"
            )

        # Flag processing milestones across registries immediately
        self._write_status(file_id, DocumentStatus.PROCESSING)
        self._update_document_status(file_id, DocumentStatus.PROCESSING)

        # Hand off pipeline execution to FastAPI background worker thread pools
        background_tasks.add_task(self._run_pipeline, file_id, str(file_path), user_id)
        logger.info(
            "Async document processing worker task successfully queued for asset: %s",
            file_id,
        )

        return {
            "file_id": file_id,
            "status": DocumentStatus.PROCESSING.value,
            "message": "Processing started. Poll /files/status/{file_id} for updates.",
        }


# Instantiate centralized orchestration singleton
process_service: ProcessService = ProcessService()
