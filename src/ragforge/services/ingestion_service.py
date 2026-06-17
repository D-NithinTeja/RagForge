from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.vectorstores import VectorStoreRetriever

from src.ragforge.config.constants import DEFAULT_MAX_CONCURRENCY
from src.ragforge.services.chunk_service import extract_images_base64, separate_elements
from src.ragforge.services.llm_service import (
    get_image_summarizer,
    get_text_table_summarizer,
)
from src.ragforge.services.retrieval_service import (
    add_documents_to_retriever,
    get_multi_vector_retriever,
)
from src.ragforge.services.unstructured_service import partition_document
from src.ragforge.services.vector_service import (
    SimpleDocStore,
    get_docstore,
    get_vectorstore,
)

logger = logging.getLogger(__name__)


class IngestionResult(TypedDict):
    retriever: VectorStoreRetriever
    docstore: SimpleDocStore
    chunk_count: int
    image_count: int
    table_count: int


def ingest_document_pipeline(
    file_path: str,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    user_id: Optional[str] = None,
    document_id: Optional[str] = None,
) -> IngestionResult:
    logger.info(
        "Initiating top-level document ingestion pipeline workflow for asset: %s",
        file_path,
    )

    # Step 1 & 2: Extract layout elements and categorize by type
    chunks = partition_document(file_path)
    texts, tables = separate_elements(chunks)
    images = extract_images_base64(chunks)

    logger.info(
        "Layout distribution extraction summary - Texts: %d, Tables: %d, Images: %d",
        len(texts),
        len(tables),
        len(images),
    )

    # Get the core text/table summarizer chain configuration
    text_table_summarizer_chain = get_text_table_summarizer()

    # Batch process textual element narrative summaries
    text_summaries: List[str] = []
    if texts:
        logger.info("Executing concurrent text block summarization batch processing...")
        text_summaries = text_table_summarizer_chain.batch(
            [str(t) for t in texts],
            {"max_concurrency": max_concurrency},
        )

    # Batch process layout table formatting summaries
    table_summaries: List[str] = []
    if tables:
        logger.info(
            "Executing concurrent HTML tabular layout summarization batch processing..."
        )
        # Utilize structural HTML table strings for maximum extraction resolution
        tables_html = [table.metadata.text_as_html for table in tables]
        table_summaries = text_table_summarizer_chain.batch(
            tables_html,
            {"max_concurrency": max_concurrency},
        )

    # Batch process multi-modal image block summaries
    image_summaries: List[str] = []
    if images:
        logger.info(
            "Executing multi-modal vision image block summarization batch processing..."
        )
        image_summarizer_chain = get_image_summarizer()
        image_summaries = image_summarizer_chain.batch(
            images,
            {"max_concurrency": max_concurrency},
        )

    # Initialize storage singletons
    vectorstore = get_vectorstore()
    docstore = get_docstore()

    # Acquire our multi-vector retriever configuration
    retriever, id_key = get_multi_vector_retriever(vectorstore, user_id=user_id)

    # Step 4: Synchronize assets into persistent storage
    logger.info(
        "Writing generated summary metrics and physical assets to storage nodes..."
    )
    counts = add_documents_to_retriever(
        vectorstore=vectorstore,
        docstore=docstore,
        texts=texts,
        text_summaries=text_summaries,
        tables=tables,
        table_summaries=table_summaries,
        images=images,
        image_summaries=image_summaries,
        id_key=id_key,
        user_id=user_id,
        document_id=document_id,
    )

    total_chunks = counts["texts"] + counts["tables"] + counts["images"]
    logger.info(
        "Ingestion pipeline execution completed successfully for asset path coordinate: %s",
        file_path,
    )

    return {
        "retriever": retriever,
        "docstore": docstore,
        "chunk_count": total_chunks,
        "image_count": counts["images"],
        "table_count": counts["tables"],
    }
