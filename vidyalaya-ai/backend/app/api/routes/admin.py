"""Teacher / admin endpoints: class analytics and full content CRUD (RBAC protected)."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.rag import index_content
from app.api.deps import require_staff
from app.core.utils import slugify, unique_slug
from app.db.base_class import utcnow
from app.db.session import get_db
from app.integrations.moodle import integration_status
from app.ml.predictors import active_models
from app.models import (
    AcademicYear, ActivityEvent, Chapter, Question, Quiz, QuizAttempt, QuizQuestion,
    Resource, Student, StudentSubjectMastery, StudentTopicMastery, Subject, Topic, User,
)
from app.schemas.assessment import (
    QuestionAdminOut, QuestionCreate, QuestionUpdate, QuizCreate, QuizOut, QuizUpdate,
)
from app.schemas.catalog import (
    ChapterCreate, ChapterOut, ChapterUpdate, ResourceCreate, ResourceOut, ResourceUpdate,
    SubjectCreate, SubjectOut, SubjectUpdate, TopicCreate, TopicOut, TopicUpdate,
)
from app.schemas.common import Message
from app.services.academic import get_current_year

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_staff)])


# --------------------------------------------------------------------------
# analytics
# --------------------------------------------------------------------------
@router.get("/analytics", response_model=Dict[str, Any])
def analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    year = get_current_year(db)
    student_count = db.scalar(select(func.count(Student.id))) or 0

    subject_rows = db.execute(
        select(
            Subject.id, Subject.name, Subject.icon, Subject.color,
            func.avg(StudentSubjectMastery.mastery), func.count(StudentSubjectMastery.id),
        )
        .join(StudentSubjectMastery, StudentSubjectMastery.subject_id == Subject.id, isouter=True)
        .group_by(Subject.id)
        .order_by(Subject.order_index)
    ).all()
    subject_performance = [
        {
            "subject_id": row[0],
            "subject_name": row[1],
            "icon": row[2],
            "color": row[3],
            "average_mastery": round(float(row[4]), 1) if row[4] is not None else 0.0,
            "students_tracked": int(row[5] or 0),
        }
        for row in subject_rows
    ]
    class_average = (
        round(sum(item["average_mastery"] for item in subject_performance) / len(subject_performance), 1)
        if subject_performance else 0.0
    )

    weak_rows = db.execute(
        select(
            Topic.id, Topic.name, Subject.name,
            func.count(StudentTopicMastery.id), func.avg(StudentTopicMastery.mastery),
        )
        .join(StudentTopicMastery, StudentTopicMastery.topic_id == Topic.id)
        .join(Subject, StudentTopicMastery.subject_id == Subject.id)
        .where(StudentTopicMastery.is_weak.is_(True))
        .group_by(Topic.id, Topic.name, Subject.name)
        .order_by(func.count(StudentTopicMastery.id).desc())
        .limit(8)
    ).all()
    weak_topics = [
        {
            "topic_id": row[0],
            "topic_name": row[1],
            "subject_name": row[2],
            "students_affected": int(row[3]),
            "average_mastery": round(float(row[4]), 1) if row[4] is not None else 0.0,
        }
        for row in weak_rows
    ]

    attempts = list(db.scalars(select(QuizAttempt).where(QuizAttempt.status == "submitted")))
    accuracies = [attempt.accuracy for attempt in attempts]
    quiz_stats = {
        "attempts": len(attempts),
        "average_accuracy": round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0,
        "pass_rate": round(100.0 * len([a for a in accuracies if a >= 60]) / len(accuracies), 1) if accuracies else 0.0,
        "quizzes_published": db.scalar(select(func.count(Quiz.id)).where(Quiz.is_published.is_(True))) or 0,
        "questions": db.scalar(select(func.count(Question.id))) or 0,
    }

    since = utcnow() - timedelta(days=14)
    activity_rows = db.execute(
        select(func.date(ActivityEvent.created_at), func.count(ActivityEvent.id))
        .where(ActivityEvent.created_at >= since)
        .group_by(func.date(ActivityEvent.created_at))
        .order_by(func.date(ActivityEvent.created_at))
    ).all()

    recent_rows = list(
        db.scalars(
            select(ActivityEvent).order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc()).limit(15)
        )
    )
    recent_activity = []
    for event in recent_rows:
        student = db.get(Student, event.student_id)
        topic = db.get(Topic, event.topic_id) if event.topic_id else None
        recent_activity.append(
            {
                "id": event.id,
                "student_name": student.user.full_name if student and student.user else "",
                "event_type": event.event_type,
                "topic_name": topic.name if topic else "",
                "result": event.result,
                "score": event.score,
                "created_at": event.created_at,
            }
        )

    top_rows = db.execute(
        select(Student.id, func.avg(StudentSubjectMastery.mastery))
        .join(StudentSubjectMastery, StudentSubjectMastery.student_id == Student.id)
        .group_by(Student.id)
        .order_by(func.avg(StudentSubjectMastery.mastery).desc())
        .limit(5)
    ).all()
    leaderboard = []
    for student_id, average in top_rows:
        student = db.get(Student, student_id)
        leaderboard.append(
            {
                "student_id": student_id,
                "name": student.user.full_name if student and student.user else "",
                "mastery": round(float(average or 0), 1),
            }
        )

    return {
        "academic_year": year.label,
        "students": student_count,
        "teachers": db.scalar(select(func.count(User.id)).where(User.role.in_(("teacher", "admin")))) or 0,
        "class_average": class_average,
        "subject_performance": subject_performance,
        "common_weak_topics": weak_topics,
        "quiz_stats": quiz_stats,
        "activity_trend": [{"date": str(row[0]), "events": int(row[1])} for row in activity_rows],
        "recent_activity": recent_activity,
        "leaderboard": leaderboard,
        "catalog": {
            "subjects": db.scalar(select(func.count(Subject.id))) or 0,
            "chapters": db.scalar(select(func.count(Chapter.id))) or 0,
            "topics": db.scalar(select(func.count(Topic.id))) or 0,
            "resources": db.scalar(select(func.count(Resource.id))) or 0,
        },
        "ml_models": active_models(),
        "moodle": integration_status(),
    }


@router.get("/students", response_model=List[Dict[str, Any]])
def list_students(
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    query = select(Student).join(User, Student.user_id == User.id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where((User.full_name.ilike(pattern)) | (User.email.ilike(pattern)))
    students = list(db.scalars(query.limit(limit)))
    payload = []
    for student in students:
        averages = list(
            db.scalars(
                select(StudentSubjectMastery.mastery).where(
                    StudentSubjectMastery.student_id == student.id
                )
            )
        )
        weak = db.scalar(
            select(func.count(StudentTopicMastery.id)).where(
                StudentTopicMastery.student_id == student.id, StudentTopicMastery.is_weak.is_(True)
            )
        ) or 0
        attempts = db.scalar(
            select(func.count(QuizAttempt.id)).where(
                QuizAttempt.student_id == student.id, QuizAttempt.status == "submitted"
            )
        ) or 0
        last_event = db.scalar(
            select(func.max(ActivityEvent.created_at)).where(ActivityEvent.student_id == student.id)
        )
        payload.append(
            {
                "id": student.id,
                "name": student.user.full_name if student.user else "",
                "email": student.user.email if student.user else "",
                "class_level": student.class_level,
                "roll_number": student.roll_number,
                "overall_mastery": round(sum(averages) / len(averages), 1) if averages else 0.0,
                "weak_topics": weak,
                "quizzes_taken": attempts,
                "last_active_at": last_event,
            }
        )
    payload.sort(key=lambda item: item["overall_mastery"], reverse=True)
    return payload


@router.get("/students/{student_id}", response_model=Dict[str, Any])
def student_detail(student_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    subjects = []
    for row in db.scalars(
        select(StudentSubjectMastery).where(StudentSubjectMastery.student_id == student.id)
    ):
        subject = db.get(Subject, row.subject_id)
        subjects.append(
            {
                "subject_id": row.subject_id,
                "subject_name": subject.name if subject else "",
                "icon": subject.icon if subject else "📘",
                "mastery": row.mastery,
                "weak_topics": row.weak_topics,
                "topics_mastered": row.topics_mastered,
            }
        )
    weak = []
    for row in db.scalars(
        select(StudentTopicMastery)
        .where(StudentTopicMastery.student_id == student.id, StudentTopicMastery.is_weak.is_(True))
        .order_by(StudentTopicMastery.mastery)
        .limit(10)
    ):
        topic = db.get(Topic, row.topic_id)
        weak.append(
            {
                "topic_id": row.topic_id,
                "topic_name": topic.name if topic else "",
                "mastery": row.mastery,
                "weakness_reason": row.weakness_reason,
                "weakness_confidence": row.weakness_confidence,
            }
        )
    attempts = []
    for attempt in db.scalars(
        select(QuizAttempt)
        .where(QuizAttempt.student_id == student.id, QuizAttempt.status == "submitted")
        .order_by(QuizAttempt.submitted_at.desc())
        .limit(10)
    ):
        quiz = db.get(Quiz, attempt.quiz_id)
        attempts.append(
            {
                "attempt_id": attempt.id,
                "quiz_title": quiz.title if quiz else "",
                "accuracy": attempt.accuracy,
                "submitted_at": attempt.submitted_at,
            }
        )
    return {
        "id": student.id,
        "name": student.user.full_name if student.user else "",
        "email": student.user.email if student.user else "",
        "class_level": student.class_level,
        "school": student.school,
        "roll_number": student.roll_number,
        "subjects": subjects,
        "weak_topics": weak,
        "recent_attempts": attempts,
    }


# --------------------------------------------------------------------------
# CRUD - subjects / chapters / topics / resources
# --------------------------------------------------------------------------
@router.get("/subjects", response_model=List[Dict[str, Any]])
def admin_subjects(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    payload = []
    for subject in db.scalars(select(Subject).order_by(Subject.order_index)):
        payload.append(
            {
                **SubjectOut.model_validate(subject).model_dump(),
                "is_active": subject.is_active,
                "chapter_count": db.scalar(
                    select(func.count(Chapter.id)).where(Chapter.subject_id == subject.id)
                ) or 0,
                "topic_count": db.scalar(
                    select(func.count(Topic.id))
                    .join(Chapter, Topic.chapter_id == Chapter.id)
                    .where(Chapter.subject_id == subject.id)
                ) or 0,
            }
        )
    return payload


@router.get("/chapters", response_model=List[Dict[str, Any]])
def admin_chapters(
    subject_id: Optional[int] = None, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = select(Chapter)
    if subject_id:
        query = query.where(Chapter.subject_id == subject_id)
    payload = []
    for chapter in db.scalars(query.order_by(Chapter.subject_id, Chapter.order_index)):
        subject = db.get(Subject, chapter.subject_id)
        payload.append(
            {
                **ChapterOut.model_validate(chapter).model_dump(),
                "is_active": chapter.is_active,
                "subject_name": subject.name if subject else "",
                "topic_count": db.scalar(
                    select(func.count(Topic.id)).where(Topic.chapter_id == chapter.id)
                ) or 0,
            }
        )
    return payload


@router.get("/topics", response_model=List[Dict[str, Any]])
def admin_topics(
    chapter_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    query = select(Topic).join(Chapter, Topic.chapter_id == Chapter.id)
    if chapter_id:
        query = query.where(Topic.chapter_id == chapter_id)
    if subject_id:
        query = query.where(Chapter.subject_id == subject_id)
    if search:
        query = query.where(Topic.name.ilike(f"%{search.strip()}%"))
    payload = []
    for topic in db.scalars(query.order_by(Topic.chapter_id, Topic.order_index).limit(limit)):
        chapter = db.get(Chapter, topic.chapter_id)
        subject = db.get(Subject, chapter.subject_id) if chapter else None
        payload.append(
            {
                **TopicOut.model_validate(topic).model_dump(),
                "is_active": topic.is_active,
                "chapter_name": chapter.name if chapter else "",
                "subject_name": subject.name if subject else "",
                "resource_count": db.scalar(
                    select(func.count(Resource.id)).where(Resource.topic_id == topic.id)
                ) or 0,
                "question_count": db.scalar(
                    select(func.count(Question.id)).where(Question.topic_id == topic.id)
                ) or 0,
            }
        )
    return payload


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)) -> SubjectOut:
    if db.scalar(select(Subject).where(Subject.code == payload.code.upper())):
        raise HTTPException(status_code=409, detail="A subject with this code already exists.")
    subject = Subject(
        code=payload.code.upper(),
        name=payload.name,
        slug=unique_slug(db, Subject, payload.name),
        description=payload.description,
        icon=payload.icon,
        color=payload.color,
        ncert_url=payload.ncert_url,
        order_index=payload.order_index,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return SubjectOut.model_validate(subject)


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db)) -> SubjectOut:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found.")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(subject, field, value)
    if payload.name:
        subject.slug = unique_slug(db, Subject, payload.name)
    db.commit()
    db.refresh(subject)
    return SubjectOut.model_validate(subject)


@router.delete("/subjects/{subject_id}", response_model=Message)
def delete_subject(subject_id: int, db: Session = Depends(get_db)) -> Message:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found.")
    subject.is_active = False  # soft delete keeps student history intact
    db.commit()
    return Message(detail="Subject archived. Student history is preserved.")


@router.post("/chapters", response_model=ChapterOut, status_code=201)
def create_chapter(payload: ChapterCreate, db: Session = Depends(get_db)) -> ChapterOut:
    if db.get(Subject, payload.subject_id) is None:
        raise HTTPException(status_code=404, detail="Subject not found.")
    chapter = Chapter(
        subject_id=payload.subject_id,
        name=payload.name,
        slug=unique_slug(db, Chapter, payload.name, Chapter.subject_id, payload.subject_id),
        number=payload.number,
        description=payload.description,
        ncert_url=payload.ncert_url,
        estimated_hours=payload.estimated_hours,
        order_index=payload.number,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return ChapterOut.model_validate(chapter)


@router.patch("/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)) -> ChapterOut:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(chapter, field, value)
    if payload.name:
        chapter.slug = unique_slug(db, Chapter, payload.name, Chapter.subject_id, chapter.subject_id)
    db.commit()
    db.refresh(chapter)
    return ChapterOut.model_validate(chapter)


@router.delete("/chapters/{chapter_id}", response_model=Message)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)) -> Message:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    chapter.is_active = False
    db.commit()
    return Message(detail="Chapter archived.")


@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)) -> TopicOut:
    chapter = db.get(Chapter, payload.chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    topic = Topic(
        chapter_id=payload.chapter_id,
        name=payload.name,
        slug=unique_slug(db, Topic, payload.name, Topic.chapter_id, payload.chapter_id),
        summary=payload.summary,
        key_concepts=payload.key_concepts,
        examples=payload.examples,
        prerequisites=payload.prerequisites,
        ncert_url=payload.ncert_url or chapter.ncert_url,
        difficulty=payload.difficulty,
        estimated_minutes=payload.estimated_minutes,
        order_index=len(chapter.topics),
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicOut.model_validate(topic)


@router.patch("/topics/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)) -> TopicOut:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(topic, field, value)
    if payload.name:
        topic.slug = unique_slug(db, Topic, payload.name, Topic.chapter_id, topic.chapter_id)
    db.commit()
    db.refresh(topic)
    return TopicOut.model_validate(topic)


@router.delete("/topics/{topic_id}", response_model=Message)
def delete_topic(topic_id: int, db: Session = Depends(get_db)) -> Message:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    topic.is_active = False
    db.commit()
    return Message(detail="Topic archived.")


@router.get("/resources", response_model=List[ResourceOut])
def list_resources(
    topic_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[ResourceOut]:
    query = select(Resource)
    if topic_id:
        query = query.where(Resource.topic_id == topic_id)
    return [
        ResourceOut.model_validate(row)
        for row in db.scalars(query.order_by(Resource.topic_id, Resource.order_index).limit(limit))
    ]


@router.post("/resources", response_model=ResourceOut, status_code=201)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db)) -> ResourceOut:
    topic = db.get(Topic, payload.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    resource = Resource(
        topic_id=payload.topic_id,
        title=payload.title,
        type=payload.type,
        description=payload.description,
        body=payload.body,
        external_url=payload.external_url,
        ncert_url=payload.ncert_url or topic.ncert_url,
        estimated_minutes=payload.estimated_minutes,
        order_index=len(topic.resources),
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return ResourceOut.model_validate(resource)


@router.patch("/resources/{resource_id}", response_model=ResourceOut)
def update_resource(resource_id: int, payload: ResourceUpdate, db: Session = Depends(get_db)) -> ResourceOut:
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found.")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(resource, field, value)
    db.commit()
    db.refresh(resource)
    return ResourceOut.model_validate(resource)


@router.delete("/resources/{resource_id}", response_model=Message)
def delete_resource(resource_id: int, db: Session = Depends(get_db)) -> Message:
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found.")
    db.delete(resource)
    db.commit()
    return Message(detail="Resource deleted.")


# --------------------------------------------------------------------------
# CRUD - questions and quizzes
# --------------------------------------------------------------------------
@router.get("/questions", response_model=List[QuestionAdminOut])
def list_questions(
    topic_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[QuestionAdminOut]:
    query = select(Question)
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    if chapter_id:
        query = query.where(Question.chapter_id == chapter_id)
    if subject_id:
        query = query.where(Question.subject_id == subject_id)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if search:
        query = query.where(Question.text.ilike(f"%{search.strip()}%"))
    rows = db.scalars(query.order_by(Question.id.desc()).limit(limit))
    return [QuestionAdminOut.model_validate(row) for row in rows]


@router.post("/questions", response_model=QuestionAdminOut, status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)) -> QuestionAdminOut:
    topic = db.get(Topic, payload.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    if payload.type == "mcq" and len(payload.options) < 2:
        raise HTTPException(status_code=422, detail="An MCQ needs at least two options.")
    if payload.options and payload.correct_answer not in payload.options:
        raise HTTPException(status_code=422, detail="The correct answer must be one of the options.")
    chapter = topic.chapter
    question = Question(
        subject_id=chapter.subject_id,
        chapter_id=chapter.id,
        topic_id=topic.id,
        type=payload.type,
        difficulty=payload.difficulty,
        text=payload.text,
        options=payload.options,
        correct_answer=payload.correct_answer,
        explanation=payload.explanation,
        concept_tag=payload.concept_tag or topic.name,
        marks=payload.marks,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return QuestionAdminOut.model_validate(question)


@router.patch("/questions/{question_id}", response_model=QuestionAdminOut)
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)) -> QuestionAdminOut:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(question, field, value)
    if question.options and question.correct_answer not in question.options:
        raise HTTPException(status_code=422, detail="The correct answer must be one of the options.")
    db.commit()
    db.refresh(question)
    return QuestionAdminOut.model_validate(question)


@router.delete("/questions/{question_id}", response_model=Message)
def delete_question(question_id: int, db: Session = Depends(get_db)) -> Message:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    question.is_active = False
    db.commit()
    return Message(detail="Question archived (existing attempts keep their history).")


@router.get("/quizzes", response_model=List[Dict[str, Any]])
def admin_quizzes(
    subject_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    query = select(Quiz)
    if subject_id:
        query = query.where(Quiz.subject_id == subject_id)
    payload = []
    for quiz in db.scalars(query.order_by(Quiz.id.desc()).limit(limit)):
        attempts = db.scalar(
            select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == quiz.id)
        ) or 0
        average = db.scalar(
            select(func.avg(QuizAttempt.accuracy)).where(
                QuizAttempt.quiz_id == quiz.id, QuizAttempt.status == "submitted"
            )
        )
        subject = db.get(Subject, quiz.subject_id)
        payload.append(
            {
                **QuizOut.model_validate(quiz).model_dump(),
                "subject_name": subject.name if subject else "",
                "question_count": len(quiz.quiz_questions),
                "attempts": attempts,
                "average_accuracy": round(float(average), 1) if average is not None else None,
            }
        )
    return payload


@router.post("/quizzes", response_model=QuizOut, status_code=201)
def create_quiz(payload: QuizCreate, db: Session = Depends(get_db)) -> QuizOut:
    if db.get(Subject, payload.subject_id) is None:
        raise HTTPException(status_code=404, detail="Subject not found.")
    quiz = Quiz(
        title=payload.title,
        description=payload.description,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        topic_id=payload.topic_id,
        difficulty=payload.difficulty,
        time_limit_minutes=payload.time_limit_minutes,
        pass_percentage=payload.pass_percentage,
        is_published=payload.is_published,
    )
    db.add(quiz)
    db.flush()
    for index, question_id in enumerate(payload.question_ids):
        if db.get(Question, question_id) is None:
            raise HTTPException(status_code=422, detail=f"Question {question_id} does not exist.")
        db.add(QuizQuestion(quiz_id=quiz.id, question_id=question_id, order_index=index))
    db.commit()
    db.refresh(quiz)
    return QuizOut.model_validate(quiz)


@router.patch("/quizzes/{quiz_id}", response_model=QuizOut)
def update_quiz(quiz_id: int, payload: QuizUpdate, db: Session = Depends(get_db)) -> QuizOut:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    question_ids = data.pop("question_ids", None)
    for field, value in data.items():
        setattr(quiz, field, value)
    if question_ids is not None:
        for link in list(quiz.quiz_questions):
            db.delete(link)
        db.flush()
        for index, question_id in enumerate(question_ids):
            db.add(QuizQuestion(quiz_id=quiz.id, question_id=question_id, order_index=index))
    db.commit()
    db.refresh(quiz)
    return QuizOut.model_validate(quiz)


@router.delete("/quizzes/{quiz_id}", response_model=Message)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)) -> Message:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    quiz.is_published = False
    db.commit()
    return Message(detail="Quiz unpublished.")


@router.post("/reindex", response_model=Dict[str, Any])
def reindex(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Rebuild the RAG vector index after editing content."""
    return index_content(db, force=True)
