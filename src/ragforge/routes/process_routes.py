from fastapi import APIRouter, BackgroundTasks, Depends, status

from src.ragforge.dependencies.auth import get_current_user
from src.ragforge.models.user import User
from src.ragforge.schemas.file import ProcessingStatusResponse
from src.ragforge.services.process_service import process_service

router = APIRouter(prefix="/files", tags=["Processing"])


@router.post(
    "/process/{file_id}",
    summary="Process an uploaded file",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target upload index asset not found"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Ingestion job orchestration failed during execution"
        },
    },
)
def process_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    return process_service.process_file_async(
        file_id, background_tasks, user_id=current_user.id
    )


@router.get(
    "/status/{file_id}",
    response_model=ProcessingStatusResponse,
    summary="Get processing status for a file",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authorization token"
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Target tracking reference file absent from workspace registries"
        },
    },
)
def get_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    return process_service.get_status(file_id)
