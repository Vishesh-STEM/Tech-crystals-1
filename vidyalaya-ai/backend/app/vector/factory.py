"""Vector-store factory: chroma (default) -> memory fallback -> pinecone."""
from __future__ import annotations

import logging
import threading
from typing import Optional

from app.core.config import settings
from app.vector.base import VectorStore
from app.vector.memory_store import InMemoryVectorStore

logger = logging.getLogger(__name__)
_store: Optional[VectorStore] = None
_lock = threading.Lock()
_backend_detail = "not initialised"


def build_vector_store() -> VectorStore:
    global _backend_detail
    backend = (settings.VECTOR_BACKEND or "chroma").lower()

    if backend == "pinecone" and settings.PINECONE_API_KEY:
        try:
            from app.vector.pinecone_store import PineconeVectorStore

            store = PineconeVectorStore(
                settings.PINECONE_API_KEY, settings.PINECONE_INDEX, settings.EMBEDDING_DIM
            )
            _backend_detail = "pinecone"
            return store
        except Exception as exc:  # pragma: no cover
            logger.warning("Pinecone unavailable (%s); falling back to Chroma/memory.", exc)

    if backend in ("chroma", "pinecone"):
        try:
            from app.vector.chroma_store import ChromaVectorStore

            store = ChromaVectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)
            _backend_detail = "chroma (local persistent client)"
            return store
        except Exception as exc:
            logger.info("ChromaDB not available (%s); using the built-in vector store.", exc)

    _backend_detail = "built-in numpy/JSON store"
    return InMemoryVectorStore()


def get_vector_store() -> VectorStore:
    global _store
    with _lock:
        if _store is None:
            _store = build_vector_store()
        return _store


def reset_vector_store() -> None:
    global _store
    with _lock:
        _store = None


def backend_detail() -> str:
    return _backend_detail
