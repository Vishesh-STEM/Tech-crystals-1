"""Tests for all three VectorStore implementations and the factory.

    python -m tests.test_vector_stores
    pytest tests/test_vector_stores.py

ChromaDB and Pinecone are optional dependencies, so this suite installs tiny
stub modules that record what the adapters send and replay canned responses.
That exercises the real adapter code (argument shapes, metadata cleaning,
distance-to-score conversion, batching, index creation) on any machine, and the
same tests pass unchanged against the genuine packages when they are installed.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import types

from app.core.config import settings
from app.vector import factory
from app.vector.base import SearchHit, VectorDocument, VectorStore
from app.vector.memory_store import InMemoryVectorStore

state: dict = {}
DOCUMENTS = [
    VectorDocument(id="topic-1", text="Ohm's law relates current and voltage",
                   metadata={"subject_id": 1, "topic": "Ohm's law", "tags": ["a", "b"], "none": None}),
    VectorDocument(id="topic-2", text="Integration by parts uses ILATE",
                   metadata={"subject_id": 2, "topic": "Integrals"}),
]
EMBEDDINGS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


# --------------------------------------------------------------------------
# stub packages
# --------------------------------------------------------------------------
class _StubCollection:
    def __init__(self, name):
        self.name = name
        self.records: dict = {}
        self.queries: list = []

    def upsert(self, ids, documents, metadatas, embeddings):
        for index, doc_id in enumerate(ids):
            self.records[doc_id] = {
                "text": documents[index],
                "metadata": metadatas[index],
                "embedding": embeddings[index],
            }

    def query(self, query_embeddings, n_results, where=None, include=None):
        self.queries.append({"where": where, "n_results": n_results, "include": include})
        items = [
            (doc_id, record)
            for doc_id, record in self.records.items()
            if not where or all(record["metadata"].get(k) == v for k, v in where.items())
        ][:n_results]
        return {
            "ids": [[doc_id for doc_id, _ in items]],
            "documents": [[record["text"] for _, record in items]],
            "metadatas": [[record["metadata"] for _, record in items]],
            "distances": [[0.25 for _ in items]],
        }

    def count(self):
        return len(self.records)


def install_chroma_stub() -> types.ModuleType:
    module = types.ModuleType("chromadb")
    config_module = types.ModuleType("chromadb.config")

    class Settings:  # noqa: D401 - mirrors chromadb.config.Settings
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class PersistentClient:
        instances: list = []

        def __init__(self, path, settings=None):
            self.path = path
            self.settings = settings
            self.collections: dict = {}
            PersistentClient.instances.append(self)
            os.makedirs(path, exist_ok=True)

        def get_or_create_collection(self, name, metadata=None):
            return self.collections.setdefault(name, _StubCollection(name))

        def delete_collection(self, name):
            self.collections.pop(name, None)

    config_module.Settings = Settings
    module.PersistentClient = PersistentClient
    module.config = config_module
    sys.modules["chromadb"] = module
    sys.modules["chromadb.config"] = config_module
    return module


class _StubIndex:
    def __init__(self):
        self.vectors: dict = {}
        self.upsert_calls: list = []
        self.deleted = False

    def upsert(self, vectors, namespace=None):
        self.upsert_calls.append(len(vectors))
        for vector in vectors:
            self.vectors[vector["id"]] = vector

    def query(self, vector, top_k, include_metadata, filter=None, namespace=None):
        matches = []
        for stored in list(self.vectors.values())[:top_k]:
            metadata = dict(stored["metadata"])
            if filter and any(metadata.get(k) != v for k, v in filter.items()):
                continue
            matches.append({"id": stored["id"], "score": 0.75, "metadata": metadata})
        return {"matches": matches}

    def describe_index_stats(self):
        return {"total_vector_count": len(self.vectors)}

    def delete(self, delete_all=False, namespace=None):
        self.deleted = True
        self.vectors.clear()


def install_pinecone_stub(existing_index: bool = False) -> types.ModuleType:
    module = types.ModuleType("pinecone")

    class ServerlessSpec:
        def __init__(self, cloud, region):
            self.cloud, self.region = cloud, region

    class Pinecone:
        created: list = []

        def __init__(self, api_key):
            self.api_key = api_key
            self._index = _StubIndex()
            self._names = ["vidyalaya-ai"] if existing_index else []

        def list_indexes(self):
            return [{"name": name} for name in self._names]

        def create_index(self, name, dimension, metric, spec):
            Pinecone.created.append({"name": name, "dimension": dimension, "metric": metric})
            self._names.append(name)

        def Index(self, name):  # noqa: N802 - mirrors the SDK
            return self._index

    module.Pinecone = Pinecone
    module.ServerlessSpec = ServerlessSpec
    sys.modules["pinecone"] = module
    return module


# --------------------------------------------------------------------------
# 1. built-in store
# --------------------------------------------------------------------------
def test_01_memory_store_round_trip():
    directory = tempfile.mkdtemp()
    path = os.path.join(directory, "store.json")
    store = InMemoryVectorStore(path)
    assert store.is_empty()

    store.upsert(DOCUMENTS, EMBEDDINGS)
    assert store.count() == 2

    hits = store.query([0.9, 0.1, 0.0], top_k=2)
    assert [hit.id for hit in hits] == ["topic-1", "topic-2"], "cosine ranking is wrong"
    assert hits[0].score > hits[1].score
    assert hits[0].text.startswith("Ohm")
    assert hits[0].metadata["topic"] == "Ohm's law"

    filtered = store.query([0.0, 1.0, 0.0], top_k=5, where={"subject_id": 2})
    assert [hit.id for hit in filtered] == ["topic-2"], "metadata filter ignored"

    # persistence across instances
    reopened = InMemoryVectorStore(path)
    assert reopened.count() == 2
    assert reopened.query([1.0, 0.0, 0.0], top_k=1)[0].id == "topic-1"

    # a mismatched embedding size must be skipped, not crash
    assert reopened.query([1.0, 0.0], top_k=2) == []

    reopened.reset()
    assert reopened.count() == 0 and InMemoryVectorStore(path).count() == 0
    shutil.rmtree(directory, ignore_errors=True)


# --------------------------------------------------------------------------
# 2. Chroma adapter
# --------------------------------------------------------------------------
def test_02_chroma_adapter():
    install_chroma_stub()
    from app.vector.chroma_store import ChromaVectorStore

    directory = tempfile.mkdtemp()
    store = ChromaVectorStore(directory, "test_collection")
    assert store.name == "chroma"
    assert store.count() == 0

    store.upsert(DOCUMENTS, EMBEDDINGS)
    assert store.count() == 2

    collection = store._collection
    record = collection.records["topic-1"]
    assert record["text"].startswith("Ohm")
    assert record["metadata"]["tags"] == "['a', 'b']", "lists must be stringified for Chroma"
    assert "none" not in record["metadata"], "None values must be dropped"
    assert record["embedding"] == [1.0, 0.0, 0.0]

    hits = store.query([1.0, 0.0, 0.0], top_k=2)
    assert isinstance(hits[0], SearchHit)
    assert abs(hits[0].score - 0.75) < 1e-6, "distance must be converted to a similarity score"
    assert collection.queries[-1]["n_results"] == 2

    store.query([1.0, 0.0, 0.0], top_k=1, where={"subject_id": 2})
    assert collection.queries[-1]["where"] == {"subject_id": 2}

    store.reset()
    assert store.count() == 0
    shutil.rmtree(directory, ignore_errors=True)


# --------------------------------------------------------------------------
# 3. Pinecone adapter
# --------------------------------------------------------------------------
def test_03_pinecone_adapter_creates_and_uses_an_index():
    module = install_pinecone_stub(existing_index=False)
    from app.vector.pinecone_store import PineconeVectorStore

    store = PineconeVectorStore("test-key", "vidyalaya-ai", dimension=3)
    assert store.name == "pinecone"
    assert module.Pinecone.created and module.Pinecone.created[-1]["dimension"] == 3, (
        "a missing index must be created with the embedding dimension"
    )

    store.upsert(DOCUMENTS, EMBEDDINGS)
    assert store.count() == 2
    stored = store._index.vectors["topic-2"]
    assert stored["values"] == [0.0, 1.0, 0.0]
    assert stored["metadata"]["text"].startswith("Integration"), "text must travel in metadata"

    hits = store.query([0.0, 1.0, 0.0], top_k=2)
    assert hits and hits[0].score == 0.75
    assert hits[0].text, "text must be lifted back out of metadata"
    assert "text" not in hits[0].metadata

    store.reset()
    assert store.count() == 0 and store._index.deleted

    # batching: 250 documents -> 3 upsert calls of at most 100
    many = [VectorDocument(id=f"d{i}", text=f"doc {i}", metadata={}) for i in range(250)]
    store.upsert(many, [[float(i), 0.0, 0.0] for i in range(250)])
    assert store._index.upsert_calls[-3:] == [100, 100, 50], store._index.upsert_calls


def test_04_pinecone_reuses_an_existing_index():
    module = install_pinecone_stub(existing_index=True)
    module.Pinecone.created.clear()
    from app.vector.pinecone_store import PineconeVectorStore

    PineconeVectorStore("test-key", "vidyalaya-ai", dimension=3)
    assert module.Pinecone.created == [], "an existing index must not be recreated"


# --------------------------------------------------------------------------
# 4. factory selection and graceful degradation
# --------------------------------------------------------------------------
def test_05_factory_selects_and_degrades():
    original = (settings.VECTOR_BACKEND, settings.PINECONE_API_KEY, settings.CHROMA_DIR)
    directory = tempfile.mkdtemp()
    settings.CHROMA_DIR = os.path.join(directory, "chroma")
    try:
        install_chroma_stub()
        settings.VECTOR_BACKEND, settings.PINECONE_API_KEY = "chroma", ""
        factory.reset_vector_store()
        assert factory.get_vector_store().name == "chroma"
        assert "chroma" in factory.backend_detail()

        # pinecone requested with a key -> pinecone
        install_pinecone_stub(existing_index=True)
        settings.VECTOR_BACKEND, settings.PINECONE_API_KEY = "pinecone", "test-key"
        factory.reset_vector_store()
        assert factory.get_vector_store().name == "pinecone"

        # pinecone requested without a key -> falls back to chroma
        settings.PINECONE_API_KEY = ""
        factory.reset_vector_store()
        assert factory.get_vector_store().name == "chroma"

        # chroma not installed -> built-in store
        sys.modules.pop("chromadb", None)
        sys.modules.pop("chromadb.config", None)
        sys.modules["chromadb"] = None          # simulate an import failure
        settings.VECTOR_BACKEND = "chroma"
        factory.reset_vector_store()
        assert factory.get_vector_store().name == "memory"
        assert "built-in" in factory.backend_detail()

        # explicit memory backend
        settings.VECTOR_BACKEND = "memory"
        factory.reset_vector_store()
        assert factory.get_vector_store().name == "memory"
    finally:
        sys.modules.pop("chromadb", None)
        sys.modules.pop("chromadb.config", None)
        sys.modules.pop("pinecone", None)
        settings.VECTOR_BACKEND, settings.PINECONE_API_KEY, settings.CHROMA_DIR = original
        factory.reset_vector_store()
        shutil.rmtree(directory, ignore_errors=True)


def test_06_every_implementation_satisfies_the_interface():
    from app.vector.chroma_store import ChromaVectorStore
    from app.vector.pinecone_store import PineconeVectorStore

    for implementation in (InMemoryVectorStore, ChromaVectorStore, PineconeVectorStore):
        assert issubclass(implementation, VectorStore)
        for method in ("reset", "upsert", "query", "count"):
            assert callable(getattr(implementation, method)), (implementation, method)
        assert getattr(implementation, "name", "abstract") != "abstract"


def test_07_rag_indexes_into_whichever_store_is_active():
    from app.ai.rag import index_content
    from app.db.session import SessionLocal

    install_chroma_stub()
    original = (settings.VECTOR_BACKEND, settings.CHROMA_DIR)
    directory = tempfile.mkdtemp()
    settings.VECTOR_BACKEND, settings.CHROMA_DIR = "chroma", os.path.join(directory, "chroma")
    factory.reset_vector_store()
    try:
        with SessionLocal() as db:
            result = index_content(db, force=True)
            assert result["backend"] == "chroma"
            assert result["indexed"] > 400, result
            store = factory.get_vector_store()
            assert store.count() == result["indexed"]

            from app.ai.embeddings import get_embedder

            hits = store.query(get_embedder().embed_one("Kirchhoff's laws"), top_k=3)
            assert hits, "the freshly indexed Chroma store returned nothing"
    finally:
        sys.modules.pop("chromadb", None)
        sys.modules.pop("chromadb.config", None)
        settings.VECTOR_BACKEND, settings.CHROMA_DIR = original
        factory.reset_vector_store()
        shutil.rmtree(directory, ignore_errors=True)


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f"  PASS  {test.__name__}")
    print(f"\n{passed}/{len(tests)} vector-store checks passed.")


if __name__ == "__main__":
    main()
