from __future__ import annotations

import logging
from typing import List, Tuple

from unstructured.documents.elements import Element

logger = logging.getLogger(__name__)


def _element_type(el: Element) -> str:
    return type(el).__name__


def _extract_base64(el: Element) -> str | None:
    meta = getattr(el, "metadata", None)
    return getattr(meta, "image_base64", None) if meta else None


def separate_elements(chunks: List[Element]) -> Tuple[List[Element], List[Element]]:
    texts: List[Element] = []
    tables: List[Element] = []

    for chunk in chunks:
        name = _element_type(chunk)

        if name in ("Table", "TableChunk"):
            tables.append(chunk)
        elif name == "CompositeElement":
            texts.append(chunk)

            # Extract nested tables from the original un-chunked elements list
            orig = getattr(getattr(chunk, "metadata", None), "orig_elements", None)
            if orig:
                for el in orig:
                    if _element_type(el) in ("Table", "TableChunk"):
                        tables.append(el)

    logger.debug(
        "Separated %d composite items into %d text components and %d tabular units",
        len(chunks),
        len(texts),
        len(tables),
    )

    return texts, tables


def extract_images_base64(chunks: List[Element]) -> List[str]:
    images_b64: List[str] = []

    for chunk in chunks:
        name = _element_type(chunk)

        if name == "Image":
            b64 = _extract_base64(chunk)
            if b64:
                images_b64.append(b64)
            continue

        if name == "CompositeElement":
            orig = getattr(getattr(chunk, "metadata", None), "orig_elements", None)
            if not orig:
                continue
            for el in orig:
                if _element_type(el) == "Image":
                    b64 = _extract_base64(el)
                    if b64:
                        images_b64.append(b64)

    logger.debug(
        "Extracted %d base64-encoded image assets from layout streams", len(images_b64)
    )
    return images_b64
