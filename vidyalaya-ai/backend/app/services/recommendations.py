"""Rule-based recommendation engine (ML-ready).

Signals used: mastery, recent performance, weakness confidence, resource
effectiveness (learning profile), question difficulty, prerequisite topics,
time since last study and recent activity. Every recommendation carries a
human-readable reason so the student knows *why* it was suggested.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base_class import utcnow
from app.models import (
    ActivityEvent, Quiz, Recommendation, Resource, Student, StudentTopicMastery,
    Subject, Topic,
)
from app.ml.predictors import get_recommendation_ranker
from app.services.learning_profile import get_or_create_profile, profile_payload

MAX_RECOMMENDATIONS = 8
FORMAT_LABEL = {
    "text": "Text explanations",
    "visual": "Visual explanations",
    "audio": "Audio revision",
    "practice": "Practice sets",
}


def _find_quiz_for_topic(db: Session, topic: Topic) -> Optional[Quiz]:
    quiz = db.scalar(
        select(Quiz).where(Quiz.topic_id == topic.id, Quiz.is_published.is_(True)).limit(1)
    )
    if quiz:
        return quiz
    return db.scalar(
        select(Quiz)
        .where(Quiz.chapter_id == topic.chapter_id, Quiz.is_published.is_(True))
        .limit(1)
    )


def _resource_for_format(db: Session, topic_id: int, fmt: str) -> Optional[Resource]:
    return db.scalar(
        select(Resource)
        .where(Resource.topic_id == topic_id, Resource.type == fmt, Resource.is_active.is_(True))
        .order_by(Resource.order_index)
        .limit(1)
    )


def _days_since(value) -> Optional[int]:
    if not value:
        return None
    return max(0, (utcnow() - value).days)


def build_candidates(
    db: Session, student: Student, academic_year_id: int
) -> List[Dict[str, Any]]:
    records = list(
        db.scalars(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id == student.id,
                StudentTopicMastery.academic_year_id == academic_year_id,
            )
        )
    )
    profile = profile_payload(get_or_create_profile(db, student, academic_year_id))
    best_format = profile["strongest_format"]
    candidates: List[Dict[str, Any]] = []
    by_topic = {record.topic_id: record for record in records}

    for record in records:
        topic = db.get(Topic, record.topic_id)
        if topic is None or not topic.is_active:
            continue
        subject = db.get(Subject, record.subject_id) if record.subject_id else None
        subject_name = subject.name if subject else ""
        idle_days = _days_since(record.last_activity_at)
        quiz = _find_quiz_for_topic(db, topic)

        # 1) weak topics -> revise, highest priority
        if record.is_weak:
            weight = 0.9 if record.weakness_confidence == "high" else 0.75
            if idle_days is not None and idle_days > 7:
                weight += 0.03
            candidates.append(
                {
                    "kind": "revise",
                    "title": f"Revise {topic.name}",
                    "reason": record.weakness_reason
                    or f"Your mastery in {topic.name} is {record.mastery:.0f}/100.",
                    "priority": min(0.99, weight + (100 - record.mastery) / 500),
                    "topic": topic,
                    "subject_id": record.subject_id,
                    "estimated_minutes": topic.estimated_minutes or 25,
                    "action_label": "Revise topic",
                    "action_url": f"/topics/{topic.id}",
                }
            )

            # 1b) prerequisite gap
            for prerequisite_slug in (topic.prerequisites or [])[:2]:
                prerequisite = db.scalar(select(Topic).where(Topic.slug == prerequisite_slug))
                if prerequisite is None:
                    continue
                prerequisite_record = by_topic.get(prerequisite.id)
                prerequisite_mastery = prerequisite_record.mastery if prerequisite_record else 0.0
                if prerequisite_mastery < max(60.0, record.mastery):
                    candidates.append(
                        {
                            "kind": "prerequisite",
                            "title": f"Revisit {prerequisite.name} first",
                            "reason": (
                                f"{prerequisite.name} is a prerequisite for {topic.name}, and your "
                                f"mastery there is {prerequisite_mastery:.0f}/100."
                            ),
                            "priority": 0.72,
                            "topic": prerequisite,
                            "subject_id": record.subject_id,
                            "estimated_minutes": prerequisite.estimated_minutes or 20,
                            "action_label": "Open prerequisite",
                            "action_url": f"/topics/{prerequisite.id}",
                        }
                    )

        # 2) shaky but not weak -> targeted practice
        elif 45 <= record.mastery < 75 and record.questions_answered >= 3:
            candidates.append(
                {
                    "kind": "practice",
                    "title": f"Practice 5 questions on {topic.name}",
                    "reason": (
                        f"You are at {record.mastery:.0f}/100 in {topic.name}. A short practice set "
                        f"is the fastest way to push it above 75."
                    ),
                    "priority": 0.6 + (75 - record.mastery) / 400,
                    "topic": topic,
                    "subject_id": record.subject_id,
                    "quiz": quiz,
                    "estimated_minutes": 15,
                    "action_label": "Start practice",
                    "action_url": f"/quiz/{quiz.id}" if quiz else f"/topics/{topic.id}",
                }
            )

        # 3) strong -> stretch
        elif record.mastery >= 85 and record.questions_answered >= 4:
            candidates.append(
                {
                    "kind": "advance",
                    "title": f"You're doing well in {topic.name}. Try advanced problems.",
                    "reason": (
                        f"Mastery {record.mastery:.0f}/100 with {record.attempts} attempts - "
                        f"harder questions will keep this topic sharp."
                    ),
                    "priority": 0.4,
                    "topic": topic,
                    "subject_id": record.subject_id,
                    "quiz": quiz,
                    "estimated_minutes": 20,
                    "action_label": "Attempt harder set",
                    "action_url": f"/quiz/{quiz.id}" if quiz else f"/topics/{topic.id}",
                }
            )

        # 4) stale knowledge -> spaced revision
        if idle_days is not None and idle_days >= 14 and record.mastery < 85 and not record.is_weak:
            candidates.append(
                {
                    "kind": "revise",
                    "title": f"Refresh {topic.name}",
                    "reason": f"You have not studied {topic.name} for {idle_days} days.",
                    "priority": 0.55 + min(0.2, idle_days / 100),
                    "topic": topic,
                    "subject_id": record.subject_id,
                    "estimated_minutes": 15,
                    "action_label": "Quick revision",
                    "action_url": f"/topics/{topic.id}",
                }
            )

    # 5) resume an opened-but-unfinished topic
    resume_rows = db.execute(
        select(ActivityEvent.topic_id, func.max(ActivityEvent.created_at))
        .where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.event_type == "opened_topic",
            ActivityEvent.topic_id.is_not(None),
        )
        .group_by(ActivityEvent.topic_id)
        .order_by(func.max(ActivityEvent.created_at).desc())
        .limit(3)
    ).all()
    for topic_id, last_seen in resume_rows:
        record = by_topic.get(topic_id)
        if record and record.questions_answered > 0:
            continue
        topic = db.get(Topic, topic_id)
        if topic is None:
            continue
        candidates.append(
            {
                "kind": "resume",
                "title": f"Finish {topic.name}",
                "reason": "You opened this topic but have not been assessed on it yet.",
                "priority": 0.5,
                "topic": topic,
                "subject_id": topic.chapter.subject_id if topic.chapter else None,
                "estimated_minutes": topic.estimated_minutes or 20,
                "action_label": "Continue",
                "action_url": f"/topics/{topic.id}",
            }
        )

    # 6) format nudge from the learning profile
    weak_records = [r for r in records if r.is_weak]
    if weak_records and profile["samples"].get(best_format, 0) >= 2:
        target = min(weak_records, key=lambda r: r.mastery)
        topic = db.get(Topic, target.topic_id)
        subject = db.get(Subject, target.subject_id) if target.subject_id else None
        resource = _resource_for_format(db, target.topic_id, best_format) if topic else None
        if topic:
            subject_name = subject.name if subject else "your subjects"
            candidates.append(
                {
                    "kind": "format",
                    "title": f"{FORMAT_LABEL[best_format]} work best for you - try one on {topic.name}",
                    "reason": (
                        f"{FORMAT_LABEL[best_format]} have produced better quiz results for you on "
                        f"{subject_name} topics "
                        f"({profile[best_format + '_effectiveness'] * 100:.0f}% effectiveness)."
                    ),
                    "priority": 0.65,
                    "topic": topic,
                    "subject_id": target.subject_id,
                    "resource": resource,
                    "estimated_minutes": resource.estimated_minutes if resource else 12,
                    "action_label": "Open resource",
                    "action_url": f"/topics/{topic.id}",
                }
            )

    return candidates


def generate_recommendations(
    db: Session, student: Student, academic_year_id: int, limit: int = MAX_RECOMMENDATIONS
) -> List[Recommendation]:
    """Regenerate the pending recommendation list for a student."""
    candidates = build_candidates(db, student, academic_year_id)
    ranker = get_recommendation_ranker()
    candidates = ranker.rank(candidates)

    seen: set = set()
    selected: List[Dict[str, Any]] = []
    for candidate in candidates:
        topic = candidate.get("topic")
        key = (candidate["kind"], topic.id if topic else None)
        topic_key = topic.id if topic else None
        if key in seen or (topic_key is not None and topic_key in {s.get("topic").id for s in selected if s.get("topic")}):
            continue
        seen.add(key)
        selected.append(candidate)
        if len(selected) >= limit:
            break

    # Replace only the auto-generated pending rows; completed history is kept.
    existing = list(
        db.scalars(
            select(Recommendation).where(
                Recommendation.student_id == student.id,
                Recommendation.academic_year_id == academic_year_id,
                Recommendation.status == "pending",
                Recommendation.generated_by == "rules",
            )
        )
    )
    for row in existing:
        db.delete(row)
    db.flush()

    created: List[Recommendation] = []
    for candidate in selected:
        topic = candidate.get("topic")
        quiz = candidate.get("quiz")
        resource = candidate.get("resource")
        recommendation = Recommendation(
            student_id=student.id,
            academic_year_id=academic_year_id,
            subject_id=candidate.get("subject_id"),
            topic_id=topic.id if topic else None,
            quiz_id=quiz.id if quiz else None,
            resource_id=resource.id if resource else None,
            kind=candidate["kind"],
            title=candidate["title"],
            reason=candidate["reason"],
            priority=round(float(candidate["priority"]), 3),
            estimated_minutes=int(candidate.get("estimated_minutes") or 20),
            action_label=candidate.get("action_label", "Start"),
            action_url=candidate.get("action_url", ""),
            status="pending",
            generated_by="rules",
        )
        db.add(recommendation)
        created.append(recommendation)
    db.flush()
    return created


def list_recommendations(
    db: Session, student_id: int, academic_year_id: int, limit: int = 10,
    status: str = "pending",
) -> List[Recommendation]:
    query = select(Recommendation).where(
        Recommendation.student_id == student_id,
        Recommendation.academic_year_id == academic_year_id,
    )
    if status != "all":
        query = query.where(Recommendation.status == status)
    return list(
        db.scalars(query.order_by(Recommendation.priority.desc(), Recommendation.id.desc()).limit(limit))
    )
