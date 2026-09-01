"""Student dashboard, progress, recommendations, learning profile and activity."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_active_year, get_current_student
from app.core.utils import greeting_for
from app.db.base_class import utcnow
from app.db.session import get_db
from app.models import (
    AcademicYear, ActivityEvent, Chapter, Quiz, QuizAttempt, Recommendation, Student,
    StudentAcademicYear, StudentSubjectMastery, StudentTopicMastery, Subject, Topic,
)
from app.schemas.common import Message
from app.schemas.student import ActivityIn, ActivityOut, RecommendationOut
from app.services.activity import continue_learning, log_event, streak_days, study_minutes
from app.services.learning_profile import compute_learning_profile, get_or_create_profile, profile_payload
from app.services.mastery import monthly_progress, overall_mastery, refresh_student_mastery
from app.services.recommendations import generate_recommendations, list_recommendations
from app.ai.ollama_client import check_health

router = APIRouter(prefix="/student", tags=["student"])


def _subject_progress(db: Session, student: Student, year: AcademicYear) -> List[Dict[str, Any]]:
    subjects = list(db.scalars(select(Subject).where(Subject.is_active.is_(True)).order_by(Subject.order_index)))
    records = {
        row.subject_id: row
        for row in db.scalars(
            select(StudentSubjectMastery).where(
                StudentSubjectMastery.student_id == student.id,
                StudentSubjectMastery.academic_year_id == year.id,
            )
        )
    }
    payload = []
    for subject in subjects:
        record = records.get(subject.id)
        topics_total = db.scalar(
            select(func.count(Topic.id)).join(Chapter, Topic.chapter_id == Chapter.id)
            .where(Chapter.subject_id == subject.id)
        ) or 0
        payload.append(
            {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "subject_slug": subject.slug,
                "icon": subject.icon,
                "color": subject.color,
                "mastery": record.mastery if record else 0.0,
                "topics_total": topics_total,
                "topics_started": record.topics_started if record else 0,
                "topics_mastered": record.topics_mastered if record else 0,
                "weak_topics": record.weak_topics if record else 0,
                "study_minutes": record.study_minutes if record else 0,
                "last_activity_at": record.last_activity_at if record else None,
            }
        )
    return payload


def _topic_rows(
    db: Session, student: Student, year: AcademicYear, weak: bool, limit: int = 5
) -> List[Dict[str, Any]]:
    query = select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == student.id,
        StudentTopicMastery.academic_year_id == year.id,
    )
    if weak:
        query = query.where(StudentTopicMastery.is_weak.is_(True)).order_by(StudentTopicMastery.mastery.asc())
    else:
        query = query.where(StudentTopicMastery.questions_answered > 0).order_by(
            StudentTopicMastery.mastery.desc()
        )
    rows = list(db.scalars(query.limit(limit)))
    payload = []
    for row in rows:
        topic = db.get(Topic, row.topic_id)
        if topic is None:
            continue
        chapter = topic.chapter
        subject = chapter.subject if chapter else None
        payload.append(
            {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "chapter_id": chapter.id if chapter else 0,
                "chapter_name": chapter.name if chapter else "",
                "subject_id": subject.id if subject else 0,
                "subject_name": subject.name if subject else "",
                "mastery": row.mastery,
                "attempts": row.attempts,
                "last_score": row.last_score,
                "average_score": row.average_score,
                "trend": row.trend or 0.0,
                "is_weak": row.is_weak,
                "weakness_confidence": row.weakness_confidence,
                "weakness_reason": row.weakness_reason or "",
                "last_activity_at": row.last_activity_at,
            }
        )
    return payload


def _stats(db: Session, student: Student, year: AcademicYear) -> Dict[str, Any]:
    attempts = list(
        db.scalars(
            select(QuizAttempt).where(
                QuizAttempt.student_id == student.id,
                QuizAttempt.academic_year_id == year.id,
                QuizAttempt.status == "submitted",
            )
        )
    )
    questions_answered = db.scalar(
        select(func.count(ActivityEvent.id)).where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.event_type.in_(("correct_answer", "incorrect_answer")),
        )
    ) or 0
    correct = db.scalar(
        select(func.count(ActivityEvent.id)).where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.event_type == "correct_answer",
        )
    ) or 0
    return {
        "quizzes_taken": len(attempts),
        "average_accuracy": round(sum(a.accuracy for a in attempts) / len(attempts), 1) if attempts else 0.0,
        "questions_answered": questions_answered,
        "accuracy": round(100.0 * correct / questions_answered, 1) if questions_answered else 0.0,
        "study_minutes_7d": study_minutes(db, student.id, 7),
        "study_minutes_30d": study_minutes(db, student.id, 30),
        "streak_days": streak_days(db, student.id),
        "daily_goal_minutes": student.daily_goal_minutes or 45,
    }


@router.get("/dashboard", response_model=Dict[str, Any])
def dashboard(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    recommendations = list_recommendations(db, student.id, year.id, limit=5)
    if not recommendations:
        recommendations = generate_recommendations(db, student, year.id)
        db.commit()
    profile = profile_payload(get_or_create_profile(db, student, year.id))
    available, detail, _models = check_health()
    db.commit()
    return {
        "greeting": greeting_for(),
        "student_name": student.user.full_name if student.user else "Student",
        "academic_year": year.label,
        "overall_mastery": overall_mastery(db, student.id, year.id),
        "subjects": _subject_progress(db, student, year),
        "needs_attention": _topic_rows(db, student, year, weak=True, limit=4),
        "recommended_today": [
            RecommendationOut.model_validate(item).model_dump() for item in recommendations
        ],
        "continue_learning": continue_learning(db, student.id, limit=4),
        "stats": _stats(db, student, year),
        "learning_profile": profile,
        "monthly_progress": monthly_progress(db, student.id, year.id),
        "ai_status": {"mode": "ollama" if available else "offline", "detail": detail},
    }


@router.get("/progress", response_model=Dict[str, Any])
def progress(
    academic_year_id: Optional[int] = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    if academic_year_id:
        selected = db.get(AcademicYear, academic_year_id)
        if selected is None:
            raise HTTPException(status_code=404, detail="Academic year not found.")
        year = selected

    attempts = list(
        db.scalars(
            select(QuizAttempt)
            .where(
                QuizAttempt.student_id == student.id,
                QuizAttempt.academic_year_id == year.id,
                QuizAttempt.status == "submitted",
            )
            .order_by(QuizAttempt.submitted_at.asc())
        )
    )
    history = []
    for attempt in attempts[-20:]:
        quiz = db.get(Quiz, attempt.quiz_id)
        subject = db.get(Subject, quiz.subject_id) if quiz else None
        history.append(
            {
                "attempt_id": attempt.id,
                "quiz_id": attempt.quiz_id,
                "quiz_title": quiz.title if quiz else "",
                "subject_name": subject.name if subject else "",
                "accuracy": attempt.accuracy,
                "score": attempt.score,
                "max_score": attempt.max_score,
                "submitted_at": attempt.submitted_at,
            }
        )
    stats = _stats(db, student, year)
    return {
        "academic_year": year.label,
        "academic_year_id": year.id,
        "overall_mastery": overall_mastery(db, student.id, year.id),
        "subjects": _subject_progress(db, student, year),
        "weak_topics": _topic_rows(db, student, year, weak=True, limit=10),
        "strong_topics": _topic_rows(db, student, year, weak=False, limit=6),
        "monthly_progress": monthly_progress(db, student.id, year.id, months=12),
        "quiz_history": history,
        "study_minutes_7d": stats["study_minutes_7d"],
        "quizzes_taken": stats["quizzes_taken"],
        "questions_answered": stats["questions_answered"],
        "accuracy": stats["accuracy"],
        "streak_days": stats["streak_days"],
    }


@router.get("/years", response_model=List[Dict[str, Any]])
def academic_years(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[Dict[str, Any]]:
    links = list(
        db.scalars(
            select(StudentAcademicYear).where(StudentAcademicYear.student_id == student.id)
        )
    )
    payload = []
    for link in links:
        year = db.get(AcademicYear, link.academic_year_id)
        if not year:
            continue
        payload.append(
            {
                "id": year.id,
                "label": year.label,
                "is_current": bool(year.is_current),
                "class_level": link.class_level,
                "overall_mastery": overall_mastery(db, student.id, year.id),
                "monthly_progress": monthly_progress(db, student.id, year.id, months=12),
            }
        )
    payload.sort(key=lambda item: item["label"], reverse=True)
    return payload


@router.get("/mastery", response_model=List[Dict[str, Any]])
def mastery(
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> List[Dict[str, Any]]:
    query = select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == student.id,
        StudentTopicMastery.academic_year_id == year.id,
    )
    if subject_id:
        query = query.where(StudentTopicMastery.subject_id == subject_id)
    rows = list(db.scalars(query.order_by(StudentTopicMastery.mastery.desc())))
    payload = []
    for row in rows:
        topic = db.get(Topic, row.topic_id)
        subject = db.get(Subject, row.subject_id) if row.subject_id else None
        payload.append(
            {
                "topic_id": row.topic_id,
                "topic_name": topic.name if topic else "",
                "subject_id": row.subject_id,
                "subject_name": subject.name if subject else "",
                "mastery": row.mastery,
                "confidence": row.confidence,
                "attempts": row.attempts,
                "questions_answered": row.questions_answered,
                "average_score": row.average_score,
                "last_score": row.last_score,
                "trend": row.trend,
                "is_weak": row.is_weak,
                "weakness_confidence": row.weakness_confidence,
                "weakness_reason": row.weakness_reason,
                "repeated_mistakes": row.repeated_mistake_concepts or [],
                "last_activity_at": row.last_activity_at,
            }
        )
    return payload


@router.get("/profile", response_model=Dict[str, Any])
def learning_profile(
    recompute: bool = False,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    record = compute_learning_profile(db, student, year.id) if recompute else get_or_create_profile(db, student, year.id)
    db.commit()
    payload = profile_payload(record)
    payload["note"] = (
        "These are adaptive resource-effectiveness signals computed from your own results. "
        "They change as you study - they are not a fixed learning style."
    )
    payload["student"] = {
        "name": student.user.full_name if student.user else "",
        "email": student.user.email if student.user else "",
        "class_level": student.class_level,
        "stream": student.stream,
        "school": student.school,
        "roll_number": student.roll_number,
        "academic_year": year.label,
        "daily_goal_minutes": student.daily_goal_minutes,
    }
    return payload


@router.get("/recommendations", response_model=List[RecommendationOut])
def recommendations(
    status: str = Query(default="pending", pattern="^(pending|done|dismissed|all)$"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> List[RecommendationOut]:
    items = list_recommendations(db, student.id, year.id, limit=limit, status=status)
    if not items and status == "pending":
        items = generate_recommendations(db, student, year.id)
        db.commit()
    return [RecommendationOut.model_validate(item) for item in items]


@router.post("/recommendations/refresh", response_model=List[RecommendationOut])
def refresh_recommendations(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> List[RecommendationOut]:
    refresh_student_mastery(db, student, year.id, topic_ids=None)
    compute_learning_profile(db, student, year.id)
    items = generate_recommendations(db, student, year.id)
    db.commit()
    return [RecommendationOut.model_validate(item) for item in items]


@router.post("/recommendations/{recommendation_id}/{action}", response_model=Message)
def update_recommendation(
    recommendation_id: int,
    action: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Message:
    if action not in ("complete", "dismiss", "open"):
        raise HTTPException(status_code=400, detail="Unknown action.")
    recommendation = db.get(Recommendation, recommendation_id)
    if recommendation is None or recommendation.student_id != student.id:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    if action == "complete":
        recommendation.status = "done"
        recommendation.completed_at = utcnow()
        log_event(
            db, student, "completed_recommendation", topic_id=recommendation.topic_id,
            subject_id=recommendation.subject_id, academic_year_id=year.id,
            details={"recommendation_id": recommendation.id},
        )
    elif action == "dismiss":
        recommendation.status = "dismissed"
    else:
        log_event(
            db, student, "viewed_recommendation", topic_id=recommendation.topic_id,
            subject_id=recommendation.subject_id, academic_year_id=year.id,
            details={"recommendation_id": recommendation.id},
        )
    db.commit()
    return Message(detail=f"Recommendation marked as {recommendation.status}.")


@router.get("/activity", response_model=List[ActivityOut])
def activity(
    limit: int = Query(default=30, ge=1, le=200),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[ActivityOut]:
    query = select(ActivityEvent).where(ActivityEvent.student_id == student.id)
    if event_type:
        query = query.where(ActivityEvent.event_type == event_type)
    rows = list(db.scalars(query.order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc()).limit(limit)))
    return [ActivityOut.model_validate(row) for row in rows]


@router.post("/activity", response_model=ActivityOut, status_code=201)
def track_activity(
    payload: ActivityIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> ActivityOut:
    event = log_event(
        db, student, payload.event_type,
        subject_id=payload.subject_id, chapter_id=payload.chapter_id, topic_id=payload.topic_id,
        resource_id=payload.resource_id, duration_seconds=payload.duration_seconds,
        result=payload.result, score=payload.score, details=payload.details,
        academic_year_id=year.id,
    )
    db.flush()
    # completing a resource or spending time changes the learning profile
    if payload.event_type in ("completed_resource", "spent_time", "abandoned_topic"):
        compute_learning_profile(db, student, year.id)
    db.commit()
    db.refresh(event)
    return ActivityOut.model_validate(event)


@router.get("/heatmap", response_model=List[Dict[str, Any]])
def study_heatmap(
    days: int = Query(default=60, ge=7, le=365),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[Dict[str, Any]]:
    since = utcnow() - timedelta(days=days)
    rows = db.execute(
        select(
            func.date(ActivityEvent.created_at).label("day"),
            func.count(ActivityEvent.id),
            func.coalesce(func.sum(ActivityEvent.duration_seconds), 0),
        )
        .where(ActivityEvent.student_id == student.id, ActivityEvent.created_at >= since)
        .group_by(func.date(ActivityEvent.created_at))
        .order_by(func.date(ActivityEvent.created_at))
    ).all()
    return [
        {"date": str(day), "events": int(count), "minutes": int((seconds or 0) / 60)}
        for day, count, seconds in rows
    ]
