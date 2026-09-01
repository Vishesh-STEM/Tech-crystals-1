"""Pinecone implementation stub.

Everything the chatbot needs is already behind :class:`VectorStore`, so moving
to Pinecone later is: ``pip install pinecone``, set ``VECTOR_BACKEND=pinecone``
plus ``PINECONE_API_KEY`` / ``PINECONE_INDEX`` and fill in the four methods
below. No RAG or API code changes are required.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from app.vector.base import SearchHit, VectorDocument, VectorStore


class PineconeVectorStore(VectorStore):  # pragma: no cover - not used in the MVP
    name = "pinecone"

    def __init__(self, api_key: str, index_name: str, dimension: int, namespace: str = "content"):
        from pinecone import Pinecone, ServerlessSpec  # type: ignore

        self._client = Pinecone(api_key=api_key)
        self._namespace = namespace
        existing = [index["name"] for index in self._client.list_indexes()]
        if index_name not in existing:
            self._client.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        self._index = self._client.Index(index_name)

    def reset(self) -> None:
        self._index.delete(delete_all=True, namespace=self._namespace)

    def upsert(self, documents: Sequence[VectorDocument], embeddings: Sequence[Sequence[float]]) -> None:
        vectors = [
            {
                "id": document.id,
                "values": list(map(float, embedding)),
                "metadata": {**document.metadata, "text": document.text[:4000]},
            }
            for document, embedding in zip(documents, embeddings)
        ]
        for start in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[start : start + 100], namespace=self._namespace)

    def query(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]:
        response = self._index.query(
            vector=list(map(float, embedding)),
            top_k=top_k,
            include_metadata=True,
            filter=where or None,
            namespace=self._namespace,
        )
        hits: List[SearchHit] = []
        for match in response.get("matches", []):
            metadata = dict(match.get("metadata") or {})
            hits.append(
                SearchHit(
                    id=match["id"],
                    text=metadata.pop("text", ""),
                    metadata=metadata,
                    score=float(match.get("score", 0.0)),
                )
            )
        return hits

    def count(self) -> int:
        try:
            stats = self._index.describe_index_stats()
            return int(stats.get("total_vector_count", 0))
        except Exception:
            return 0
