from src.ragforge.services.streaming_service import _sanitize_mermaid, _sse


def test_mermaid_syntax_healing_loops():
    malformed_markdown = (
        "Here is the workflow diagram layout:\n"
        "```mermaid\n"
        "flowchart TD\n"
        "id1[Component (With Unsafe Parentheses) Data]\n"
        "id2[Simple plain text description]\n"
        "id1 --> id2\n"
        "```"
    )

    sanitized = _sanitize_mermaid(malformed_markdown)

    # Assert regex logic successfully injected double-quotes around the malformed layout segment
    assert 'id1["Component (With Unsafe Parentheses) Data"]' in sanitized
    assert (
        "id2[Simple plain text description]" in sanitized
    )  # Standard letters stay clean


def test_sse_packet_serialization():
    sample_payload = {"type": "delta", "content": "hello"}
    formatted_sse = _sse(sample_payload)

    assert formatted_sse.startswith("data: ")
    assert formatted_sse.endswith("\n\n")
