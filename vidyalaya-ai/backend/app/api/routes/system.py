"""Health and platform metadata endpoints (public)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import __version__
from app.ai.embeddings import get_embedder
from app.ai.ollama_client import check_health
from app.core.config import settings
from app.db.session import ACTIVE_DATABASE_URL, USING_FALLBACK, get_db
from app.integrations.moodle import integration_status
from app.ml.predictors import active_models
from app.models import Subject
from app.vector.factory import backend_detail, get_vector_store

router = APIRouter(tags=["system"])


@router.get("/health", response_model=Dict[str, Any])
def health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    database_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_ok = False
    available, detail, _models = check_health()
    store = get_vector_store()
    seeded = bool(db.scalar(select(func.count(Subject.id))))
    return {
        "status": "ok" if database_ok else "degraded",
        "app": settings.APP_NAME,
        "version": __version__,
        "environment": settings.ENV,
        "database": "connected" if database_ok else "unavailable",
        "database_engine": ACTIVE_DATABASE_URL.split(":")[0],
        "database_fallback_active": USING_FALLBACK,
        "ai_mode": "ollama" if available else "offline",
        "ai_detail": detail,
        "vector_backend": store.name,
        "vector_detail": backend_detail(),
        "indexed_documents": store.count(),
        "seeded": seeded,
    }


@router.get("/meta", response_model=Dict[str, Any])
def meta(db: Session = Depends(get_db)) -> Dict[str, Any]:
    available, detail, models = check_health()
    store = get_vector_store()
    return {
        "app": settings.APP_NAME,
        "tagline": settings.APP_TAGLINE,
        "version": __version__,
        "ai": {
            "mode": "ollama" if available else "offline",
            "detail": detail,
            "configured_model": settings.OLLAMA_MODEL,
            "installed_models": models,
            "base_url": settings.OLLAMA_BASE_URL,
        },
        "vector": {
            "backend": store.name,
            "detail": backend_detail(),
            "documents": store.count(),
            "embedding_backend": get_embedder().name,
            "embedding_dimension": get_embedder().dim,
            "pinecone_ready": True,
        },
        "ml_models": active_models(),
        "moodle": integration_status(),
        "subjects": db.scalar(select(func.count(Subject.id))) or 0,
    }
