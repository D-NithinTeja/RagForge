import pytest

from src.ragforge.config import settings
from src.ragforge.core.exceptions import FileValidationError, StorageFileNotFound


def test_application_settings_load():
    assert settings.APP_NAME == "RAGForge"
    assert settings.DEBUG is True


def test_custom_exception_status_mapping():
    with pytest.raises(StorageFileNotFound) as e:
        raise StorageFileNotFound("Assets Not Found")

    assert e.value.status_code == 404
    assert "Assets Not Found" in str(e.value)

    with pytest.raises(FileValidationError) as e:
        raise FileValidationError()
    assert e.value.status_code == 400
