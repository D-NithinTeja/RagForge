import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.ragforge.core.exceptions import AppError
from src.ragforge.dependencies.auth import get_current_user
from src.ragforge.dependencies.db import get_db
from src.ragforge.models.user import User
from src.ragforge.schemas.file import (
    FileDeleteResponse,
    FileItem,
    FileListResponse,
    FileUploadResponse,
    MultiFileUploadResponse,
)
from src.ragforge.services.document_service import document_service
from src.ragforge.services.file_service import file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


@router.get(
    "",
    response_model=FileListResponse,
    summary="List all uploaded files",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        }
    },
)
def list_files(
    page: Optional[int] = Query(None, ge=1, description="Page number index (1-based)"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, descriptions="Items per page sizing threshold"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return document_service.list_documents(db, current_user.id, page, limit)


@router.get(
    "/{file_id}",
    response_model=FileItem,
    summary="Get a single file by id",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Requested file tracking index asset not found"
        },
    },
)
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = document_service.get_document(db, file_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="File index entry not found")
    return doc


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single file",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "File format type or sizing parameter validation failed"
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        },
    },
)
def upload_file(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    file_id = file_service.save_upload(file)
    file_path = file_service.get_file_path(file_id)

    document_service.create_document(
        db,
        file_id,
        file.filename or "unnamed_upload",
        content_type=file.content_type or "application/octet-stream",
        user_id=current_user.id,
        file_path=str(file_path) if file_path else None,
        file_size=file_path.stat().st_size if file_path else None,
    )

    logger.info(
        "Singular upload transaction captured and tracked successfully: %s", file_id
    )
    return {"message": "File uploaded successfully", "file_id": file_id}


@router.post(
    "/upload/multiple",
    response_model=MultiFileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        }
    },
)
def upload_multiple_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results: List[Dict[str, Any]] = []

    for file in files:
        try:
            file_id = file_service.save_upload(file)
            file_path = file_service.get_file_path(file_id)
            document_service.create_document(
                db=db,
                doc_id=file_id,
                filename=file.filename or "unnamed_uploads",
                content_type=file.content_type or "application/octet-stream",
                user_id=current_user.id,
                file_path=str(file_path) if file_path else None,
                file_size=file_path.stat().st_size if file_path else None,
            )

            results.append({"file_id": file_id})
        except AppError as e:
            logger.warning(
                "Independent asset batch item upload failed for %s: %s",
                file.filename,
                e.message,
            )
            results.append(
                {"file": file.filename or "unnamed_upload", "error": e.message}
            )

    return {
        "message": "Multiple file batch upload operation completed",
        "files": results,
    }


@router.delete(
    "/delete",
    response_model=FileDeleteResponse,
    summary="Delete a file by id",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target file tracking asset not found"
        },
    },
)
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unlink physical storage blocks from systems folders and drop metadata trackers atomically."""
    file_service.delete_file(file_id)
    document_service.delete_document(db, doc_id=file_id, user_id=current_user.id)
    return {"message": "File deletion attempted successfully", "file_id": file_id}
