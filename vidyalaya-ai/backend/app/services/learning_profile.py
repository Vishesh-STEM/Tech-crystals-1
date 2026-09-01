"""Adaptive resource-effectiveness profile.

This is NOT a fixed psychological "learning style" label. For every study
format (text / visual / audio / practice) we measure how the student actually
performs on quizzes taken shortly after using that format, and blend it with a
neutral prior so a single lucky (or unlucky) quiz cannot dominate.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base_class import utcnow
from app.models import (
    ActivityEvent, Answer, Question, QuizAttempt, Student, StudentLearningProfile,
)
from app.services.activity import streak_days

FORMATS = ("text", "visual", "audio", "practice")
PRIOR_WEIGHT = 2.0          # neutral evidence, keeps early numbers honest
PRIOR_VALUE = 0.5
FOLLOW_UP_WINDOW_DAYS = 7
COMPLETION_WEIGHT = {"completed_resource": 1.0, "opened_resource": 0.6}


def _blend(values: List[float], weights: List[float]) -> float:
    numerator = PRIOR_VALUE * PRIOR_WEIGHT + sum(v * w for v, w in zip(values, weights))
    denominator = PRIOR_WEIGHT + sum(weights)
    return numerator / denominator if denominator else PRIOR_VALUE


def compute_learning_profile(
    db: Session, student: Student, academic_year_id: int, persist: bool = True
) -> StudentLearningProfile:
    record = db.scalar(
        select(StudentLearningProfile).where(
            StudentLearningProfile.student_id == student.id,
            StudentLearningProfile.academic_year_id == academic_year_id,
        )
    )
    if record is None:
        record = StudentLearningProfile(
            student_id=student.id, academic_year_id=academic_year_id
        )
        if persist:
            db.add(record)

    # --- all graded answers (topic, time, correctness) --------------------
    answer_rows = db.execute(
        select(Question.topic_id, QuizAttempt.submitted_at, Answer.is_correct, Question.difficulty)
        .join(Answer, Answer.question_id == Question.id)
        .join(QuizAttempt, Answer.attempt_id == QuizAttempt.id)
        .where(
            QuizAttempt.student_id == student.id,
            QuizAttempt.academic_year_id == academic_year_id,
            QuizAttempt.status == "submitted",
        )
    ).all()

    by_topic: Dict[int, List[Any]] = {}
    for topic_id, submitted_at, is_correct, difficulty in answer_rows:
        if topic_id is None or submitted_at is None:
            continue
        by_topic.setdefault(topic_id, []).append((submitted_at, bool(is_correct), difficulty))

    # --- resource usage events -------------------------------------------
    usage_rows = db.execute(
        select(
            ActivityEvent.resource_type,
            ActivityEvent.topic_id,
            ActivityEvent.created_at,
            ActivityEvent.event_type,
            ActivityEvent.duration_seconds,
        ).where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.academic_year_id == academic_year_id,
            ActivityEvent.resource_type.in_(FORMATS),
            ActivityEvent.event_type.in_(tuple(COMPLETION_WEIGHT)),
        )
    ).all()

    values: Dict[str, List[float]] = {fmt: [] for fmt in FORMATS}
    weights: Dict[str, List[float]] = {fmt: [] for fmt in FORMATS}
    samples: Dict[str, int] = {fmt: 0 for fmt in FORMATS}
    minutes: Dict[str, int] = {fmt: 0 for fmt in FORMATS}
    followups: Dict[str, int] = {fmt: 0 for fmt in FORMATS}

    for fmt, topic_id, created_at, event_type, duration in usage_rows:
        if fmt not in FORMATS:
            continue
        samples[fmt] += 1
        minutes[fmt] += int((duration or 0) / 60)
        if topic_id is None or created_at is None:
            continue
        window_end = created_at + timedelta(days=FOLLOW_UP_WINDOW_DAYS)
        after = [
            correct
            for submitted_at, correct, _difficulty in by_topic.get(topic_id, [])
            if created_at <= submitted_at <= window_end
        ]
        if not after:
            continue
        accuracy = sum(1 for c in after if c) / len(after)
        weight = COMPLETION_WEIGHT.get(event_type, 0.6) * min(2.0, 0.5 + len(after) / 4.0)
        values[fmt].append(accuracy)
        weights[fmt].append(weight)
        followups[fmt] += 1

    effectiveness = {fmt: _blend(values[fmt], weights[fmt]) for fmt in FORMATS}

    # Repeated usage of a format that keeps producing results is a small
    # positive signal; heavy usage with no follow-up evidence is neutral.
    for fmt in FORMATS:
        if followups[fmt] >= 3:
            effectiveness[fmt] = min(1.0, effectiveness[fmt] + 0.02 * min(followups[fmt], 5))

    record.text_effectiveness = round(effectiveness["text"], 3)
    record.visual_effectiveness = round(effectiveness["visual"], 3)
    record.audio_effectiveness = round(effectiveness["audio"], 3)
    record.practice_effectiveness = round(effectiveness["practice"], 3)
    record.text_samples = samples["text"]
    record.visual_samples = samples["visual"]
    record.audio_samples = samples["audio"]
    record.practice_samples = samples["practice"]

    # --- preferred difficulty --------------------------------------------
    difficulty_stats: Dict[str, List[int]] = {}
    for _topic_id, _submitted_at, is_correct, difficulty in answer_rows:
        bucket = difficulty_stats.setdefault(difficulty or "medium", [0, 0])
        bucket[1] += 1
        if is_correct:
            bucket[0] += 1
    best_difficulty = "medium"
    best_accuracy = -1.0
    for difficulty, (correct, total) in difficulty_stats.items():
        if total >= 3:
            accuracy = correct / total
            if accuracy > best_accuracy:
                best_accuracy, best_difficulty = accuracy, difficulty
    record.preferred_difficulty = best_difficulty

    # --- study rhythm -----------------------------------------------------
    day_minutes: Dict[Any, int] = {}
    for created_at, duration in db.execute(
        select(ActivityEvent.created_at, ActivityEvent.duration_seconds).where(
            ActivityEvent.student_id == student.id,
            ActivityEvent.academic_year_id == academic_year_id,
        )
    ).all():
        if not created_at:
            continue
        day_minutes[created_at.date()] = day_minutes.get(created_at.date(), 0) + int((duration or 0) / 60)
    record.average_session_minutes = round(
        sum(day_minutes.values()) / len(day_minutes), 1
    ) if day_minutes else 0.0
    record.study_streak_days = streak_days(db, student.id)
    record.evidence = {
        "follow_up_quizzes": followups,
        "minutes_by_format": minutes,
        "difficulty_accuracy": {
            k: round(v[0] / v[1], 2) for k, v in difficulty_stats.items() if v[1]
        },
        "window_days": FOLLOW_UP_WINDOW_DAYS,
    }
    record.last_computed_at = utcnow()
    return record


def profile_payload(record: StudentLearningProfile) -> Dict[str, Any]:
    scores = {
        "text": record.text_effectiveness or 0.5,
        "visual": record.visual_effectiveness or 0.5,
        "audio": record.audio_effectiveness or 0.5,
        "practice": record.practice_effectiveness or 0.5,
    }
    strongest = max(scores, key=lambda k: scores[k])
    weakest = min(scores, key=lambda k: scores[k])
    return {
        "text_effectiveness": scores["text"],
        "visual_effectiveness": scores["visual"],
        "audio_effectiveness": scores["audio"],
        "practice_effectiveness": scores["practice"],
        "samples": {
            "text": record.text_samples or 0,
            "visual": record.visual_samples or 0,
            "audio": record.audio_samples or 0,
            "practice": record.practice_samples or 0,
        },
        "strongest_format": strongest,
        "weakest_format": weakest,
        "preferred_difficulty": record.preferred_difficulty or "medium",
        "average_session_minutes": record.average_session_minutes or 0.0,
        "study_streak_days": record.study_streak_days or 0,
        "evidence": record.evidence or {},
    }


def get_or_create_profile(
    db: Session, student: Student, academic_year_id: int
) -> StudentLearningProfile:
    record = db.scalar(
        select(StudentLearningProfile).where(
            StudentLearningProfile.student_id == student.id,
            StudentLearningProfile.academic_year_id == academic_year_id,
        )
    )
    if record is None:
        record = compute_learning_profile(db, student, academic_year_id)
        db.flush()
    return record
