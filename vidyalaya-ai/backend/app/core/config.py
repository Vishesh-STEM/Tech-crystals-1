"""Application configuration.

Every value can be overridden with an environment variable (or a .env file).
No secrets are hard-coded; see .env.example at the repository root.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # ---- General -------------------------------------------------------
    APP_NAME: str = "Vidyalaya AI"
    APP_TAGLINE: str = "Learn smarter. Study what matters."
    ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # ---- Security ------------------------------------------------------
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    PASSWORD_HASH_ITERATIONS: int = 260000

    # ---- Database ------------------------------------------------------
    # PostgreSQL is the intended production database:
    #   postgresql+psycopg2://vidyalaya:vidyalaya@localhost:5432/vidyalaya
    # SQLite is the zero-setup development fallback.
    DATABASE_URL: str = "sqlite:///./vidyalaya.db"
    SQLITE_FALLBACK_URL: str = "sqlite:///./vidyalaya.db"
    ALLOW_SQLITE_FALLBACK: bool = True
    SQL_ECHO: bool = False

    # ---- CORS ----------------------------------------------------------
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://localhost:3000",
    ]

    # ---- AI / Ollama ---------------------------------------------------
    OLLAMA_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    OLLAMA_NUM_PREDICT: int = 512
    OLLAMA_TEMPERATURE: float = 0.3
    AI_HEALTH_CACHE_SECONDS: int = 30

    # ---- Embeddings / vector store -------------------------------------
    # "local"  -> TF-IDF + SVD via scikit-learn (no downloads, always works)
    # "sentence-transformers" -> free local model, used when installed
    EMBEDDING_BACKEND: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 256

    # "chroma" -> ChromaDB (default when installed), "memory" -> built-in
    # numpy store, "pinecone" -> reserved for the future implementation.
    VECTOR_BACKEND: str = "chroma"
    CHROMA_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "vidyalaya_content"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "vidyalaya-ai"
    PINECONE_ENVIRONMENT: str = ""
    RAG_TOP_K: int = 5

    # ---- Moodle (integration layer only; not required for the MVP) ------
    MOODLE_ENABLED: bool = False
    MOODLE_BASE_URL: str = ""
    MOODLE_WS_TOKEN: str = ""
    MOODLE_LTI_CLIENT_ID: str = ""

    # ---- Seeding -------------------------------------------------------
    SEED_ON_STARTUP: bool = True
    DEMO_STUDENT_EMAIL: str = "abhinav@student.vidyalaya.ai"
    DEMO_STUDENT_PASSWORD: str = "Student@123"
    DEMO_TEACHER_EMAIL: str = "teacher@vidyalaya.ai"
    DEMO_TEACHER_PASSWORD: str = "Teacher@123"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                return value
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
