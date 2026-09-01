"""Vector store abstraction.

The chatbot only ever talks to :class:`VectorStore`. Chroma is the local
default; a Pinecone implementation can be added later (see
``app/vector/pinecone_store.py``) without touching the RAG pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class VectorDocument:
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchHit:
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class VectorStore(ABC):
    name = "abstract"

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def upsert(self, documents: Sequence[VectorDocument], embeddings: Sequence[Sequence[float]]) -> None: ...

    @abstractmethod
    def query(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]: ...

    @abstractmethod
    def count(self) -> int: ...

    def is_empty(self) -> bool:
        return self.count() == 0
