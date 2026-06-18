import io

from fastapi import BackgroundTasks, UploadFile
from starlette.datastructures import Headers

from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.models.document import DocumentStatus
from src.ragforge.services.document_service import document_service
from src.ragforge.services.file_service import file_service
from src.ragforge.services.process_service import process_service


def test_async_processing_state_machine_flow():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Store dummy physical file container asset
    mock_file = UploadFile(
        file=io.BytesIO(b"Report data block"),
        filename="annual_review.txt",
        headers=Headers({"content-type": "text/plain"}),
    )
    file_uuid = file_service.save_upload(mock_file)

    # 2. Register metadata inventory tracking entry row
    doc = document_service.create_document(
        db,
        doc_id=file_uuid,
        filename="annual_review.txt",
        content_type="text/plain",
        user_id="user-123",
    )
    db.close()

    # Instantiate mock background task execution collector frame
    bg_tasks = BackgroundTasks()

    try:
        # 3. Trigger asynchronous background orchestration handoff
        response = process_service.process_file_async(
            file_id=file_uuid, background_tasks=bg_tasks, user_id="user-123"
        )

        assert response["status"] == DocumentStatus.PROCESSING.value
        assert (
            len(bg_tasks.tasks) == 1
        )  # Verify that the worker operation has been queued

        # 4. Check disk tracking state updates
        status_check = process_service.get_status(file_uuid)
        assert status_check["status"] == DocumentStatus.PROCESSING.value

    finally:
        file_service.delete_file(file_uuid)
        # Safely remove local generated JSON trace artifact file
        trace_path = process_service._status_path(file_uuid)
        if trace_path.exists():
            trace_path.unlink()
        Base.metadata.drop_all(bind=engine)
