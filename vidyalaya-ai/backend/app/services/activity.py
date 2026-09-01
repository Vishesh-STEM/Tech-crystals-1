"""Activity event tracking + derived study statistics."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base_class import utcnow
from app.models import ActivityEvent, Chapter, Resource, Student, Topic
from app.models.analytics import EVENT_TYPES
from app.services.academic import student_year

FORMAT_EVENT = {
    "text": "selected_text",
    "visual": "selected_visual",
    "audio": "selected_audio",
    "practice": "selected_practice",
}


def log_event(
    db: Session,
    student: Student,
    event_type: str,
    *,
    subject_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    resource_type: str = "",
    duration_seconds: int = 0,
    result: str = "",
    score: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
    academic_year_id: Optional[int] = None,
    created_at: Optional[datetime] = None,
) -> ActivityEvent:
    """Persist one meaningful learning event.

    Parent ids (subject/chapter) are filled in automatically from the topic or
    resource so the analytics queries stay simple.
    """
    if resource_id and not topic_id:
        resource = db.get(Resource, resource_id)
        if resource:
            topic_id = resource.topic_id
            resource_type = resource_type or resource.type
    if topic_id and not chapter_id:
        topic = db.get(Topic, topic_id)
        if topic:
            chapter_id = topic.chapter_id
    if chapter_id and not subject_id:
        chapter = db.get(Chapter, chapter_id)
        if chapter:
            subject_id = chapter.subject_id

    year_id = academic_year_id or student_year(db, student).id
    event = ActivityEvent(
        student_id=student.id,
        academic_year_id=year_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        topic_id=topic_id,
        resource_id=resource_id,
        event_type=event_type if event_type in EVENT_TYPES else event_type[:40],
        resource_type=resource_type or "",
        duration_seconds=max(0, int(duration_seconds or 0)),
        result=result or "",
        score=score,
        details=details or {},
        created_at=created_at or utcnow(),
    )
    db.add(event)
    return event


def study_minutes(db: Session, student_id: int, days: int = 7) -> int:
    since = utcnow() - timedelta(days=days)
    seconds = db.scalar(
        select(func.coalesce(func.sum(ActivityEvent.duration_seconds), 0)).where(
            ActivityEvent.student_id == student_id, ActivityEvent.created_at >= since
        )
    )
    return int((seconds or 0) / 60)


def streak_days(db: Session, student_id: int, max_days: int = 60) -> int:
    """Consecutive days (ending today or yesterday) with at least one event."""
    since = utcnow() - timedelta(days=max_days)
    rows = db.execute(
        select(ActivityEvent.created_at).where(
            ActivityEvent.student_id == student_id, ActivityEvent.created_at >= since
        )
    ).all()
    if not rows:
        return 0
    days = {row[0].date() for row in rows if row[0]}
    today = utcnow().date()
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def recent_activity(db: Session, student_id: int, limit: int = 20) -> List[ActivityEvent]:
    return list(
        db.scalars(
            select(ActivityEvent)
            .where(ActivityEvent.student_id == student_id)
            .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
            .limit(limit)
        )
    )


def continue_learning(db: Session, student_id: int, limit: int = 4) -> List[Dict[str, Any]]:
    """Most recently opened topics with their subject/chapter context."""
    rows = db.execute(
        select(
            ActivityEvent.topic_id,
            func.max(ActivityEvent.created_at).label("last_seen"),
            func.sum(ActivityEvent.duration_seconds).label("seconds"),
        )
        .where(
            ActivityEvent.student_id == student_id,
            ActivityEvent.topic_id.is_not(None),
            ActivityEvent.event_type.in_(
                ("opened_topic", "opened_resource", "completed_resource", "completed_quiz")
            ),
        )
        .group_by(ActivityEvent.topic_id)
        .order_by(func.max(ActivityEvent.created_at).desc())
        .limit(limit)
    ).all()

    items: List[Dict[str, Any]] = []
    for topic_id, last_seen, seconds in rows:
        topic = db.get(Topic, topic_id)
        if not topic:
            continue
        chapter = topic.chapter
        subject = chapter.subject if chapter else None
        items.append(
            {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "chapter_id": chapter.id if chapter else None,
                "chapter_name": chapter.name if chapter else "",
                "subject_id": subject.id if subject else None,
                "subject_name": subject.name if subject else "",
                "subject_slug": subject.slug if subject else "",
                "icon": subject.icon if subject else "📘",
                "color": subject.color if subject else "indigo",
                "last_seen": last_seen,
                "minutes_spent": int((seconds or 0) / 60),
            }
        )
    return items
