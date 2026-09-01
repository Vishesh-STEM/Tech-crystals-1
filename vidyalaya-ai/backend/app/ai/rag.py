"""Retrieval-Augmented Generation over the platform's own course content.

Pipeline: question -> embedding -> vector search -> relevant syllabus content.
The index is built from topics and resources stored in the database, so the AI
always prioritises the educational content inside the application.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.embeddings import LocalTfidfEmbedder, get_embedder
from app.core.config import settings
from app.models import Chapter, Question, Resource, Subject, Topic
from app.vector.base import SearchHit, VectorDocument
from app.vector.factory import get_vector_store

logger = logging.getLogger(__name__)


def _topic_document(topic: Topic, chapter: Chapter, subject: Subject) -> VectorDocument:
    concepts = ", ".join(topic.key_concepts or [])
    examples = " ".join(topic.examples or [])
    text = (
        f"{subject.name} > {chapter.name} > {topic.name}\n"
        f"{topic.summary}\n"
        f"Key concepts: {concepts}\n"
        f"Examples: {examples}"
    ).strip()
    return VectorDocument(
        id=f"topic-{topic.id}",
        text=text,
        metadata={
            "kind": "topic",
            "topic_id": topic.id,
            "topic": topic.name,
            "chapter_id": chapter.id,
            "chapter": chapter.name,
            "subject_id": subject.id,
            "subject": subject.name,
            "ncert_url": topic.ncert_url or chapter.ncert_url or subject.ncert_url or "",
            "difficulty": topic.difficulty or "medium",
        },
    )


def _resource_document(resource: Resource, topic: Topic, chapter: Chapter, subject: Subject) -> VectorDocument:
    text = (
        f"{subject.name} > {chapter.name} > {topic.name} > {resource.title} "
        f"({resource.type})\n{resource.description}\n{resource.body}"
    ).strip()
    return VectorDocument(
        id=f"resource-{resource.id}",
        text=text,
        metadata={
            "kind": "resource",
            "resource_id": resource.id,
            "resource_type": resource.type,
            "title": resource.title,
            "topic_id": topic.id,
            "topic": topic.name,
            "chapter_id": chapter.id,
            "chapter": chapter.name,
            "subject_id": subject.id,
            "subject": subject.name,
            "ncert_url": resource.ncert_url or topic.ncert_url or "",
        },
    )


def build_documents(db: Session) -> List[VectorDocument]:
    documents: List[VectorDocument] = []
    rows = db.execute(
        select(Topic, Chapter, Subject)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .where(Topic.is_active.is_(True))
    ).all()
    for topic, chapter, subject in rows:
        documents.append(_topic_document(topic, chapter, subject))
    resource_rows = db.execute(
        select(Resource, Topic, Chapter, Subject)
        .join(Topic, Resource.topic_id == Topic.id)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .where(Resource.is_active.is_(True))
    ).all()
    for resource, topic, chapter, subject in resource_rows:
        documents.append(_resource_document(resource, topic, chapter, subject))
    return documents


def index_content(db: Session, force: bool = True) -> Dict[str, Any]:
    """(Re)build the vector index from the database content."""
    store = get_vector_store()
    if not force and not store.is_empty():
        return {"indexed": store.count(), "rebuilt": False, "backend": store.name}

    documents = build_documents(db)
    if not documents:
        return {"indexed": 0, "rebuilt": False, "backend": store.name}

    embedder = get_embedder()
    if isinstance(embedder, LocalTfidfEmbedder):
        embedder.fit([document.text for document in documents])
    else:
        try:
            embedder.fit([document.text for document in documents])
        except Exception:
            pass

    embeddings = embedder.embed([document.text for document in documents])
    store.reset()
    batch = 200
    for start in range(0, len(documents), batch):
        store.upsert(documents[start : start + batch], embeddings[start : start + batch])
    logger.info("Indexed %s documents into %s", len(documents), store.name)
    return {
        "indexed": len(documents),
        "rebuilt": True,
        "backend": store.name,
        "embedder": embedder.name,
        "dimension": embedder.dim,
    }


def keyword_search(db: Session, query: str, top_k: int = 5) -> List[SearchHit]:
    """Database keyword fallback (used when the vector index is unavailable)."""
    words = [w for w in "".join(c.lower() if c.isalnum() else " " for c in query).split() if len(w) > 2]
    if not words:
        return []
    conditions = []
    for word in words[:6]:
        pattern = f"%{word}%"
        conditions.extend([Topic.name.ilike(pattern), Topic.summary.ilike(pattern)])
    rows = db.execute(
        select(Topic, Chapter, Subject)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .where(or_(*conditions))
        .limit(top_k * 2)
    ).all()
    hits: List[SearchHit] = []
    for topic, chapter, subject in rows:
        haystack = f"{topic.name} {topic.summary} {' '.join(topic.key_concepts or [])}".lower()
        score = sum(1 for word in words if word in haystack) / max(1, len(words))
        document = _topic_document(topic, chapter, subject)
        hits.append(SearchHit(id=document.id, text=document.text, metadata=document.metadata, score=score))
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits[:top_k]


def retrieve(
    db: Session, query: str, top_k: Optional[int] = None, subject_id: Optional[int] = None
) -> List[SearchHit]:
    top_k = top_k or settings.RAG_TOP_K
    store = get_vector_store()
    hits: List[SearchHit] = []
    if not store.is_empty():
        try:
            embedder = get_embedder()
            embedding = embedder.embed_one(query)
            where = {"subject_id": subject_id} if subject_id else None
            hits = store.query(embedding, top_k=top_k, where=where)
        except Exception as exc:
            logger.warning("Vector search failed (%s); falling back to keyword search.", exc)
            hits = []
    hits = [hit for hit in hits if hit.score > 0.02]
    if not hits:
        hits = keyword_search(db, query, top_k)
    return hits


def practice_questions(db: Session, topic_id: int, limit: int = 3) -> List[Question]:
    return list(
        db.scalars(
            select(Question)
            .where(Question.topic_id == topic_id, Question.is_active.is_(True))
            .order_by(Question.difficulty.desc())
            .limit(limit)
        )
    )


def format_context(hits: List[SearchHit], limit_chars: int = 3500) -> str:
    blocks: List[str] = []
    used = 0
    for index, hit in enumerate(hits, start=1):
        metadata = hit.metadata or {}
        header = f"[{index}] {metadata.get('subject','')} > {metadata.get('chapter','')} > {metadata.get('topic','')}"
        body = hit.text.strip()
        block = f"{header}\n{body}"
        if used + len(block) > limit_chars:
            block = block[: max(0, limit_chars - used)]
        blocks.append(block)
        used += len(block)
        if used >= limit_chars:
            break
    return "\n\n".join(blocks)
