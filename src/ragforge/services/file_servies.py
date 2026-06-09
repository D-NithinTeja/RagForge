from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from src.ragforge.config import settings
from src.ragforge.config.constants import FILE_WRITE_CHUNK_SIZE
from src.ragforge.config.file_types import ALLOWED_CONTENT_TYPES
from src.ragforge.core.exceptions import FileValidationError

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self) -> None:
        upload_root = settings.UPLOAD_DIR
        self.upload_dir: Path = Path(upload_root)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Physical file storage layer mounted at: %s", self.upload_dir)

    def save_upload(self, file: UploadFile) -> str:
        self._validate_file(file)

        doc_id = str(uuid.uuid4())

        # Safely resolve extension markers
        ext = Path(file.filename).suffix if file.filename else ""
        if not ext:
            ext = mimetypes.guess_extension(file.content_type) or ".bin"

        filename = f"{doc_id}{ext}"
        file_path = self.upload_dir / filename

        try:
            bytes_written = 0
            with file_path.open("wb") as buffer:
                while chunk := file.file.read(FILE_WRITE_CHUNK_SIZE):
                    buffer.write(chunk)
                    bytes_written += len(chunk)

            logger.info(
                "File saved successfully to storage node: %s (%d bytes)",
                file_path,
                bytes_written,
            )
            return doc_id

        except Exception as e:
            logger.exception(
                "Disk write operation encountered a terminal failure for %s", file_path
            )
            if file_path.exists():
                file_path.unlink()  # Remove orphan files to prevent storage leak
            raise FileValidationError(
                "File storage execution could not complete"
            ) from e

    def delete_file(self, doc_id: str) -> bool:
        try:
            matched_files = list(self.upload_dir.glob(f"{doc_id}*"))
            if not matched_files:
                logger.warning(
                    "No storage asset matched requested doc_id criteria: %s", doc_id
                )
                return False

            for file_path in matched_files:
                file_path.unlink()
                logger.info("Successfully unlinked storage target file: %s", file_path)

            return True
        except Exception:
            logger.exception(
                "Storage file deletion failed for doc_id string parameter: %s", doc_id
            )
            return False

    def get_file_path(self, doc_id: str) -> Optional[Path]:
        matched_files = list(self.upload_dir.glob(f"{doc_id}*"))
        if not matched_files:
            return None
        return matched_files[0]

    def _validate_file(self, file: UploadFile) -> None:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise FileValidationError(
                f"MIME Content type alignment [{file.content_type}] is restricted"
            )

        # Read binary length safely without unrolling the entire stream allocation into memory
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Always rewind stream pointer back to start

        max_size_mb = settings.MAX_UPLOAD_SIZE

        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            raise FileValidationError(
                f"File sizing parameters break standard restriction limits. Cap: {max_size_mb} MB"
            )


# Instantiate centralized singleton instance for cross service processing integration
file_service: FileService = FileService()
