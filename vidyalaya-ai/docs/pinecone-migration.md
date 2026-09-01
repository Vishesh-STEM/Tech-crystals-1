# Pinecone migration plan

ChromaDB (local, free) is the default vector store. The chatbot only ever talks
to the abstract `VectorStore`:

```python
class VectorStore(ABC):
    def reset(self) -> None: ...
    def upsert(self, documents, embeddings) -> None: ...
    def query(self, embedding, top_k=5, where=None) -> list[SearchHit]: ...
    def count(self) -> int: ...
```

Implementations live side by side:

| File | Backend | Notes |
| --- | --- | --- |
| `vector/chroma_store.py` | ChromaDB | default when the package is installed |
| `vector/memory_store.py` | built-in | numpy/JSON cosine store, always available |
| `vector/pinecone_store.py` | Pinecone | implemented against the Pinecone SDK |

`vector/factory.py` picks one from `VECTOR_BACKEND` and degrades gracefully
(pinecone → chroma → memory) if a dependency or key is missing.

## Migration

```bash
pip install pinecone
# .env
VECTOR_BACKEND=pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX=vidyalaya-ai
EMBEDDING_DIM=256          # must match the index dimension
```

Then rebuild the index once:

```bash
curl -X POST localhost:8000/api/admin/reindex -H "Authorization: Bearer $TEACHER_TOKEN"
# or
cd backend && python -m app.seed.seed --index
```

`PineconeVectorStore` creates the index (serverless, cosine) if it does not
exist, upserts in batches of 100 with the passage text in metadata, and returns
the same `SearchHit` objects the RAG pipeline already consumes.

## Things to keep in mind

- **Dimension must match the embedder.** `local` (TF-IDF+SVD) uses
  `EMBEDDING_DIM` (256 by default); `sentence-transformers/all-MiniLM-L6-v2`
  produces 384. Recreate the index if you switch embedders.
- **The TF-IDF embedder is fitted on your corpus**, so re-index after large
  content edits (the admin "Rebuild AI index" button does exactly that).
- Namespaces are supported (`namespace="content"`); use one per environment.
- Nothing else changes: no RAG, API, UI or database changes are required.
