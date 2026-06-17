import os

from src.ragforge.services.vector_service import get_docstore


def test_docstore_initialization():
    test_db = "./test_docstore.db"

    docstore = get_docstore(persist_path=test_db)

    # Verify write and read
    docstore.mset([("test_id", "test_content")])
    result = docstore.mget(["test_id"])

    assert result == ["test_content"]

    if os.path.exists(test_db):
        os.remove(test_db)
