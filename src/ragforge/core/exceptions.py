"""Custom exception hierarchy for the application."""

from fastapi import status


class AppError(Exception):
    """Base application exception layer."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "An unexpected error has occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class StorageFileNotFoundError(AppError):
    status_code: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Requested file asset could not be located"


class DocumentNotFoundError(AppError):
    status_code: int = status.HTTP_404_NOT_FOUND
    default_message: str = "Document index record not found"


class FileValidationError(AppError):
    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "File validation failed against constraints"


class AuthenticationError(AppError):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    default_message: str = "Authentication validation failed"


class ForbiddenError(AppError):
    status_code: int = status.HTTP_403_FORBIDDEN
    default_message: str = "Access to the requested resource is denied"


class ConflictError(AppError):
    status_code: int = status.HTTP_409_CONFLICT
    default_message: str = "Resource conflict detected within system state"


class VectorStoreError(AppError):
    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    default_message: str = "Vector store operation failed"


class ProcessingError(AppError):
    status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT
    default_message: str = "Document syntax chunking process failed"


class QueryError(AppError):
    status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT
    default_message: str = "Query processing failed"
