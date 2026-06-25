from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy.orm import Session

from src.ragforge.config.constants import DEFAULT_ID_KEY
from src.ragforge.models.message import MessageRole
from src.ragforge.services.conversation_service import conversation_service
from src.ragforge.services.rag_chain import build_rag_chain
from src.ragforge.services.retrieval_service import get_multi_vector_retriever
from src.ragforge.services.vector_service import get_vectorstore

logger = logging.getLogger(__name__)

# Compile pattern configurations tracking characters hazardous to unquoted Mermaid node labels
_MERMAID_UNSAFE = re.compile(r"[.()\[\]{},:#%<>\\]")

# Static array tracking explicit structural keywords reserved by the Mermaid engine specification
_MERMAID_RESERVED = frozenset(
    {
        "end",
        "subgraph",
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "gantt",
        "pie",
        "gitGraph",
        "mindmap",
        "timeline",
    }
)

# Matches valid diagram framework initialization markers within a text block stream
_DIAGRAM_DECL = re.compile(
    r"^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|gantt|pie|gitGraph|mindmap|timeline)\b",
    re.MULTILINE | re.IGNORECASE,
)


def _heal_mermaid_block(code: str) -> str:
    # 1. Clear any conversational introduction preamble drifting before the true structural tag
    m = _DIAGRAM_DECL.search(code)
    if m:
        code = code[m.start() :]

    # 2. Encapsulate unsafe punctuation matrices inside standard double-quote layouts safely
    def _maybe_quote(match: re.Match, open_b: str, close_b: str) -> str:
        node_id, label = match.group(1), match.group(2)
        if label.startswith('"') and label.endswith('"'):
            return match.group(0)  # Already quoted, leave unmodified

        has_unsafe = bool(_MERMAID_UNSAFE.search(label))
        is_reserved = label.strip().lower() in _MERMAID_RESERVED
        if has_unsafe or is_reserved:
            safe = label.replace('"', "'")  # Escape any internal double quotes safely
            return f'{node_id}{open_b}"{safe}"{close_b}'
        return match.group(0)

    # Sanitize rectangular node boundaries [label]
    code = re.sub(
        r'\b(\w+)\[([^"\]\[]+)\]',
        lambda m: _maybe_quote(m, "[", "]"),
        code,
    )
    # Sanitize rounded node boundaries (label)
    code = re.sub(
        r'\b(\w+)\(([^"\)\(]+)\)',
        lambda m: _maybe_quote(m, "(", ")"),
        code,
    )
    # Sanitize diamond node boundaries {label}
    code = re.sub(
        r'\b(\w+)\{([^"\}\{]+)\}',
        lambda m: _maybe_quote(m, "{", "}"),
        code,
    )
    return code


def _sanitize_mermaid(text: str) -> str:

    def fix_block(m: re.Match) -> str:
        return f"```mermaid\n{_heal_mermaid_block(m.group(1))}```"

    healed = re.sub(r"```mermaid\n(.*?)(?:```|$)", fix_block, text, flags=re.DOTALL)

    # Automatically close any truncated or dangling blocks left behind by unexpected connection timeouts
    last_open = healed.rfind("```mermaid")
    if last_open != -1 and "```" not in healed[last_open + len("```mermaid") :]:
        healed += "\n```"
    return healed


# Step tracking user readability text labels registry
_STEP_LABELS = {
    "resolve_originals": "Resolving original content...",
    "parse_docs": "Parsing document types...",
    "build_prompt": "Building prompt...",
}


def _sse(data: dict) -> str:
    """Format dictionary payloads into spec-compliant Server-Sent Events network strings."""
    return f"data: {json.dumps(data)}\n\n"


def _extract_sources(context: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Convert retrieved multi-vector document context records into fine-grained response references."""
    sources: List[Dict[str, Any]] = []
    for doc in context.get("texts", []):
        metadata = doc.metadata if hasattr(doc, "metadata") else {}
        doc_id = metadata.get(DEFAULT_ID_KEY)
        summary = metadata.get(
            "summary", doc.page_content if hasattr(doc, "page_content") else str(doc)
        )
        original = doc.page_content if hasattr(doc, "page_content") else str(doc)

        sources.append(
            {
                "summary": summary,
                "original": original,
                "type": metadata.get("type", "text"),
                "doc_id": doc_id,
                "image_base64": metadata.get("image_base64"),
            }
        )
    return sources


async def stream_chat_response(
    question: str,
    user_id: str,
    db: Session,
    conversation_id: str,
    doc_ids: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    # Validate multi-tenant workspace isolation rules first
    conversation_service.get_conversation(db, conversation_id, user_id)
    history = conversation_service.get_history(db, conversation_id, user_id)

    # Persist the incoming user message step block directly to our log history
    conversation_service.add_message(
        db, conversation_id, MessageRole.USER, question, user_id
    )

    full_response = ""
    sources: List[Dict[str, Any]] = []

    try:
        vectorstore = get_vectorstore()
        retriever, _ = get_multi_vector_retriever(
            vectorstore, user_id=user_id, doc_ids=doc_ids
        )

        # Assemble the atomic LCEL chain blueprint layout graph dynamically
        chain = build_rag_chain(retriever, question, history)

        # Stream intermediate graph events using standard v2 LangChain event emitters
        async for event in chain.astream_events(question, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_retriever_start":
                yield _sse({"type": "status", "content": "Searching documents..."})
            elif kind == "on_chain_start" and name in _STEP_LABELS:
                yield _sse({"type": "status", "content": _STEP_LABELS[name]})
            elif kind == "on_chat_model_start":
                yield _sse({"type": "status", "content": "Generating response..."})
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]

                # Check for reasoning parameter tokens (e.g., DeepSeek reasoning chains)
                reasoning = chunk.additional_kwargs.get("reasoning_content")
                if reasoning:
                    yield _sse({"type": "thinking", "content": reasoning})

                token = chunk.content
                if token:
                    full_response += token
                    yield _sse({"type": "delta", "content": token})

            elif kind == "on_chain_end" and name == "parse_docs":
                sources = _extract_sources(event["data"]["output"])

    except Exception as e:
        logger.error(
            "Dangling fatal failure inside active streaming loops: %s", e, exc_info=True
        )
        error_msg = str(e)
        yield _sse({"type": "error", "content": error_msg})
        if not full_response:
            full_response = f"Error processing request: {error_msg}"

    # Perform a final cleanup check over accumulated output text streams
    full_response = _sanitize_mermaid(full_response)

    # Group associated multi-modal visual blocks to rehydrate frontend indices cleanly
    images = [
        s["image_base64"]
        for s in sources
        if s.get("type") == "image" and s.get("image_base64")
    ]

    # Save the finalized consolidated AI reply parameters back to our database record
    if full_response:
        conversation_service.add_message(
            db,
            conversation_id,
            MessageRole.ASSISTANT,
            full_response,
            user_id,
            sources=sources,
        )

    # Push the terminal 'complete' signal framing packet down the event pipe
    yield _sse(
        {
            "type": "complete",
            "content": full_response,
            "conversation_id": conversation_id,
            "sources": sources,
            "images": images,
        }
    )
