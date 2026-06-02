"""Environment and configuration settings parser using Pydantic Validation."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Overwriting model_config of BaseSettings to connect with our .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignores extra environment variables not mapped here
    )

    # Application Setup
    APP_NAME: str = "RAGForge"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # Default to True for the active development phase
    LOG_LEVEL: str = "DEBUG"  # Verbose logs during development

    # API Networking
    API_HOST: str = "127.0.0.1"  # Bind to localhost securely during development
    API_PORT: int = 8000

    # Database Architecture
    # Defaults SQLite for developer accessibility.
    # Overwrite this in your production .env with a PostgreSQL string as Python default is ignored
    DATABASE_URL: str = "sqlite:///./ragforge.db"
    DB_POOL_SIZE: int = (
        5  # SQLite handles small pools; override to 20+ for PostgreSQL production
    )
    DB_MAX_OVERFLOW: int = 10

    # LLM Foundations (Defaulting to localized Ollama services)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = (
        "llama3.2:3b"  # For developing; Change to 8b models for production
    )

    # Embeddings Processing
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Ingestion Constraints
    MAX_UPLOAD_SIZE: int = 5
    UPLOAD_DIR: str = "./uploads"

    # API Keys / External Provider Token Handlers
    HUGGING_FACE_HUB_TOKEN: str | None = None

    # CORS Configurations
    CORS_ALLOWED_ORIGINS: list[str] = ["*"]

    # JWT Tokens
    SECRET_KEY: str = "change-this-in-production-environment"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    @property
    def embedding_model_name(self) -> str:
        """Helper to extract model names quickly if full paths are passed."""
        return self.EMBEDDING_MODEL.split("/")[-1]
