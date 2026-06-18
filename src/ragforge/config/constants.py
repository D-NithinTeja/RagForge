"""Centralized system parameters and algorithmic values."""

# Vector database persistence tracking
DEFAULT_CHROMA_PERSIST_DIR: str = "./chroma_db"
DEFAULT_DOCSTORE_PATH: str = "./docstore.db"  # Stores the original text.
COLLECTION_NAME: str = "ragforge_summaries"

# Information Retrieval limits
DEFAULT_SEARCH_K: int = 5
DEFAULT_FETCH_K: int = 20
DEFAULT_SEARCH_TYPE: str = "mmr"  # Maximal Marginal Relevance for context diversity
DEFAULT_ID_KEY: str = "doc_id"

# Chat Context windows
MAX_CONTEXT_TOKENS: int = 3000
MAX_HISTORY_EXCHANGES: int = 4  # Track history depth for conversation relevance

# Document Parsing & Chunking boundaries
DEFAULT_PARTITION_STRATEGY: str = "hi_res"
DEFAULT_MAX_CHARACTERS: int = 3000
DEFAULT_COMBINE_UNDER_N_CHARS: int = 500
DEFAULT_NEW_AFTER_N_CHARS: int = 2000  # Soft limit
DEFAULT_IMAGE_TYPES: list[str] = ["Image"]

# Large Language Model Runtime parameters
VISION_MODEL: str = "qwen3-vl:8b"
SUMMARIZATION_TEMPERATURE: float = 0.3  # Deterministic for structural accuracy
QA_TEMPERATURE: float = 0.5  # Slightly balanced creativity for response styling
VISION_TEMPERATURE: float = 0.4
LLM_MAX_RETRIES: int = 1  # Increase it to 3 or more in production
DEFAULT_MAX_CONCURRENCY: int = 1

# File Streaming and IO optimization boundaries
FILE_WRITE_CHUNK_SIZE: int = 1024 * 1024  # 1 MB blocks
MAX_QUESTION_LENGTH: int = 2000  # Input query validation caps
