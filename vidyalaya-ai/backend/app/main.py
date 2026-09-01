"""Vidyalaya AI - FastAPI application entry point.

    uvicorn app.main:app --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import __version__
from app.api.routes import admin, auth, catalog, chat, quiz, student, system
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import SessionLocal, engine
from app.models import Subject

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("vidyalaya")


def bootstrap() -> None:
    """Create tables, seed the demo content and build the RAG index."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seeded = bool(db.scalar(select(func.count(Subject.id))))
        if not seeded and settings.SEED_ON_STARTUP:
            from app.seed.seed import seed_all

            logger.info("Empty database detected - seeding Class 12 content and demo data...")
            stats = seed_all(db)
            logger.info("Seed complete: %s", stats)
        try:
            from app.ai.rag import index_content
            from app.vector.factory import get_vector_store

            if get_vector_store().is_empty():
                logger.info("Building the RAG vector index: %s", index_content(db, force=True))
        except Exception as exc:  # pragma: no cover - never block startup on AI
            logger.warning("Vector index unavailable (%s). Chat will use keyword search.", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description=(
        "Personalised Class 12 learning platform - mastery tracking, weak-topic detection, "
        "recommendations and a local-LLM AI tutor with RAG."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a single readable message instead of a raw pydantic error list."""
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(part) for part in first.get("loc", [])[1:]) or "request"
    message = first.get("msg", "Invalid request.")
    message = message.replace("Value error, ", "")
    errors = [
        {
            "field": ".".join(str(part) for part in error.get("loc", [])[1:]),
            "message": str(error.get("msg", "")).replace("Value error, ", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"{field}: {message}", "errors": errors},
    )


@app.exception_handler(IntegrityError)
async def integrity_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """A constraint violation is a client conflict, not a server error."""
    logger.warning("Integrity error on %s: %s", request.url.path, exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "That would duplicate an existing record. "
                      "Try a different name or code."
        },
    )


for router in (
    system.router, auth.router, catalog.router, quiz.router,
    student.router, chat.router, admin.router,
):
    app.include_router(router, prefix=settings.API_PREFIX)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
