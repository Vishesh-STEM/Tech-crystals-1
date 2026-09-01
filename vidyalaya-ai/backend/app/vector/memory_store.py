"""Built-in vector store: cosine similarity over a persisted JSON file.

Zero external dependencies - guarantees the RAG pipeline works even when
ChromaDB is not installed.
"""
from __future__ import annotations

import json
import math
import os
import threading
from typing import Any, Dict, List, Optional, Sequence

from app.vector.base import SearchHit, VectorDocument, VectorStore


class InMemoryVectorStore(VectorStore):
    name = "memory"

    def __init__(self, path: str = "./data/vector/memory_store.json"):
        self.path = path
        self._lock = threading.Lock()
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._load()

    # -- persistence -------------------------------------------------------
    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as handle:
                    self._docs = json.load(handle)
            except Exception:
                self._docs = {}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self._docs, handle)
        except Exception:
            pass

    # -- VectorStore -------------------------------------------------------
    def reset(self) -> None:
        with self._lock:
            self._docs = {}
            self._save()

    def upsert(self, documents: Sequence[VectorDocument], embeddings: Sequence[Sequence[float]]) -> None:
        with self._lock:
            for document, embedding in zip(documents, embeddings):
                self._docs[document.id] = {
                    "text": document.text,
                    "metadata": document.metadata,
                    "embedding": [float(x) for x in embedding],
                }
            self._save()

    def query(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]:
        query_vector = list(embedding)
        norm = math.sqrt(sum(v * v for v in query_vector)) or 1.0
        hits: List[SearchHit] = []
        for doc_id, payload in self._docs.items():
            metadata = payload.get("metadata", {})
            if where and any(metadata.get(key) != value for key, value in where.items()):
                continue
            vector = payload.get("embedding") or []
            if len(vector) != len(query_vector):
                continue
            dot = sum(a * b for a, b in zip(query_vector, vector))
            magnitude = math.sqrt(sum(v * v for v in vector)) or 1.0
            hits.append(
                SearchHit(
                    id=doc_id,
                    text=payload.get("text", ""),
                    metadata=metadata,
                    score=float(dot / (norm * magnitude)),
                )
            )
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]

    def count(self) -> int:
        return len(self._docs)
