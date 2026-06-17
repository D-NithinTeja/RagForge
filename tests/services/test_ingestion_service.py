from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ragforge.services.ingestion_service import ingest_document_pipeline


@patch("src.ragforge.services.ingestion_service.partition_document")
@patch("src.ragforge.services.ingestion_service.get_text_table_summarizer")
def test_ingestion_pipeline_orchestration_flow(mock_get_summarizer, mock_partition):
    """Verify that the ingestion pipeline coordinates extraction, summarization, and storage parameters correctly."""
    # 1. Setup mock layout element stream
    mock_element = MagicMock()
    mock_element.__class__.__name__ = "CompositeElement"
    mock_element.__str__.return_value = "Mock structural report string text block."
    mock_partition.return_value = [mock_element]

    # 2. Setup mock batch LLM summary chain returns
    mock_chain = MagicMock()
    mock_chain.batch.return_value = ["Brief processed mock summary layout overview."]
    mock_get_summarizer.return_value = mock_chain

    # 3. Execute the orchestrator over a dummy file coordinate handle
    result = ingest_document_pipeline(
        file_path="dummy_report.pdf",
        user_id="mock-user-uuid",
        document_id="mock-doc-uuid",
    )

    # 4. Assert all pipeline tracking parameters align perfectly
    assert result["chunk_count"] == 1
    assert result["image_count"] == 0
    assert result["table_count"] == 0
    assert result["retriever"] is not None
