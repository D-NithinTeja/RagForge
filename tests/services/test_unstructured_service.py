"""Validates structural layout partitioning logic hooks."""

from pathlib import Path

import pytest

from src.ragforge.services.unstructured_service import partition_document


def test_unstructured_text_partitioning_flow():
    sample_path = Path("./tests/services/sample_doc.md")
    sample_content = (
        "# Architectural Foundation\n\n"
        "This is narrative paragraph text confirming system behaviors.\n\n"
        "## Subcomponent Tier\n\n"
        "Secondary tracking text block asserting layout processing thresholds."
    )
    sample_path.write_text(sample_content, encoding="utf-8")

    try:
        chunks = partition_document(str(sample_path), strategy="fast")

        assert len(chunks) > 0
        assert hasattr(chunks[0], "text")
        assert len(chunks[0].text) > 0

    finally:
        if sample_path.exists():
            sample_path.unlink()
