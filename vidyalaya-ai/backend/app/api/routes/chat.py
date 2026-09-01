"""AI tutor chat endpoints (RAG + Ollama with an offline fallback)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.ollama_client import check_health
from app.ai.tutor import answer as tutor_answer
from app.api.deps import get_active_year, get_current_student
from app.core.config import settings
from app.db.base_class import utcnow
from app.db.session import get_db
from app.models import AcademicYear, ChatMessage, ChatSession, Student
from app.schemas.chat import ChatMessageOut, ChatRequest, ChatResponse, ChatSessionOut, ChatSource
from app.schemas.common import Message
from app.services.activity import log_event
from app.services.learning_profile import compute_learning_profile
from app.vector.factory import backend_detail, get_vector_store

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_session(db: Session, student: Student, session_id: Optional[int]) -> ChatSession:
    if session_id:
        session = db.get(ChatSession, session_id)
        if session is None or session.student_id != student.id:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return session
    session = ChatSession(student_id=student.id, title="New conversation")
    db.add(session)
    db.flush()
    return session


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse, include_in_schema=False)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> ChatResponse:
    session = _get_session(db, student, payload.session_id)
    question = payload.message.strip()

    db.add(
        ChatMessage(
            session_id=session.id, role="user", content=question,
            topic_id=payload.topic_id, created_at=utcnow(),
        )
    )
    db.flush()

    result = tutor_answer(
        db, student, question, year.id, topic_id=payload.topic_id, intent=payload.intent
    )
    topic = result.get("topic")
    assistant = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["content"],
        mode=result["mode"],
        model=result.get("model", ""),
        sources=result.get("sources", []),
        topic_id=topic.id if topic is not None else None,
        subject_id=topic.chapter.subject_id if topic is not None and topic.chapter else None,
        latency_ms=result.get("latency_ms", 0.0),
        created_at=utcnow(),
    )
    db.add(assistant)
    if session.title in ("New conversation", "", None):
        session.title = question[:80]
    session.last_message_at = utcnow()

    log_event(
        db, student, "asked_chatbot", topic_id=assistant.topic_id, subject_id=assistant.subject_id,
        academic_year_id=year.id, result=result["mode"],
        details={"intent": result.get("intent"), "session_id": session.id},
    )
    if result.get("intent") in ("explain", "simplify", "example"):
        log_event(
            db, student, "requested_explanation", topic_id=assistant.topic_id,
            academic_year_id=year.id, details={"session_id": session.id},
        )
    compute_learning_profile(db, student, year.id)
    db.commit()
    db.refresh(assistant)

    return ChatResponse(
        session_id=session.id,
        message=ChatMessageOut.model_validate(assistant),
        sources=[ChatSource(**source) for source in result.get("sources", [])],
        mode=result["mode"],
        model=result.get("model", ""),
        detected_subject=result.get("detected_subject"),
        detected_topic=result.get("detected_topic"),
        suggestions=result.get("suggestions", []),
        latency_ms=result.get("latency_ms", 0.0),
    )


@router.get("/sessions", response_model=List[ChatSessionOut])
def sessions(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    limit: int = Query(default=25, ge=1, le=100),
) -> List[ChatSessionOut]:
    rows = list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.student_id == student.id)
            .order_by(ChatSession.last_message_at.desc(), ChatSession.id.desc())
            .limit(limit)
        )
    )
    return [ChatSessionOut.model_validate(row) for row in rows]


@router.get("/history", response_model=List[ChatMessageOut])
def history(
    session_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[ChatMessageOut]:
    if session_id:
        session = _get_session(db, student, session_id)
        rows = list(
            db.scalars(
                select(ChatMessage).where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.id.asc()).limit(limit)
            )
        )
    else:
        rows = list(
            db.scalars(
                select(ChatMessage)
                .join(ChatSession, ChatMessage.session_id == ChatSession.id)
                .where(ChatSession.student_id == student.id)
                .order_by(ChatMessage.id.desc())
                .limit(limit)
            )
        )
        rows.reverse()
    return [ChatMessageOut.model_validate(row) for row in rows]


@router.delete("/sessions/{session_id}", response_model=Message)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Message:
    session = _get_session(db, student, session_id)
    db.delete(session)
    db.commit()
    return Message(detail="Conversation deleted.")


@router.get("/status", response_model=Dict[str, Any])
def status(student: Student = Depends(get_current_student)) -> Dict[str, Any]:
    available, detail, models = check_health()
    store = get_vector_store()
    return {
        "mode": "ollama" if available else "offline",
        "detail": detail if available else f"AI tutor is running in offline mode. {detail}",
        "model": settings.OLLAMA_MODEL,
        "installed_models": models,
        "base_url": settings.OLLAMA_BASE_URL,
        "vector_backend": store.name,
        "vector_detail": backend_detail(),
        "indexed_documents": store.count(),
        "rag_top_k": settings.RAG_TOP_K,
    }
