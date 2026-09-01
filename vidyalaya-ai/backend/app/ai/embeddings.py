"""Free, local embeddings.

Default backend ("local") uses scikit-learn TF-IDF + truncated SVD: it needs no
downloads, no API key and no GPU. If ``sentence-transformers`` is installed the
free MiniLM model is used instead (set EMBEDDING_BACKEND=sentence-transformers).
A pure-python hashing embedder is the last-resort fallback so the app can never
fail to start because of embeddings.
"""
from __future__ import annotations

import hashlib
import math
import os
import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from app.core.config import settings

MODEL_DIR = os.environ.get("ML_MODEL_DIR", "./data/models")
_lock = threading.Lock()


class Embedder(ABC):
    name = "abstract"
    dim = 0

    @abstractmethod
    def fit(self, corpus: Sequence[str]) -> None: ...

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> List[List[float]]: ...

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]


def _normalise(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


class HashingEmbedder(Embedder):
    """Dependency-free bag-of-words hashing embedder (always available)."""

    name = "hashing"

    def __init__(self, dim: int = 256):
        self.dim = dim
        self._idf: dict[str, float] = {}

    @staticmethod
    def _tokens(text: str) -> List[str]:
        cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
        return [t for t in cleaned.split() if len(t) > 2]

    def fit(self, corpus: Sequence[str]) -> None:
        document_frequency: dict[str, int] = {}
        for document in corpus:
            for token in set(self._tokens(document)):
                document_frequency[token] = document_frequency.get(token, 0) + 1
        total = max(1, len(corpus))
        self._idf = {
            token: math.log((total + 1) / (count + 1)) + 1.0
            for token, count in document_frequency.items()
        }

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            vector = [0.0] * self.dim
            for token in self._tokens(text):
                index = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dim
                vector[index] += self._idf.get(token, 1.0)
            vectors.append(_normalise(vector))
        return vectors


class LocalTfidfEmbedder(Embedder):
    """TF-IDF + SVD embeddings via scikit-learn (free, local, deterministic)."""

    name = "tfidf-svd"

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.target_dim = dim          # configured size; self.dim tracks the fitted size
        self._vectorizer = None
        self._svd = None

    def fit(self, corpus: Sequence[str]) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus = [c for c in corpus if c and c.strip()] or ["vidyalaya"]
        vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), min_df=1, max_features=20000
        )
        matrix = vectorizer.fit_transform(corpus)
        components = max(
            2, min(self.target_dim, matrix.shape[1] - 1, max(2, matrix.shape[0] - 1))
        )
        svd = TruncatedSVD(n_components=components, random_state=42)
        svd.fit(matrix)
        self._vectorizer = vectorizer
        self._svd = svd
        self.dim = components
        self.save()

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if self._vectorizer is None or self._svd is None:
            raise RuntimeError("Embedder is not fitted yet - run the content indexer first.")
        matrix = self._vectorizer.transform(list(texts))
        reduced = self._svd.transform(matrix)
        return [_normalise([float(x) for x in row]) for row in reduced]

    # -- persistence -------------------------------------------------------
    @property
    def path(self) -> str:
        return os.path.join(MODEL_DIR, "embedder.joblib")

    def save(self) -> None:
        try:
            import joblib

            os.makedirs(MODEL_DIR, exist_ok=True)
            joblib.dump({"vectorizer": self._vectorizer, "svd": self._svd, "dim": self.dim}, self.path)
        except Exception:
            pass

    def load(self) -> bool:
        try:
            import joblib

            if not os.path.exists(self.path):
                return False
            payload = joblib.load(self.path)
            self._vectorizer = payload["vectorizer"]
            self._svd = payload["svd"]
            self.dim = payload.get("dim", self.dim)   # fitted size, may differ from target
            return True
        except Exception:
            return False


class SentenceTransformerEmbedder(Embedder):  # pragma: no cover - optional
    name = "sentence-transformers"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def fit(self, corpus: Sequence[str]) -> None:
        return None  # pre-trained

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        vectors = self._model.encode(list(texts), normalize_embeddings=True)
        return [[float(x) for x in vector] for vector in vectors]


_embedder: Optional[Embedder] = None


def get_embedder() -> Embedder:
    global _embedder
    with _lock:
        if _embedder is not None:
            return _embedder
        backend = (settings.EMBEDDING_BACKEND or "local").lower()
        if backend in ("sentence-transformers", "st", "minilm"):
            try:
                _embedder = SentenceTransformerEmbedder(settings.EMBEDDING_MODEL)
                return _embedder
            except Exception:
                pass
        try:
            import sklearn  # noqa: F401

            embedder = LocalTfidfEmbedder(settings.EMBEDDING_DIM)
            embedder.load()
            _embedder = embedder
        except Exception:
            _embedder = HashingEmbedder(settings.EMBEDDING_DIM)
        return _embedder


def reset_embedder() -> None:
    global _embedder
    with _lock:
        _embedder = None
