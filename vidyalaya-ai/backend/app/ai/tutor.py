"""The AI tutor orchestrator.

    question -> intent + subject/topic detection
             -> embedding -> vector search (Chroma) -> relevant content
             -> student learning profile + performance history
             -> Ollama (local LLM)  |  offline answer engine
             -> answer + sources (logged by the API layer)
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import offline
from app.ai.ollama_client import OllamaUnavailable, active_model, check_health, generate
from app.ai.prompts import SYSTEM_PROMPT, TASK_BY_INTENT, USER_PROMPT
from app.ai.rag import format_context, retrieve
from app.core.config import settings
from app.models import (
    Student, StudentSubjectMastery, StudentTopicMastery, Subject, Topic,
)
from app.services.learning_profile import get_or_create_profile, profile_payload
from app.services.recommendations import list_recommendations

INTENT_KEYWORDS = {
    "practice": ("practice", "questions on", "give me question", "quiz me", "problems on", "mcq"),
    "simplify": ("simpler", "simplify", "easy words", "explain like", "eli5", "don't understand", "confused"),
    "example": ("example", "solved", "numerical", "illustrate"),
    "revision": ("revise", "revision", "summary", "summarise", "summarize", "quick notes", "formula sheet"),
    "weakness": ("weak", "struggling", "bad at", "improve my", "why am i"),
    "next": ("what should i study", "what next", "study next", "plan my", "today"),
}


def detect_intent(message: str, explicit: Optional[str] = None) -> str:
    if explicit and explicit in TASK_BY_INTENT:
        return explicit
    lowered = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return "explain"


def resolve_topic(db: Session, hits, topic_id: Optional[int]) -> Optional[Topic]:
    if topic_id:
        topic = db.get(Topic, topic_id)
        if topic:
            return topic
    for hit in hits:
        candidate_id = (hit.metadata or {}).get("topic_id")
        if candidate_id:
            topic = db.get(Topic, int(candidate_id))
            if topic:
                return topic
    return None


def build_student_context(
    db: Session, student: Student, academic_year_id: int, topic: Optional[Topic]
) -> Dict[str, Any]:
    profile = profile_payload(get_or_create_profile(db, student, academic_year_id))

    subject_rows = list(
        db.scalars(
            select(StudentSubjectMastery).where(
                StudentSubjectMastery.student_id == student.id,
                StudentSubjectMastery.academic_year_id == academic_year_id,
            )
        )
    )
    subjects = []
    for row in subject_rows:
        subject = db.get(Subject, row.subject_id)
        if subject:
            subjects.append({"subject": subject.name, "mastery": row.mastery})
    subjects.sort(key=lambda item: item["mastery"])

    weak_rows = list(
        db.scalars(
            select(StudentTopicMastery)
            .where(
                StudentTopicMastery.student_id == student.id,
                StudentTopicMastery.academic_year_id == academic_year_id,
                StudentTopicMastery.is_weak.is_(True),
            )
            .order_by(StudentTopicMastery.mastery.asc())
            .limit(5)
        )
    )
    weak_topics = []
    for row in weak_rows:
        topic_row = db.get(Topic, row.topic_id)
        if topic_row:
            weak_topics.append(
                {
                    "topic": topic_row.name,
                    "mastery": row.mastery,
                    "reason": row.weakness_reason,
                }
            )

    topic_stats: Dict[str, Any] = {}
    if topic is not None:
        record = db.scalar(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id == student.id,
                StudentTopicMastery.topic_id == topic.id,
                StudentTopicMastery.academic_year_id == academic_year_id,
            )
        )
        if record:
            topic_stats = {
                "topic": topic.name,
                "mastery": record.mastery,
                "attempts": record.attempts,
                "average_score": record.average_score,
                "last_score": record.last_score,
                "questions_answered": record.questions_answered,
                "is_weak": record.is_weak,
                "weakness_reason": record.weakness_reason,
            }

    recommendations = list_recommendations(db, student.id, academic_year_id, limit=3)
    next_steps = [f"{r.title} - {r.reason}" for r in recommendations]

    overall = round(sum(s["mastery"] for s in subjects) / len(subjects), 1) if subjects else None
    return {
        "student_name": student.user.full_name if student.user else "Student",
        "class_level": student.class_level,
        "overall_mastery": overall,
        "subjects": subjects,
        "weak_topics": weak_topics,
        "topic_stats": topic_stats,
        "learning_profile": profile,
        "next_steps": next_steps,
    }


def context_to_text(context: Dict[str, Any]) -> str:
    lines = [
        f"Student name: {context['student_name']} (Class {context['class_level']})",
    ]
    if context.get("overall_mastery") is not None:
        lines.append(f"Overall mastery: {context['overall_mastery']}/100")
    if context.get("subjects"):
        lines.append(
            "Subject mastery: "
            + ", ".join(f"{s['subject']} {s['mastery']:.0f}" for s in context["subjects"])
        )
    if context.get("topic_stats"):
        stats = context["topic_stats"]
        lines.append(
            f"On '{stats['topic']}': mastery {stats['mastery']:.0f}/100, attempts {stats['attempts']}, "
            f"average {stats.get('average_score') or 0:.0f}%, last {stats.get('last_score') or 0:.0f}%."
        )
        if stats.get("weakness_reason"):
            lines.append(f"Weakness note: {stats['weakness_reason']}")
    if context.get("weak_topics"):
        lines.append(
            "Weak topics: "
            + "; ".join(f"{w['topic']} ({w['mastery']:.0f}/100)" for w in context["weak_topics"])
        )
    profile = context.get("learning_profile") or {}
    if profile:
        lines.append(
            "Resource effectiveness - text {t:.0%}, visual {v:.0%}, audio {a:.0%}, practice {p:.0%}".format(
                t=profile.get("text_effectiveness", 0.5),
                v=profile.get("visual_effectiveness", 0.5),
                a=profile.get("audio_effectiveness", 0.5),
                p=profile.get("practice_effectiveness", 0.5),
            )
        )
    if context.get("next_steps"):
        lines.append("Pending recommendations: " + " | ".join(context["next_steps"]))
    return "\n".join(lines)


def follow_up_suggestions(intent: str, topic: Optional[Topic]) -> List[str]:
    name = topic.name if topic else "this topic"
    base = [
        f"Explain {name} in simpler words",
        f"Give me 3 practice questions on {name}",
        f"Make a revision sheet for {name}",
    ]
    if intent == "next":
        base = [
            "Why is this topic weak for me?",
            "Plan my next 3 study sessions",
            "Which subject needs most attention?",
        ]
    return base


def answer(
    db: Session,
    student: Student,
    message: str,
    academic_year_id: int,
    topic_id: Optional[int] = None,
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    started = time.time()
    resolved_intent = detect_intent(message, intent)
    hits = retrieve(db, message, top_k=settings.RAG_TOP_K)
    topic = resolve_topic(db, hits, topic_id)
    context = build_student_context(db, student, academic_year_id, topic)

    mode, model, text = "offline", "", ""
    available, detail, _models = check_health()
    if available:
        try:
            prompt = USER_PROMPT.format(
                context=format_context(hits) or "(no stored content matched this question)",
                student_context=context_to_text(context),
                question=message.strip(),
                task=TASK_BY_INTENT.get(resolved_intent, TASK_BY_INTENT["explain"]),
            )
            text = generate(prompt, system=SYSTEM_PROMPT)
            mode, model = "ollama", active_model()
        except OllamaUnavailable as exc:
            detail = f"Ollama call failed ({exc}); answered in offline mode."
            text = ""

    if not text:
        text = offline.compose_answer(db, message, hits, context, resolved_intent, topic)
        mode = "offline"

    sources = []
    for hit in hits[:4]:
        metadata = hit.metadata or {}
        sources.append(
            {
                "title": metadata.get("title") or metadata.get("topic") or "Syllabus content",
                "subject": metadata.get("subject", ""),
                "chapter": metadata.get("chapter", ""),
                "topic": metadata.get("topic", ""),
                "topic_id": int(metadata["topic_id"]) if metadata.get("topic_id") else None,
                "ncert_url": metadata.get("ncert_url", ""),
                "score": round(float(hit.score), 3),
                "snippet": hit.text[:220],
            }
        )

    return {
        "content": text,
        "mode": mode,
        "model": model,
        "detail": detail,
        "sources": sources,
        "intent": resolved_intent,
        "topic": topic,
        "detected_subject": (hits[0].metadata or {}).get("subject") if hits else None,
        "detected_topic": topic.name if topic else None,
        "suggestions": follow_up_suggestions(resolved_intent, topic),
        "latency_ms": round((time.time() - started) * 1000, 1),
    }
