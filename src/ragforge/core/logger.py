"""Logging setup and management utilities."""

import logging

from ragforge.config import settings


def setup_logging() -> None:
    """Configure structured logging topology for the RAGForge application framework."""

    # Defined a scannable format containing tracking indicators
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Resolves the severity dynamically using settings
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Enforce basic configuration to intercept root terminal emission streams
    logging.basicConfig(format=log_format, level=level, force=True)

    # Restrict verbose noise levels from core pipeline
    noisy_loggers = ("httpx", "chromadb", "unstructured", "httpcore")
    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.WARNING)
