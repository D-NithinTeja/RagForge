from src.ragforge.main import app


def test_main_application_unrolled_endpoints():
    openapi_schema = app.openapi()
    unrolled_paths = openapi_schema.get("paths", {}).keys()

    assert "/files" in unrolled_paths, (
        f"File index directory route missing. Found paths: {unrolled_paths}"
    )
    assert "/files/upload" in unrolled_paths, (
        "Document ingestion upload target endpoint route missing"
    )
    assert "/files/status/{file_id}" in unrolled_paths, (
        "Background pipeline status handle polling route missing"
    )
    assert "/conversations" in unrolled_paths, (
        "Session listing collection path directory route missing"
    )
    assert "/conversations/{conversation_id}/ask" in unrolled_paths, (
        "Real-time question streaming route missing"
    )
    assert "/" in unrolled_paths
