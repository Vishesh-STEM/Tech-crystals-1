"""Quiz attempt lifecycle: start, grade, and update every downstream analytic."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base_class import utcnow
from app.models import (
    AcademicYear, Answer, Question, Quiz, QuizAttempt, Student, Topic,
)
from app.services.activity import log_event
from app.services.learning_profile import compute_learning_profile
from app.services.mastery import refresh_student_mastery
from app.services.recommendations import generate_recommendations


def _normalise(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def is_answer_correct(question: Question, given: str) -> bool:
    given_clean = _normalise(given)
    if not given_clean:
        return False
    correct = _normalise(question.correct_answer)
    if given_clean == correct:
        return True
    # accept the bare option letter ("b") for a labelled option ("B. ...")
    if len(given_clean) == 1 and correct[:1] == given_clean and correct[1:2] in (".", ")"):
        return True
    # accept the option text without its "A. " label
    if "." in correct[:3] and _normalise(correct.split(".", 1)[1]) == given_clean:
        return True
    if question.type == "numeric":
        try:
            return abs(float(given_clean) - float(correct)) < 1e-6
        except ValueError:
            return False
    return False


def quiz_questions(db: Session, quiz: Quiz) -> List[Question]:
    return [link.question for link in quiz.quiz_questions if link.question and link.question.is_active]


def start_attempt(db: Session, student: Student, quiz: Quiz, year: AcademicYear) -> QuizAttempt:
    questions = quiz_questions(db, quiz)
    if not questions:
        raise HTTPException(status_code=400, detail="This quiz has no questions yet.")

    previous = db.scalar(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.student_id == student.id,
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.status == "submitted",
        )
    ) or 0
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=student.id,
        academic_year_id=year.id,
        attempt_number=previous + 1,
        status="in_progress",
        started_at=utcnow(),
        max_score=float(sum(question.marks or 1 for question in questions)),
    )
    db.add(attempt)
    db.flush()
    log_event(
        db, student, "retook_quiz" if previous else "started_quiz",
        subject_id=quiz.subject_id, chapter_id=quiz.chapter_id, topic_id=quiz.topic_id,
        academic_year_id=year.id, details={"quiz_id": quiz.id, "attempt_id": attempt.id},
    )
    db.commit()
    db.refresh(attempt)
    return attempt


def submit_attempt(
    db: Session,
    student: Student,
    quiz: Quiz,
    attempt: QuizAttempt,
    answers: List[Dict[str, Any]],
    duration_seconds: int,
    year: AcademicYear,
) -> Dict[str, Any]:
    if attempt.status == "submitted":
        raise HTTPException(status_code=409, detail="This attempt has already been submitted.")

    questions = {question.id: question for question in quiz_questions(db, quiz)}
    given_by_question = {
        int(item["question_id"]): item for item in answers if item.get("question_id") in questions
    }

    correct_count = 0
    score = 0.0
    max_score = 0.0
    review: List[Dict[str, Any]] = []
    topic_stats: Dict[str, Dict[str, Any]] = {}
    difficulty_stats: Dict[str, Dict[str, Any]] = {}
    touched_topics = set()

    for question_id, question in questions.items():
        payload = given_by_question.get(question_id, {})
        given = str(payload.get("answer", ""))
        time_spent = int(payload.get("time_spent_seconds", 0) or 0)
        correct = is_answer_correct(question, given)
        marks = float(question.marks or 1)
        max_score += marks
        if correct:
            correct_count += 1
            score += marks

        db.add(
            Answer(
                attempt_id=attempt.id,
                question_id=question.id,
                given_answer=given[:500],
                is_correct=correct,
                marks_awarded=marks if correct else 0.0,
                time_spent_seconds=time_spent,
            )
        )
        touched_topics.add(question.topic_id)
        topic = db.get(Topic, question.topic_id)
        bucket = topic_stats.setdefault(
            str(question.topic_id), {"topic": topic.name if topic else "", "correct": 0, "total": 0}
        )
        bucket["total"] += 1
        bucket["correct"] += 1 if correct else 0
        dbucket = difficulty_stats.setdefault(question.difficulty, {"correct": 0, "total": 0})
        dbucket["total"] += 1
        dbucket["correct"] += 1 if correct else 0

        log_event(
            db, student, "attempted_question", topic_id=question.topic_id,
            academic_year_id=year.id, duration_seconds=time_spent,
            result="correct" if correct else "incorrect",
            details={"question_id": question.id, "difficulty": question.difficulty},
        )
        log_event(
            db, student, "correct_answer" if correct else "incorrect_answer",
            topic_id=question.topic_id, academic_year_id=year.id,
            result="correct" if correct else "incorrect",
            details={"question_id": question.id, "concept": question.concept_tag},
        )

        review.append(
            {
                "question_id": question.id,
                "question_text": question.text,
                "options": question.options or [],
                "given_answer": given,
                "correct_answer": question.correct_answer,
                "is_correct": correct,
                "explanation": question.explanation or "",
                "difficulty": question.difficulty,
                "topic_id": question.topic_id,
                "topic_name": topic.name if topic else "",
                "concept_tag": question.concept_tag or "",
            }
        )

    total_questions = len(questions)
    accuracy = round(100.0 * correct_count / total_questions, 1) if total_questions else 0.0
    for bucket in topic_stats.values():
        bucket["accuracy"] = round(100.0 * bucket["correct"] / bucket["total"], 1) if bucket["total"] else 0.0
    for bucket in difficulty_stats.values():
        bucket["accuracy"] = round(100.0 * bucket["correct"] / bucket["total"], 1) if bucket["total"] else 0.0

    attempt.status = "submitted"
    attempt.submitted_at = utcnow()
    attempt.duration_seconds = max(0, int(duration_seconds or 0))
    attempt.score = score
    attempt.max_score = max_score
    attempt.accuracy = accuracy
    attempt.topic_breakdown = topic_stats
    attempt.difficulty_breakdown = difficulty_stats

    log_event(
        db, student, "completed_quiz" if attempt.attempt_number == 1 else "retook_quiz",
        subject_id=quiz.subject_id, chapter_id=quiz.chapter_id,
        topic_id=quiz.topic_id or (sorted(touched_topics)[0] if touched_topics else None),
        academic_year_id=year.id, duration_seconds=attempt.duration_seconds, score=accuracy,
        result=f"{correct_count}/{total_questions}",
        details={"quiz_id": quiz.id, "attempt_id": attempt.id, "attempt_number": attempt.attempt_number},
    )
    db.flush()

    # ---- downstream analytics (this is the "mastery updated" step) --------
    mastery_result = refresh_student_mastery(db, student, year.id, topic_ids=list(touched_topics))
    compute_learning_profile(db, student, year.id)
    db.flush()
    recommendations = generate_recommendations(db, student, year.id)
    db.commit()

    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "attempt_number": attempt.attempt_number,
        "score": score,
        "max_score": max_score,
        "accuracy": accuracy,
        "passed": accuracy >= (quiz.pass_percentage or 60),
        "duration_seconds": attempt.duration_seconds,
        "submitted_at": attempt.submitted_at,
        "topic_breakdown": topic_stats,
        "difficulty_breakdown": difficulty_stats,
        "answers": review,
        "mastery_updates": mastery_result["topics"],
        "new_recommendations": [
            {
                "id": recommendation.id,
                "kind": recommendation.kind,
                "title": recommendation.title,
                "reason": recommendation.reason,
                "priority": recommendation.priority,
                "action_url": recommendation.action_url,
            }
            for recommendation in recommendations[:4]
        ],
    }
