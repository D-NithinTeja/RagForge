import io

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from src.ragforge.core.exceptions import FileValidationError
from src.ragforge.services.file_servies import file_service


def test_file_upload_validation_and_streaming_lifecycle():

    # 1. Simulate a clean text stream payload file matching our validation format
    dummy_bytes = b"Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur"
    mock_upload = UploadFile(
        file=io.BytesIO(dummy_bytes),
        filename="testing.txt",
        headers=Headers({"content-type": "text/plain"}),
    )

    # 2. Save the upload and assert a valid UUID handle is generated
    doc_id = file_service.save_upload(mock_upload)
    assert doc_id is not None
    assert len(doc_id) == 36

    # 3. Locate path target
    resolved_path = file_service.get_file_path(doc_id)
    assert resolved_path is not None
    assert resolved_path.exists() is True

    # 4. Clean up and verify path resolution
    delete_result = file_service.delete_file(doc_id)
    assert delete_result is True
    assert resolved_path.exists() is False


def test_file_validation_rejects_unallowed_mimetypes():
    bad_upload = UploadFile(
        file=io.BytesIO(b"Not Virus Code"),
        filename="virus.exe",
        headers=Headers({"content-type": "application/x-msdownload"}),
    )

    with pytest.raises(FileValidationError):
        file_service.save_upload(bad_upload)
