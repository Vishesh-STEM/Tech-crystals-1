"""Curriculum browsing endpoints (subjects, chapters, topics, resources)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_active_year, get_current_student
from app.db.session import get_db
from app.models import (
    AcademicYear, Chapter, Question, Quiz, Resource, Student, StudentSubjectMastery,
    StudentTopicMastery, Subject, Topic,
)
from app.schemas.catalog import ChapterOut, ResourceOut, SubjectOut, TopicOut
from app.services.activity import log_event

router = APIRouter(tags=["catalog"])


def _topic_progress(
    db: Session, student_id: int, year_id: int, topic_ids: List[int]
) -> Dict[int, StudentTopicMastery]:
    if not topic_ids:
        return {}
    rows = db.scalars(
        select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.academic_year_id == year_id,
            StudentTopicMastery.topic_id.in_(topic_ids),
        )
    )
    return {row.topic_id: row for row in rows}


@router.get("/subjects", response_model=List[Dict[str, Any]])
def list_subjects(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> List[Dict[str, Any]]:
    subjects = list(db.scalars(select(Subject).where(Subject.is_active.is_(True)).order_by(Subject.order_index)))
    mastery = {
        row.subject_id: row
        for row in db.scalars(
            select(StudentSubjectMastery).where(
                StudentSubjectMastery.student_id == student.id,
                StudentSubjectMastery.academic_year_id == year.id,
            )
        )
    }
    payload: List[Dict[str, Any]] = []
    for subject in subjects:
        chapter_count = db.scalar(
            select(func.count(Chapter.id)).where(Chapter.subject_id == subject.id)
        ) or 0
        topic_count = db.scalar(
            select(func.count(Topic.id)).join(Chapter, Topic.chapter_id == Chapter.id)
            .where(Chapter.subject_id == subject.id)
        ) or 0
        record = mastery.get(subject.id)
        payload.append(
            {
                **SubjectOut.model_validate(subject).model_dump(),
                "chapter_count": chapter_count,
                "topic_count": topic_count,
                "mastery": record.mastery if record else 0.0,
                "topics_started": record.topics_started if record else 0,
                "topics_mastered": record.topics_mastered if record else 0,
                "weak_topics": record.weak_topics if record else 0,
                "last_activity_at": record.last_activity_at if record else None,
            }
        )
    return payload


@router.get("/subjects/{subject_id}", response_model=Dict[str, Any])
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    subject = db.get(Subject, subject_id)
    if subject is None or not subject.is_active:
        raise HTTPException(status_code=404, detail="Subject not found.")

    log_event(db, student, "opened_subject", subject_id=subject.id, academic_year_id=year.id)
    chapters_payload: List[Dict[str, Any]] = []
    all_topic_ids = [topic.id for chapter in subject.chapters for topic in chapter.topics]
    progress = _topic_progress(db, student.id, year.id, all_topic_ids)

    for chapter in subject.chapters:
        topic_ids = [topic.id for topic in chapter.topics]
        values = [progress[tid].mastery for tid in topic_ids if tid in progress]
        chapters_payload.append(
            {
                **ChapterOut.model_validate(chapter).model_dump(),
                "topic_count": len(topic_ids),
                "mastery": round(sum(values) / len(values), 1) if values else 0.0,
                "topics_started": len(values),
                "weak_topics": len([tid for tid in topic_ids if tid in progress and progress[tid].is_weak]),
            }
        )
    quiz_count = db.scalar(select(func.count(Quiz.id)).where(Quiz.subject_id == subject.id)) or 0
    record = db.scalar(
        select(StudentSubjectMastery).where(
            StudentSubjectMastery.student_id == student.id,
            StudentSubjectMastery.subject_id == subject.id,
            StudentSubjectMastery.academic_year_id == year.id,
        )
    )
    db.commit()
    return {
        **SubjectOut.model_validate(subject).model_dump(),
        "chapters": chapters_payload,
        "quiz_count": quiz_count,
        "mastery": record.mastery if record else 0.0,
        "weak_topics": record.weak_topics if record else 0,
        "topics_mastered": record.topics_mastered if record else 0,
    }


@router.get("/chapters/{chapter_id}", response_model=Dict[str, Any])
def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None or not chapter.is_active:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    subject = chapter.subject
    log_event(
        db, student, "opened_chapter", chapter_id=chapter.id, subject_id=subject.id,
        academic_year_id=year.id,
    )
    topic_ids = [topic.id for topic in chapter.topics]
    progress = _topic_progress(db, student.id, year.id, topic_ids)
    topics_payload = []
    for topic in chapter.topics:
        record = progress.get(topic.id)
        resource_count = db.scalar(
            select(func.count(Resource.id)).where(Resource.topic_id == topic.id)
        ) or 0
        topics_payload.append(
            {
                **TopicOut.model_validate(topic).model_dump(),
                "mastery": record.mastery if record else 0.0,
                "is_weak": record.is_weak if record else False,
                "attempts": record.attempts if record else 0,
                "resource_count": resource_count,
            }
        )
    quizzes = list(
        db.scalars(
            select(Quiz).where(Quiz.chapter_id == chapter.id, Quiz.is_published.is_(True))
        )
    )
    db.commit()
    return {
        **ChapterOut.model_validate(chapter).model_dump(),
        "subject": SubjectOut.model_validate(subject).model_dump(),
        "topics": topics_payload,
        "quizzes": [
            {"id": quiz.id, "title": quiz.title, "difficulty": quiz.difficulty,
             "time_limit_minutes": quiz.time_limit_minutes,
             "question_count": len(quiz.quiz_questions)}
            for quiz in quizzes
        ],
    }


@router.get("/topics/{topic_id}", response_model=Dict[str, Any])
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    topic = db.get(Topic, topic_id)
    if topic is None or not topic.is_active:
        raise HTTPException(status_code=404, detail="Topic not found.")
    chapter = topic.chapter
    subject = chapter.subject
    log_event(
        db, student, "opened_topic", topic_id=topic.id, chapter_id=chapter.id,
        subject_id=subject.id, academic_year_id=year.id, duration_seconds=0,
    )
    record = db.scalar(
        select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student.id,
            StudentTopicMastery.topic_id == topic.id,
            StudentTopicMastery.academic_year_id == year.id,
        )
    )
    resources = list(
        db.scalars(
            select(Resource).where(Resource.topic_id == topic.id, Resource.is_active.is_(True))
            .order_by(Resource.order_index)
        )
    )
    quizzes = list(
        db.scalars(
            select(Quiz).where(
                (Quiz.topic_id == topic.id) | (Quiz.chapter_id == chapter.id),
                Quiz.is_published.is_(True),
            )
        )
    )
    prerequisites = []
    for slug in topic.prerequisites or []:
        prerequisite = db.scalar(select(Topic).where(Topic.slug == slug))
        if prerequisite:
            prerequisite_record = db.scalar(
                select(StudentTopicMastery).where(
                    StudentTopicMastery.student_id == student.id,
                    StudentTopicMastery.topic_id == prerequisite.id,
                    StudentTopicMastery.academic_year_id == year.id,
                )
            )
            prerequisites.append(
                {
                    "id": prerequisite.id,
                    "name": prerequisite.name,
                    "mastery": prerequisite_record.mastery if prerequisite_record else 0.0,
                }
            )
    question_count = db.scalar(
        select(func.count(Question.id)).where(Question.topic_id == topic.id, Question.is_active.is_(True))
    ) or 0
    db.commit()
    return {
        **TopicOut.model_validate(topic).model_dump(),
        "chapter": ChapterOut.model_validate(chapter).model_dump(),
        "subject": SubjectOut.model_validate(subject).model_dump(),
        "resources": [ResourceOut.model_validate(resource).model_dump() for resource in resources],
        "quizzes": [
            {"id": quiz.id, "title": quiz.title, "question_count": len(quiz.quiz_questions),
             "time_limit_minutes": quiz.time_limit_minutes, "difficulty": quiz.difficulty}
            for quiz in quizzes
        ],
        "prerequisites": prerequisites,
        "question_count": question_count,
        "progress": {
            "mastery": record.mastery if record else 0.0,
            "attempts": record.attempts if record else 0,
            "questions_answered": record.questions_answered if record else 0,
            "average_score": record.average_score if record else None,
            "last_score": record.last_score if record else None,
            "trend": record.trend if record else 0.0,
            "is_weak": record.is_weak if record else False,
            "weakness_confidence": record.weakness_confidence if record else "none",
            "weakness_reason": record.weakness_reason if record else "",
            "study_minutes": record.study_minutes if record else 0,
        },
    }


@router.get("/topics/{topic_id}/resources", response_model=List[ResourceOut])
def topic_resources(
    topic_id: int,
    type: Optional[str] = Query(default=None, pattern="^(text|visual|audio|practice)$"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[ResourceOut]:
    if db.get(Topic, topic_id) is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    query = select(Resource).where(Resource.topic_id == topic_id, Resource.is_active.is_(True))
    if type:
        query = query.where(Resource.type == type)
    resources = list(db.scalars(query.order_by(Resource.order_index)))
    return [ResourceOut.model_validate(resource) for resource in resources]


@router.get("/topics/{topic_id}/questions", response_model=List[Dict[str, Any]])
def topic_questions(
    topic_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> List[Dict[str, Any]]:
    """Practice questions for a topic (answers included - this is practice, not a graded quiz)."""
    if db.get(Topic, topic_id) is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    questions = list(
        db.scalars(
            select(Question)
            .where(Question.topic_id == topic_id, Question.is_active.is_(True))
            .order_by(Question.difficulty, Question.id)
            .limit(limit)
        )
    )
    return [
        {
            "id": question.id,
            "text": question.text,
            "options": question.options,
            "difficulty": question.difficulty,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "concept_tag": question.concept_tag,
        }
        for question in questions
    ]


@router.get("/resources/{resource_id}", response_model=Dict[str, Any])
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
    year: AcademicYear = Depends(get_active_year),
) -> Dict[str, Any]:
    resource = db.get(Resource, resource_id)
    if resource is None or not resource.is_active:
        raise HTTPException(status_code=404, detail="Resource not found.")
    log_event(
        db, student, "opened_resource", resource_id=resource.id, resource_type=resource.type,
        academic_year_id=year.id,
    )
    log_event(
        db, student, f"selected_{resource.type}", resource_id=resource.id,
        resource_type=resource.type, academic_year_id=year.id,
    )
    db.commit()
    topic = resource.topic
    return {
        **ResourceOut.model_validate(resource).model_dump(),
        "topic": {"id": topic.id, "name": topic.name} if topic else None,
    }
