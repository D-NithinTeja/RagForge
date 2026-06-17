from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from src.ragforge.config.constants import (
    DEFAULT_FETCH_K,
    DEFAULT_ID_KEY,
    DEFAULT_SEARCH_K,
    DEFAULT_SEARCH_TYPE,
)
from src.ragforge.services.vector_service import SimpleDocStore

logger = logging.getLogger(__name__)


def get_multi_vector_retriever(
    vectorstore: Chroma,
    search_type: str = DEFAULT_SEARCH_TYPE,
    search_k: int = DEFAULT_SEARCH_K,
    user_id: Optional[str] = None,
    doc_ids: Optional[List[str]] = None,
) -> Tuple[VectorStoreRetriever, str]:

    id_key = DEFAULT_ID_KEY
    search_kwargs: Dict[str, Any] = {"k": search_k}

    if search_type == "mmr":
        search_kwargs["fetch_k"] = DEFAULT_FETCH_K
    if user_id and doc_ids:
        search_kwargs["filter"] = {
            "$and": [
                {"user_id": {"$eq": user_id}},
                {"document_id": {"$in": doc_ids}},
            ]
        }
    elif user_id:
        search_kwargs["filter"] = {"user_id": user_id}
    elif doc_ids:
        search_kwargs["filter"] = {"document_id": {"$in": doc_ids}}

    logger.info("Generated retriever query configuration arguments: %s", search_kwargs)

    retriever = vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )
    return retriever, id_key


def add_documents_to_retriever(
    vectorstore: Chroma,
    docstore: SimpleDocStore,
    texts: Optional[List[Any]] = None,
    text_summaries: Optional[List[str]] = None,
    tables: Optional[List[Any]] = None,
    table_summaries: Optional[List[str]] = None,
    images: Optional[List[str]] = None,
    image_summaries: Optional[List[str]] = None,
    id_key: str = DEFAULT_ID_KEY,
    user_id: Optional[str] = None,
    document_id: Optional[str] = None,
) -> Dict[str, int]:

    counts = {"texts": 0, "tables": 0, "images": 0}
    base_meta: Dict[str, Any] = {}
    if user_id:
        base_meta["user_id"] = user_id
    if document_id:
        base_meta["document_id"] = document_id

    # 1. Process narrative textual chunks
    if texts and text_summaries:
        if len(texts) != len(text_summaries):
            raise ValueError(
                f"Texts array and summary collections count mismatch: {len(texts)} vs {len(text_summaries)}"
            )

        text_ids = [str(uuid.uuid4()) for _ in texts]
        summary_docs = [
            Document(
                page_content=summary,
                metadata={id_key: text_ids[i], "type": "text", **base_meta},
            )
            for i, summary in enumerate(text_summaries)
        ]
        vectorstore.add_documents(summary_docs)
        docstore.mset(list(zip(text_ids, [str(t) for t in texts])))
        counts["texts"] = len(texts)
        logger.info("Added %d text chunk vectors to database index", len(texts))

    # 2. Process tabular data elements
    if tables and table_summaries:
        if len(tables) != len(table_summaries):
            raise ValueError(
                f"Tables collection mismatch against summary parameters: {len(tables)} vs {len(table_summaries)}"
            )

        table_ids = [str(uuid.uuid4()) for _ in tables]
        summary_docs = [
            Document(
                page_content=summary,
                metadata={id_key: table_ids[i], "type": "table", **base_meta},
            )
            for i, summary in enumerate(table_summaries)
        ]
        vectorstore.add_documents(summary_docs)

        # Pull HTML formatting parameters if present from unstructured entities
        table_contents = [
            t.metadata.text_as_html
            if hasattr(t, "metadata") and getattr(t.metadata, "text_as_html", None)
            else str(t)
            for t in tables
        ]
        docstore.mset(list(zip(table_ids, table_contents)))
        counts["tables"] = len(tables)
        logger.info("Added %d structured data tables to database index", len(tables))

    # 3. Process multi-modal image structures
    if images and image_summaries:
        if len(images) != len(image_summaries):
            raise ValueError(
                f"Images count maps unevenly onto summaries configurations: {len(images)} vs {len(image_summaries)}"
            )

        img_ids = [str(uuid.uuid4()) for _ in images]
        summary_docs = [
            Document(
                page_content=summary,
                metadata={id_key: img_ids[i], "type": "image", **base_meta},
            )
            for i, summary in enumerate(image_summaries)
        ]
        vectorstore.add_documents(summary_docs)

        # Package image metrics inside structured JSON envelopes to hold both summary and base64 strings
        img_entries = [
            json.dumps(
                {
                    "base64": f"data:image/jpeg;base64,{img}",
                    "summary": image_summaries[i],
                }
            )
            for i, img in enumerate(images)
        ]
        docstore.mset(list(zip(img_ids, img_entries)))
        counts["images"] = len(images)
        logger.info("Added %d image layout contexts to database index", len(images))

    return counts
