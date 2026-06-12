from __future__ import annotations

import logging
from typing import Any, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

from src.ragforge.config import settings
from src.ragforge.config.constants import (
    LLM_MAX_RETRIES,
    QA_TEMPERATURE,
    SUMMARIZATION_TEMPERATURE,
    VISION_MODEL,
    VISION_TEMPERATURE,
)
from src.ragforge.config.prompts import (
    IMAGE_SUMMARIZATION_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    TEXT_TABLE_SUMMARIZATION_PROMPT,
)

logger = logging.getLogger(__name__)

# cached singleton instances to avoid recreating ChatOllama every time.(lazy initialization.)
_text_llm: Optional[ChatOllama] = None
_qa_llm: Runnable | None = None
_vision_llm: Optional[ChatOllama] = None


def get_text_llm() -> ChatOllama:
    """Return a client configured for text summarization."""
    global _text_llm
    if _text_llm is None:
        _text_llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_HOST,
            temperature=SUMMARIZATION_TEMPERATURE,
        )
    return _text_llm


def get_qa_llm() -> Runnable:
    """Return a ChatOllama client optimized Q&A interactions."""
    global _qa_llm
    if _qa_llm is None:
        _qa_llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_HOST,
            temperature=QA_TEMPERATURE,
        ).with_retry(stop_after_attempt=LLM_MAX_RETRIES)
    return _qa_llm


def _get_vision_llm() -> ChatOllama:
    """Return a ChatOllama multi-modal client targeting vision."""
    global _vision_llm
    if _vision_llm is None:
        _vision_llm = ChatOllama(
            model=VISION_MODEL,
            base_url=settings.OLLAMA_HOST,
            temperature=VISION_TEMPERATURE,
        )
    return _vision_llm


def get_text_table_summarizer() -> Any:
    """Construct an LCEL chain to extract facts from document texts and table objects."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SUMMARIZATION_SYSTEM_PROMPT),
            ("human", TEXT_TABLE_SUMMARIZATION_PROMPT),
        ]
    )
    # The lambda component passes the incoming argument map key onto prompt fields smoothly
    return {"element": lambda x: x} | prompt | get_text_llm() | StrOutputParser()


def get_image_summarizer() -> Any:
    """Construct an LCEL chain to parse images via multi-modal vision inputs."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SUMMARIZATION_SYSTEM_PROMPT),
            (
                "human",
                [
                    {"type": "text", "text": IMAGE_SUMMARIZATION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,{image}"},
                    },
                ],
            ),
        ]
    )
    return prompt | _get_vision_llm() | StrOutputParser()
