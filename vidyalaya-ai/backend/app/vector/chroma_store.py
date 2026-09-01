"""ChromaDB implementation of :class:`VectorStore` (local persistent client)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.vector.base import SearchHit, VectorDocument, VectorStore


class ChromaVectorStore(VectorStore):
    name = "chroma"

    def __init__(self, directory: str, collection: str):
        import chromadb  # imported lazily so the package stays optional
        from chromadb.config import Settings as ChromaSettings

        self._client = chromadb.PersistentClient(
            path=directory, settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collection_name = collection
        self._collection = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )

    def reset(self) -> None:
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, documents: Sequence[VectorDocument], embeddings: Sequence[Sequence[float]]) -> None:
        if not documents:
            return
        self._collection.upsert(
            ids=[document.id for document in documents],
            documents=[document.text for document in documents],
            metadatas=[_clean_metadata(document.metadata) for document in documents],
            embeddings=[list(map(float, embedding)) for embedding in embeddings],
        )

    def query(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]:
        result = self._collection.query(
            query_embeddings=[list(map(float, embedding))],
            n_results=top_k,
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )
        hits: List[SearchHit] = []
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        for index, doc_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else 1.0
            hits.append(
                SearchHit(
                    id=doc_id,
                    text=docs[index] if index < len(docs) else "",
                    metadata=metas[index] if index < len(metas) else {},
                    score=float(1.0 - distance),
                )
            )
        return hits

    def count(self) -> int:
        try:
            return int(self._collection.count())
        except Exception:
            return 0


def _clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Chroma only accepts scalar metadata values."""
    cleaned: Dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned
