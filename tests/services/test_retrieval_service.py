import pytest

from src.ragforge.services.retrieval_service import (
    add_documents_to_retriever,
    get_multi_vector_retriever,
)
from src.ragforge.services.vector_service import get_docstore, get_vectorstore


def test_indexing_synchronization_and_tenant_filtering():
    """Verify that document summaries to vector layers and build search filters."""
    vectorstore = get_vectorstore()
    docstore = get_docstore(persist_path=":memory:")

    user_id = "tenant-customer-abc"
    document_id = "doc-envelope-123"

    # 1. Store text chunk fields into targets
    texts = ["Full text context string tracking financial balance parameters."]
    text_summaries = ["Deterministic brief balance layout overview."]

    counts = add_documents_to_retriever(
        vectorstore=vectorstore,
        docstore=docstore,
        texts=texts,
        text_summaries=text_summaries,
        user_id=user_id,
        document_id=document_id,
    )

    assert counts["texts"] == 1

    # 2. Compile retrieval router filter path
    retriever, id_key = get_multi_vector_retriever(
        vectorstore=vectorstore, user_id=user_id, doc_ids=[document_id]
    )

    # Asset internal dictionary properties evaluate correctly under LangChain's configuration signatures
    assert retriever.search_kwargs["k"] == 5
    assert "filter" in retriever.search_kwargs
    assert "$and" in retriever.search_kwargs["filter"]
