"""Quiz endpoints: browse, start an attempt, submit and review."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_active_year, get_current_student
from app.db.session import get_db
from app.models import AcademicYear, Answer, Chapter, Question, Quiz, QuizAttempt, Student, Subject, Topic
from app.schemas.assessment import AttemptResult, AttemptSubmit, QuestionOut
from app.services.quiz import quiz_questions, start_attempt, submit_attempt

router = APIRouter(tags=["quizzes"])


def _get_quiz(db: Session, quiz_id: int) -> Quiz:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None or not quiz.is_published:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz


@router.get("/quizzes", response_model=List[Dict[str, Any]])
def list_quizzes(
    subject_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[Dict[str, Any]]:
    query = select(Quiz).where(Quiz.is_published.is_(True))
    if subject_id:
        query = query.where(Quiz.subject_id == subject_id)
    if chapter_id:
        query = query.where(Quiz.chapter_id == chapter_id)
    if topic_id:
        query = query.where(Quiz.topic_id == topic_id)
    quizzes = list(db.scalars(query.order_by(Quiz.subject_id, Quiz.id).limit(limit)))

    payload = []
    for quiz in quizzes:
        best = db.scalar(
            select(func.max(QuizAttempt.accuracy)).where(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.student_id == student.id,
                QuizAttempt.status == "submitted",
            )
        )
        attempts = db.scalar(
            select(func.count(QuizAttempt.id)).where(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.student_id == student.id,
                QuizAttempt.status == "submitted",
            )
        ) or 0
        subject = db.get(Subject, quiz.subject_id)
        payload.append(
            {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "subject_id": quiz.subject_id,
                "subject_name": subject.name if subject else "",
                "icon": subject.icon if subject else "📘",
                "color": subject.color if subject else "indigo",
                "chapter_id": quiz.chapter_id,
                "topic_id": quiz.topic_id,
                "difficulty": quiz.difficulty,
                "time_limit_minutes": quiz.time_limit_minutes,
                "question_count": len(quiz.quiz_questions),
                "best_score": best,
                "attempts_count": attempts,
            }
        )
    return payload


@router.get("/quiz/{quiz_id}", response_model=Dict[str, Any])
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Dict[str, Any]:
    quiz = _get_quiz(db, quiz_id)
    questions = quiz_questions(db, quiz)
    subject = db.get(Subject, quiz.subject_id)
    chapter = db.get(Chapter, quiz.chapter_id) if quiz.chapter_id else None
    topic = db.get(Topic, quiz.topic_id) if quiz.topic_id else None
    attempts = list(
        db.scalars(
            select(QuizAttempt)
            .where(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.student_id == student.id,
                QuizAttempt.status == "submitted",
            )
            .order_by(QuizAttempt.submitted_at.desc())
            .limit(5)
        )
    )
    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "subject_id": quiz.subject_id,
        "subject_name": subject.name if subject else "",
        "icon": subject.icon if subject else "📘",
        "color": subject.color if subject else "indigo",
        "chapter_name": chapter.name if chapter else None,
        "topic_name": topic.name if topic else None,
        "difficulty": quiz.difficulty,
        "time_limit_minutes": quiz.time_limit_minutes,
        "pass_percentage": quiz.pass_percentage,
        "question_count": len(questions),
        "questions": [QuestionOut.model_validate(question).model_dump() for question in questions],
        "previous_attempts": [
            {
                "id": attempt.id,
                "attempt_number": attempt.attempt_number,
                "accuracy": attempt.accuracy,
                "score": attempt.score,
                "max_score": attempt.max_score,
                "submitted_at": attempt.submitted_at,
            }
            for attempt in attempts
        ],
    }


@router.post("/quiz/{quiz_id}/attempt", response_model=Dict[str, Any])
def create_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    quiz = _get_quiz(db, quiz_id)
    attempt = start_attempt(db, student, quiz, year)
    questions = quiz_questions(db, quiz)
    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "attempt_number": attempt.attempt_number,
        "started_at": attempt.started_at,
        "time_limit_minutes": quiz.time_limit_minutes,
        "questions": [QuestionOut.model_validate(question).model_dump() for question in questions],
    }


@router.post("/quiz/{quiz_id}/attempt/{attempt_id}/submit", response_model=AttemptResult)
def submit(
    quiz_id: int,
    attempt_id: int,
    payload: AttemptSubmit,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> AttemptResult:
    quiz = _get_quiz(db, quiz_id)
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None or attempt.quiz_id != quiz.id:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    if attempt.student_id != student.id:
        raise HTTPException(status_code=403, detail="This attempt belongs to another student.")
    result = submit_attempt(
        db, student, quiz, attempt,
        [answer.model_dump() for answer in payload.answers],
        payload.duration_seconds, year,
    )
    return AttemptResult(**result)


@router.get("/attempts/{attempt_id}", response_model=Dict[str, Any])
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Dict[str, Any]:
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    if attempt.student_id != student.id:
        raise HTTPException(status_code=403, detail="This attempt belongs to another student.")
    quiz = db.get(Quiz, attempt.quiz_id)
    answers = list(db.scalars(select(Answer).where(Answer.attempt_id == attempt.id)))
    review = []
    for answer in answers:
        question = db.get(Question, answer.question_id)
        topic = db.get(Topic, question.topic_id) if question else None
        review.append(
            {
                "question_id": answer.question_id,
                "question_text": question.text if question else "",
                "options": question.options if question else [],
                "given_answer": answer.given_answer,
                "correct_answer": question.correct_answer if question else "",
                "is_correct": answer.is_correct,
                "explanation": question.explanation if question else "",
                "difficulty": question.difficulty if question else "medium",
                "topic_id": question.topic_id if question else None,
                "topic_name": topic.name if topic else "",
                "concept_tag": question.concept_tag if question else "",
            }
        )
    return {
        "attempt_id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "quiz_title": quiz.title if quiz else "",
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "accuracy": attempt.accuracy,
        "passed": attempt.accuracy >= (quiz.pass_percentage if quiz else 60),
        "duration_seconds": attempt.duration_seconds,
        "submitted_at": attempt.submitted_at,
        "topic_breakdown": attempt.topic_breakdown or {},
        "difficulty_breakdown": attempt.difficulty_breakdown or {},
        "answers": review,
    }
