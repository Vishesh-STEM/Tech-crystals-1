"""Transparent topic/subject mastery + weak-topic detection.

The algorithm is deliberately explainable (every number can be traced back to
answers the student gave). ``app/ml`` defines interfaces so a trained model can
replace these rules later without touching the callers.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base_class import utcnow
from app.models import (
    ActivityEvent, Answer, Chapter, MasterySnapshot, Question, QuizAttempt,
    Student, StudentSubjectMastery, StudentTopicMastery, Subject, Topic,
)

DIFFICULTY_WEIGHT = {"easy": 0.8, "medium": 1.0, "hard": 1.3}
RECENT_WEIGHTS = (0.5, 0.3, 0.2)  # newest first
MASTERED_THRESHOLD = 80.0
WEAK_MASTERY_THRESHOLD = 50.0
MIN_QUESTIONS_FOR_WEAKNESS = 3


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _weighted_recent(scores: List[float]) -> float:
    """Weighted average of up to the three most recent scores (newest first)."""
    if not scores:
        return 0.0
    recent = scores[:3]
    weights = RECENT_WEIGHTS[: len(recent)]
    total_w = sum(weights)
    return sum(s * w for s, w in zip(recent, weights)) / total_w


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _answers_for_topic(
    db: Session, student_id: int, topic_id: int, academic_year_id: int
) -> List[Tuple[Answer, Question, QuizAttempt]]:
    rows = db.execute(
        select(Answer, Question, QuizAttempt)
        .join(Question, Answer.question_id == Question.id)
        .join(QuizAttempt, Answer.attempt_id == QuizAttempt.id)
        .where(
            QuizAttempt.student_id == student_id,
            QuizAttempt.academic_year_id == academic_year_id,
            QuizAttempt.status == "submitted",
            Question.topic_id == topic_id,
        )
        .order_by(QuizAttempt.submitted_at.asc(), Answer.id.asc())
    ).all()
    return [(r[0], r[1], r[2]) for r in rows]


# --------------------------------------------------------------------------
# topic mastery
# --------------------------------------------------------------------------
def recompute_topic_mastery(
    db: Session, student: Student, topic_id: int, academic_year_id: int
) -> Optional[StudentTopicMastery]:
    topic = db.get(Topic, topic_id)
    if topic is None:
        return None
    chapter = db.get(Chapter, topic.chapter_id)
    subject_id = chapter.subject_id if chapter else None

    record = db.scalar(
        select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student.id,
            StudentTopicMastery.topic_id == topic_id,
            StudentTopicMastery.academic_year_id == academic_year_id,
        )
    )
    if record is None:
        record = StudentTopicMastery(
            student_id=student.id,
            topic_id=topic_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
        )
        db.add(record)

    rows = _answers_for_topic(db, student.id, topic_id, academic_year_id)

    # ---- study engagement (resources opened / completed) ------------------
    engagement = db.execute(
        select(
            func.count(ActivityEvent.id),
            func.coalesce(func.sum(ActivityEvent.duration_seconds), 0),
            func.max(ActivityEvent.created_at),
        ).where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.topic_id == topic_id,
            ActivityEvent.academic_year_id == academic_year_id,
        )
    ).one()
    event_count, engagement_seconds, last_event_at = engagement
    study_minutes = int((engagement_seconds or 0) / 60)
    completed_resources = db.scalar(
        select(func.count(ActivityEvent.id)).where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.topic_id == topic_id,
            ActivityEvent.event_type == "completed_resource",
        )
    ) or 0

    if not rows:
        # Studied but never assessed -> low-confidence "exposure" mastery.
        exposure = _clamp(min(completed_resources, 3) * 8 + min(study_minutes, 30) * 0.2, 0, 30)
        record.mastery = round(exposure, 1)
        record.confidence = round(min(0.25, 0.05 * (event_count or 0)), 2)
        record.attempts = 0
        record.questions_answered = 0
        record.correct_answers = 0
        record.incorrect_answers = 0
        record.last_score = None
        record.average_score = None
        record.best_score = None
        record.trend = 0.0
        record.study_minutes = study_minutes
        record.is_weak = False
        record.weakness_confidence = "none"
        record.weakness_reason = (
            "Not assessed yet - take a quiz on this topic to measure your mastery."
            if event_count else ""
        )
        record.repeated_mistake_concepts = []
        record.last_activity_at = last_event_at
        return record

    # ---- per-attempt scores (newest first) --------------------------------
    per_attempt: Dict[int, Dict[str, Any]] = {}
    weighted_correct = 0.0
    weighted_total = 0.0
    mistakes: Dict[str, int] = {}
    seen_by_concept: Dict[str, int] = {}
    mistakes_by_attempt: Dict[int, set] = {}
    correct_total = 0

    for answer, question, attempt in rows:
        bucket = per_attempt.setdefault(
            attempt.id, {"correct": 0, "total": 0, "at": attempt.submitted_at or attempt.started_at}
        )
        bucket["total"] += 1
        weight = DIFFICULTY_WEIGHT.get(question.difficulty, 1.0)
        weighted_total += weight
        if answer.is_correct:
            bucket["correct"] += 1
            weighted_correct += weight
            correct_total += 1
        tag = (question.concept_tag or topic.name).strip()
        seen_by_concept[tag] = seen_by_concept.get(tag, 0) + 1
        if not answer.is_correct:
            mistakes[tag] = mistakes.get(tag, 0) + 1
            mistakes_by_attempt.setdefault(attempt.id, set()).add(tag)

    ordered_ids = sorted(
        per_attempt,
        key=lambda attempt_id: (per_attempt[attempt_id]["at"] or datetime.min),
        reverse=True,
    )
    latest_mistakes = mistakes_by_attempt.get(ordered_ids[0], set()) if ordered_ids else set()
    ordered = [per_attempt[attempt_id] for attempt_id in ordered_ids]
    scores = [round(100.0 * b["correct"] / b["total"], 1) for b in ordered if b["total"]]
    questions_answered = len(rows)
    incorrect_total = questions_answered - correct_total

    recent_score = _weighted_recent(scores)
    historical = sum(scores) / len(scores)
    difficulty_accuracy = 100.0 * (weighted_correct / weighted_total) if weighted_total else 0.0

    # 65% recency-weighted performance + 35% full history, then blended with a
    # difficulty-aware accuracy so hard questions count for more.
    base = 0.65 * recent_score + 0.35 * historical
    mastery = 0.75 * base + 0.25 * difficulty_accuracy

    # improvement / decline
    if len(scores) >= 2:
        older = scores[1:]
        trend = scores[0] - (sum(older) / len(older))
    else:
        trend = 0.0
    mastery += max(-6.0, min(8.0, trend * 0.15))

    # Repeated identical mistakes are a genuine understanding gap - but only
    # when the concept is missed *most* of the times it is asked AND it was
    # still wrong in the latest attempt. Two slips out of ten is not a weakness,
    # and a concept that has since been fixed must not haunt the student.
    repeated = sorted(
        [
            concept
            for concept, misses in mistakes.items()
            if misses >= 2
            and misses / max(1, seen_by_concept.get(concept, misses)) >= 0.5
            and concept in latest_mistakes
        ],
        key=lambda concept: -mistakes[concept],
    )
    mastery -= min(6.0, 2.0 * len(repeated))

    # engagement bonus (small, capped) - studying helps but does not fake mastery
    mastery += min(4.0, completed_resources * 1.5)

    # recency decay: knowledge fades if a topic is untouched
    last_attempt_at = ordered[0]["at"] if ordered else None
    reference = max([d for d in (last_attempt_at, last_event_at) if d], default=None)
    if reference:
        days_idle = (utcnow() - reference).days
        if days_idle > 14:
            mastery -= min(10.0, (days_idle - 14) / 7.0 * 2.5)

    mastery = _clamp(round(mastery, 1))
    confidence = min(1.0, (questions_answered / 12.0) * 0.7 + (len(scores) / 4.0) * 0.3)

    record.mastery = mastery
    record.confidence = round(confidence, 2)
    record.attempts = len(scores)
    record.questions_answered = questions_answered
    record.correct_answers = correct_total
    record.incorrect_answers = incorrect_total
    record.last_score = scores[0]
    record.average_score = round(historical, 1)
    record.best_score = max(scores)
    record.trend = round(trend, 1)
    record.study_minutes = study_minutes
    record.repeated_mistake_concepts = repeated
    record.last_activity_at = reference
    record.subject_id = subject_id

    level, reason = detect_weakness(
        mastery=mastery,
        scores=scores,
        average=historical,
        trend=trend,
        repeated=repeated,
        questions_answered=questions_answered,
        topic_name=topic.name,
    )
    record.weakness_confidence = level
    record.weakness_reason = reason
    record.is_weak = level in ("medium", "high")
    return record


def detect_weakness(
    *,
    mastery: float,
    scores: List[float],
    average: float,
    trend: float,
    repeated: List[str],
    questions_answered: int,
    topic_name: str,
) -> Tuple[str, str]:
    """Multi-signal weak-topic detection.

    Never flags a topic from a single bad question: at least
    ``MIN_QUESTIONS_FOR_WEAKNESS`` answered questions are required.
    """
    if questions_answered < MIN_QUESTIONS_FOR_WEAKNESS:
        return "none", "Not enough attempts yet to judge this topic."

    signals: List[Tuple[int, str]] = []
    if mastery < WEAK_MASTERY_THRESHOLD:
        signals.append((2, f"Your mastery score is {mastery:.0f}/100."))
    elif mastery < 65:
        signals.append((1, f"Your mastery score is {mastery:.0f}/100 - not consolidated yet."))

    if average < 50:
        signals.append((2, f"Your average score on this topic is {average:.0f}%."))
    elif average < 60:
        signals.append((1, f"Your average score on this topic is {average:.0f}%."))

    low_recent = [s for s in scores[:3] if s < 50]
    if len(scores) >= 3 and len(low_recent) == 3:
        signals.append((2, "You have scored below 50% in your last 3 attempts on this topic."))
    elif len(low_recent) >= 2:
        signals.append((1, f"{len(low_recent)} of your recent attempts were below 50%."))

    if trend < -10:
        signals.append((1, f"Your score dropped by {abs(trend):.0f} points since earlier attempts."))

    if repeated:
        shown = ", ".join(repeated[:2])
        signals.append((2, f"Repeated mistakes on {shown}."))

    total = sum(weight for weight, _ in signals)
    if total >= 5:
        level = "high"
    elif total >= 3:
        level = "medium"
    elif total >= 1:
        level = "low"
    else:
        return "none", f"{topic_name} looks healthy - keep revising periodically."

    reason = " ".join(text for _, text in signals[:3])
    return level, reason


# --------------------------------------------------------------------------
# subject mastery + snapshots
# --------------------------------------------------------------------------
def recompute_subject_mastery(
    db: Session, student: Student, subject_id: int, academic_year_id: int
) -> StudentSubjectMastery:
    record = db.scalar(
        select(StudentSubjectMastery).where(
            StudentSubjectMastery.student_id == student.id,
            StudentSubjectMastery.subject_id == subject_id,
            StudentSubjectMastery.academic_year_id == academic_year_id,
        )
    )
    if record is None:
        record = StudentSubjectMastery(
            student_id=student.id, subject_id=subject_id, academic_year_id=academic_year_id
        )
        db.add(record)

    topic_records = list(
        db.scalars(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id == student.id,
                StudentTopicMastery.subject_id == subject_id,
                StudentTopicMastery.academic_year_id == academic_year_id,
            )
        )
    )
    assessed = [t for t in topic_records if t.questions_answered > 0]
    if assessed:
        weights = [max(0.25, t.confidence or 0.25) for t in assessed]
        record.mastery = round(
            sum(t.mastery * w for t, w in zip(assessed, weights)) / sum(weights), 1
        )
    else:
        record.mastery = round(
            sum(t.mastery for t in topic_records) / len(topic_records), 1
        ) if topic_records else 0.0

    record.topics_started = len([t for t in topic_records if (t.study_minutes or 0) > 0 or t.questions_answered > 0])
    record.topics_mastered = len([t for t in assessed if t.mastery >= MASTERED_THRESHOLD])
    record.weak_topics = len([t for t in topic_records if t.is_weak])
    record.study_minutes = sum(t.study_minutes or 0 for t in topic_records)
    dates = [t.last_activity_at for t in topic_records if t.last_activity_at]
    record.last_activity_at = max(dates) if dates else None
    return record


def write_snapshot(
    db: Session,
    student: Student,
    academic_year_id: int,
    subject_id: Optional[int],
    mastery: float,
    when: Optional[datetime] = None,
    quizzes_taken: int = 0,
    study_minutes: int = 0,
) -> MasterySnapshot:
    when = when or utcnow()
    period = when.strftime("%Y-%m")
    snapshot = db.scalar(
        select(MasterySnapshot).where(
            MasterySnapshot.student_id == student.id,
            MasterySnapshot.subject_id.is_(subject_id) if subject_id is None
            else MasterySnapshot.subject_id == subject_id,
            MasterySnapshot.period == period,
        )
    )
    if snapshot is None:
        snapshot = MasterySnapshot(
            student_id=student.id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            period=period,
            created_at=when,
        )
        db.add(snapshot)
    snapshot.mastery = round(mastery, 1)
    snapshot.quizzes_taken = quizzes_taken or snapshot.quizzes_taken or 0
    snapshot.study_minutes = study_minutes or snapshot.study_minutes or 0
    return snapshot


def refresh_student_mastery(
    db: Session,
    student: Student,
    academic_year_id: int,
    topic_ids: Optional[Iterable[int]] = None,
    snapshot: bool = True,
) -> Dict[str, Any]:
    """Recompute mastery for the given topics (or every touched topic)."""
    if topic_ids is None:
        touched = set(
            db.scalars(
                select(StudentTopicMastery.topic_id).where(
                    StudentTopicMastery.student_id == student.id,
                    StudentTopicMastery.academic_year_id == academic_year_id,
                )
            )
        )
        touched.update(
            db.scalars(
                select(ActivityEvent.topic_id).where(
                    ActivityEvent.student_id == student.id,
                    ActivityEvent.topic_id.is_not(None),
                )
            )
        )
        topic_ids = [t for t in touched if t]

    updates: List[Dict[str, Any]] = []
    subjects: set[int] = set()
    for topic_id in topic_ids:
        record = recompute_topic_mastery(db, student, topic_id, academic_year_id)
        if record is None:
            continue
        if record.subject_id:
            subjects.add(record.subject_id)
        topic = db.get(Topic, topic_id)
        updates.append(
            {
                "topic_id": topic_id,
                "topic_name": topic.name if topic else "",
                "mastery": record.mastery,
                "is_weak": record.is_weak,
                "weakness_confidence": record.weakness_confidence,
                "reason": record.weakness_reason,
                "trend": record.trend,
            }
        )

    db.flush()
    overall_values: List[float] = []
    for subject_id in subjects:
        subject_record = recompute_subject_mastery(db, student, subject_id, academic_year_id)
        overall_values.append(subject_record.mastery)
        if snapshot:
            write_snapshot(db, student, academic_year_id, subject_id, subject_record.mastery)

    if snapshot and overall_values:
        write_snapshot(
            db, student, academic_year_id, None, sum(overall_values) / len(overall_values)
        )
    db.flush()
    return {"topics": updates, "subjects_updated": sorted(subjects)}


def overall_mastery(db: Session, student_id: int, academic_year_id: int) -> float:
    values = list(
        db.scalars(
            select(StudentSubjectMastery.mastery).where(
                StudentSubjectMastery.student_id == student_id,
                StudentSubjectMastery.academic_year_id == academic_year_id,
            )
        )
    )
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else 0.0


def weak_topics(
    db: Session, student_id: int, academic_year_id: int, limit: int = 10
) -> List[StudentTopicMastery]:
    return list(
        db.scalars(
            select(StudentTopicMastery)
            .where(
                StudentTopicMastery.student_id == student_id,
                StudentTopicMastery.academic_year_id == academic_year_id,
                StudentTopicMastery.is_weak.is_(True),
            )
            .order_by(StudentTopicMastery.mastery.asc())
            .limit(limit)
        )
    )


def monthly_progress(
    db: Session, student_id: int, academic_year_id: int, subject_id: Optional[int] = None,
    months: int = 6,
) -> List[Dict[str, Any]]:
    query = select(MasterySnapshot).where(
        MasterySnapshot.student_id == student_id,
        MasterySnapshot.academic_year_id == academic_year_id,
    )
    query = query.where(
        MasterySnapshot.subject_id.is_(None) if subject_id is None
        else MasterySnapshot.subject_id == subject_id
    )
    rows = list(db.scalars(query.order_by(MasterySnapshot.period.asc())))
    rows = rows[-months:]
    output = []
    for row in rows:
        year, month = row.period.split("-")
        label = datetime(int(year), int(month), 1).strftime("%b")
        output.append(
            {
                "period": row.period,
                "label": label,
                "mastery": row.mastery,
                "quizzes_taken": row.quizzes_taken,
                "study_minutes": row.study_minutes,
            }
        )
    return output
