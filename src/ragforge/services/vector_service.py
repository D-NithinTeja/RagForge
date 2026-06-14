from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, List, Optional

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.ragforge.config import settings
from src.ragforge.config.constants import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PERSIST_DIR,
    DEFAULT_DOCSTORE_PATH,
)

logger = logging.getLogger(__name__)


# caches
_vectorstore: Optional[Chroma] = None
_docstore: Optional["SimpleDocStore"] = None


class SimpleDocStore:
    def __init__(self, persist_path: Optional[str] = None) -> None:
        path = persist_path or ":memory:"
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS docstore "
            "(id TEXT PRIMARY KEY, content TEXT NOT NULL)"
        )
        self._conn.commit()

    def mset(self, items: List[tuple]) -> None:
        "Inserts muliple sets"
        rows = [
            (doc_id, content if isinstance(content, str) else str(content))
            for doc_id, content in items
        ]
        self._conn.executemany(
            "INSERT OR REPLACE INTO docstore (id, content) VALUES (?, ?)", rows
        )
        self._conn.commit()

    def mget(self, doc_ids: List[str]) -> List[Optional[Any]]:
        if not doc_ids:
            return []
        placeholders = ",".join("?" * len(doc_ids))
        rows = self._conn.execute(
            f"SELECT id, content FROM docstore WHERE id IN ({placeholders})",
            doc_ids,
        ).fetchall()
        lookup = dict(rows)
        return [lookup.get(doc_id) for doc_id in doc_ids]


def get_vectorstore(persist_directory: str = DEFAULT_CHROMA_PERSIST_DIR) -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        logger.info("Initializing Chroma vector store at %s", persist_directory)
        embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )
    return _vectorstore


def get_docstore(persist_path: str = DEFAULT_DOCSTORE_PATH) -> SimpleDocStore:
    global _docstore
    if _docstore is None:
        logger.info("Initializing document store at %s", persist_path)
        _docstore = SimpleDocStore(persist_path=persist_path)
    return _docstore
