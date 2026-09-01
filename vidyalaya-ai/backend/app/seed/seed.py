"""Database seeding: curriculum, demo users and realistic learning history.

    python -m app.seed.seed            # seed if empty
    python -m app.seed.seed --reset    # drop everything and reseed

The demo history is *simulated activity*, not fabricated mastery: quiz attempts
and answers are inserted, and the real mastery / weakness / learning-profile /
recommendation services then compute every number the UI shows.
"""
from __future__ import annotations

import argparse
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.core.utils import slugify
from app.db.base_class import Base, utcnow
from app.db.session import SessionLocal, engine
from app.models import (
    AcademicYear, ActivityEvent, Answer, Chapter, ChatMessage, ChatSession,
    MasterySnapshot, Question, Quiz, QuizAttempt, QuizQuestion, Recommendation,
    Resource, Student, StudentLearningProfile, StudentSubjectMastery,
    StudentTopicMastery, Subject, Teacher, Topic, User,
)
from app.seed.content import SUBJECTS
from app.seed.questions import generate_for_topic
from app.seed.resources import build_resources
from app.services.academic import ensure_enrolment, get_or_create_year
from app.services.activity import log_event
from app.services.learning_profile import compute_learning_profile
from app.services.mastery import refresh_student_mastery, write_snapshot
from app.services.recommendations import generate_recommendations

logger = logging.getLogger(__name__)

# Target accuracy per subject for the flagship demo student.
DEMO_SUBJECT_TARGETS = {"MATH": 0.80, "PHY": 0.55, "CHEM": 0.83, "BIO": 0.68, "ENG": 0.90, "CS": 0.77}
# Topics that must come out as genuine weaknesses in the demo data.
DEMO_WEAK_TOPICS = {
    "kirchhoffs-laws-and-circuit-analysis": 0.36,
    "electric-current-drift-velocity-and-ohms-law": 0.48,
    "integration-by-parts-and-partial-fractions": 0.42,
    "indefinite-integrals-and-substitution": 0.50,
}
MONTH_FACTORS = [0.74, 0.84, 0.92, 1.0]  # four months of steady improvement
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}
# Which study formats were used before each simulated quiz, and how much they
# actually helped. The learning-profile service then *measures* this from the
# resulting data instead of being told.
FORMAT_ROTATION = [
    ["practice"], ["visual"], ["text"], ["audio"], ["practice", "visual"],
    ["text", "practice"], ["audio", "text"], ["visual", "practice"],
]
FORMAT_EFFECT = {"practice": 0.12, "visual": 0.05, "text": 0.0, "audio": -0.14}

EXTRA_STUDENTS = [
    ("Ananya Sharma", "ananya@student.vidyalaya.ai", 0.86),
    ("Rohan Verma", "rohan@student.vidyalaya.ai", 0.71),
    ("Meera Nair", "meera@student.vidyalaya.ai", 0.63),
    ("Kabir Singh", "kabir@student.vidyalaya.ai", 0.49),
    ("Ishita Rao", "ishita@student.vidyalaya.ai", 0.78),
    ("Aarav Gupta", "aarav@student.vidyalaya.ai", 0.58),
    ("Zoya Khan", "zoya@student.vidyalaya.ai", 0.91),
]


# --------------------------------------------------------------------------
# catalogue
# --------------------------------------------------------------------------
def seed_catalog(db: Session) -> Dict[str, int]:
    counts = {"subjects": 0, "chapters": 0, "topics": 0, "resources": 0, "questions": 0, "quizzes": 0}

    # concept pool used to build believable distractors across subjects
    concept_pool: List[str] = []
    for pack in SUBJECTS:
        for chapter in pack["chapters"]:
            for topic in chapter["topics"]:
                concept_pool.extend(topic.get("concepts") or [])

    for order, pack in enumerate(SUBJECTS):
        subject = db.scalar(select(Subject).where(Subject.code == pack["code"]))
        if subject is None:
            subject = Subject(
                code=pack["code"],
                name=pack["name"],
                slug=slugify(pack["name"]),
                description=pack.get("description", ""),
                icon=pack.get("icon", "📘"),
                color=pack.get("color", "indigo"),
                ncert_url=pack.get("ncert_url", ""),
                order_index=order,
            )
            db.add(subject)
            db.flush()
            counts["subjects"] += 1

        for chapter_index, chapter_data in enumerate(pack["chapters"]):
            chapter_slug = slugify(chapter_data["name"])
            chapter = db.scalar(
                select(Chapter).where(Chapter.subject_id == subject.id, Chapter.slug == chapter_slug)
            )
            if chapter is None:
                chapter = Chapter(
                    subject_id=subject.id,
                    name=chapter_data["name"],
                    slug=chapter_slug,
                    number=chapter_data.get("number", chapter_index + 1),
                    description=chapter_data.get("description", ""),
                    ncert_url=chapter_data.get("ncert_url", ""),
                    estimated_hours=chapter_data.get("estimated_hours", 6),
                    order_index=chapter_index,
                )
                db.add(chapter)
                db.flush()
                counts["chapters"] += 1

            sibling_names = [t["name"] for t in chapter_data["topics"]]
            for topic_index, topic_data in enumerate(chapter_data["topics"]):
                topic_slug = slugify(topic_data["name"])
                topic = db.scalar(
                    select(Topic).where(Topic.chapter_id == chapter.id, Topic.slug == topic_slug)
                )
                if topic is None:
                    topic = Topic(
                        chapter_id=chapter.id,
                        name=topic_data["name"],
                        slug=topic_slug,
                        summary=topic_data.get("summary", ""),
                        key_concepts=list(topic_data.get("concepts") or []),
                        examples=list(topic_data.get("examples") or []),
                        prerequisites=list(topic_data.get("prerequisites") or []),
                        ncert_url=topic_data.get("ncert_url") or chapter_data.get("ncert_url", ""),
                        difficulty=topic_data.get("difficulty", "medium"),
                        estimated_minutes=topic_data.get("estimated_minutes", 25),
                        order_index=topic_index,
                    )
                    db.add(topic)
                    db.flush()
                    counts["topics"] += 1

                # ---- resources ------------------------------------------
                if not db.scalar(select(func.count(Resource.id)).where(Resource.topic_id == topic.id)):
                    for resource_index, resource_data in enumerate(
                        build_resources(
                            {**topic_data, "ncert_url": topic.ncert_url}, chapter.name, subject.name
                        )
                    ):
                        db.add(
                            Resource(
                                topic_id=topic.id,
                                title=resource_data["title"],
                                type=resource_data["type"],
                                description=resource_data["description"],
                                body=resource_data["body"],
                                ncert_url=resource_data.get("ncert_url", ""),
                                estimated_minutes=resource_data["estimated_minutes"],
                                order_index=resource_index,
                            )
                        )
                        counts["resources"] += 1

                # ---- questions ------------------------------------------
                if not db.scalar(select(func.count(Question.id)).where(Question.topic_id == topic.id)):
                    others = [c for c in concept_pool if c not in (topic_data.get("concepts") or [])]
                    seed_value = abs(hash(topic_slug)) % (2**31)
                    peers = [name for name in sibling_names if name != topic_data["name"]]
                    if len(peers) < 3:
                        peers = peers + [
                            t["name"]
                            for c in pack["chapters"]
                            for t in c["topics"]
                            if t["name"] != topic_data["name"] and t["name"] not in peers
                        ][: 4 - len(peers)]
                    generated = generate_for_topic(
                        topic_data, chapter.name, subject.name, peers, others[:400], seed_value
                    )
                    authored = topic_data.get("questions") or []
                    for question_data in authored + generated:
                        db.add(
                            Question(
                                subject_id=subject.id,
                                chapter_id=chapter.id,
                                topic_id=topic.id,
                                type=question_data.get("type", "mcq"),
                                difficulty=question_data.get("difficulty", "medium"),
                                text=question_data["text"],
                                options=list(question_data.get("options") or []),
                                correct_answer=question_data["answer"],
                                explanation=question_data.get("explanation", ""),
                                concept_tag=question_data.get("concept", topic.name),
                                marks=question_data.get("marks", 1),
                            )
                        )
                        counts["questions"] += 1
            db.flush()

    db.flush()
    counts["quizzes"] = seed_quizzes(db)
    return counts


def seed_quizzes(db: Session) -> int:
    created = 0
    for subject in db.scalars(select(Subject).order_by(Subject.order_index)):
        for chapter in subject.chapters:
            topic_ids = [topic.id for topic in chapter.topics]
            if not topic_ids:
                continue
            questions = list(
                db.scalars(
                    select(Question)
                    .where(Question.topic_id.in_(topic_ids), Question.is_active.is_(True))
                    .order_by(Question.difficulty.desc(), Question.id.asc())
                )
            )
            if not questions:
                continue

            title = f"{chapter.name} - Chapter Test"
            if not db.scalar(select(Quiz).where(Quiz.title == title)):
                quiz = Quiz(
                    title=title,
                    description=f"Mixed difficulty test covering {chapter.name} ({subject.name}).",
                    subject_id=subject.id,
                    chapter_id=chapter.id,
                    difficulty="mixed",
                    time_limit_minutes=15,
                    pass_percentage=60,
                )
                db.add(quiz)
                db.flush()
                # spread the questions across the chapter's topics
                by_topic: Dict[int, List[Question]] = {}
                for question in questions:
                    by_topic.setdefault(question.topic_id, []).append(question)
                selected: List[Question] = []
                while len(selected) < min(8, len(questions)):
                    added = False
                    for topic_id in topic_ids:
                        bucket = by_topic.get(topic_id) or []
                        if bucket:
                            selected.append(bucket.pop(0))
                            added = True
                            if len(selected) >= 8:
                                break
                    if not added:
                        break
                for index, question in enumerate(selected):
                    db.add(QuizQuestion(quiz_id=quiz.id, question_id=question.id, order_index=index))
                created += 1

            for topic in chapter.topics:
                topic_questions = [q for q in questions if q.topic_id == topic.id]
                if len(topic_questions) < 4:
                    continue
                topic_title = f"{topic.name} - Topic Quiz"
                if db.scalar(select(Quiz).where(Quiz.title == topic_title)):
                    continue
                quiz = Quiz(
                    title=topic_title,
                    description=f"Focused quiz on {topic.name}.",
                    subject_id=subject.id,
                    chapter_id=chapter.id,
                    topic_id=topic.id,
                    difficulty=topic.difficulty or "mixed",
                    time_limit_minutes=10,
                    pass_percentage=60,
                )
                db.add(quiz)
                db.flush()
                for index, question in enumerate(topic_questions[:5]):
                    db.add(QuizQuestion(quiz_id=quiz.id, question_id=question.id, order_index=index))
                created += 1
    db.flush()
    return created


# --------------------------------------------------------------------------
# users
# --------------------------------------------------------------------------
def create_user(
    db: Session, email: str, name: str, password: str, role: str, emoji: str = "🎓"
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        email=email,
        full_name=name,
        hashed_password=hash_password(password),
        role=role,
        avatar_emoji=emoji,
    )
    db.add(user)
    db.flush()
    return user


def create_student(
    db: Session, user: User, year: AcademicYear, roll: str, previous_year: Optional[AcademicYear] = None
) -> Student:
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student:
        return student
    student = Student(
        user_id=user.id,
        class_level="12",
        stream="Science",
        school="Delhi Public School",
        roll_number=roll,
        guardian_name="",
        current_academic_year_id=year.id,
        daily_goal_minutes=45,
    )
    db.add(student)
    db.flush()
    ensure_enrolment(db, student, year)
    if previous_year:
        ensure_enrolment(db, student, previous_year)
    return student


# --------------------------------------------------------------------------
# simulated learning history
# --------------------------------------------------------------------------
def _target_for_topic(topic: Topic, subject_target: float) -> float:
    return DEMO_WEAK_TOPICS.get(topic.slug, subject_target)


def simulate_history(
    db: Session,
    student: Student,
    year: AcademicYear,
    subject_targets: Dict[str, float],
    months: int = 4,
    quizzes_per_subject_per_month: int = 1,
    seed_value: int = 7,
) -> Dict[str, Any]:
    rng = random.Random(seed_value)
    now = utcnow()
    subjects = list(db.scalars(select(Subject).order_by(Subject.order_index)))
    monthly: Dict[str, Dict[int, List[float]]] = {}
    attempts_created = 0

    for month_index in range(months):
        months_back = months - 1 - month_index
        factor = MONTH_FACTORS[min(month_index, len(MONTH_FACTORS) - 1)]
        if months_back == 0:
            base_day = now - timedelta(days=rng.randint(0, 5), hours=rng.randint(1, 6))
        else:
            base_day = now - timedelta(days=30 * months_back + rng.randint(2, 10))
        period = base_day.strftime("%Y-%m")

        for subject in subjects:
            target = subject_targets.get(subject.code)
            if target is None:
                continue
            quizzes = list(
                db.scalars(
                    select(Quiz)
                    .where(Quiz.subject_id == subject.id, Quiz.is_published.is_(True))
                    .order_by(Quiz.id)
                )
            )
            if not quizzes:
                continue
            chosen = [quizzes[(month_index * 3 + offset) % len(quizzes)] for offset in range(quizzes_per_subject_per_month)]

            for quiz_offset, quiz in enumerate(chosen):
                when = base_day + timedelta(hours=rng.randint(9, 20), minutes=rng.randint(0, 59), days=quiz_offset)
                if when > now:
                    when = now - timedelta(hours=rng.randint(2, 30))
                questions = [qq.question for qq in quiz.quiz_questions if qq.question]
                if not questions:
                    continue

                # ---- study before the quiz (drives resource effectiveness)
                formats = FORMAT_ROTATION[(month_index * 3 + quiz_offset + subject.id) % len(FORMAT_ROTATION)]
                format_effect = sum(FORMAT_EFFECT[f] for f in formats) / len(formats)

                topic_ids = sorted({q.topic_id for q in questions})
                study_topic_id = topic_ids[0]
                log_event(
                    db, student, "opened_subject", subject_id=subject.id,
                    academic_year_id=year.id, created_at=when - timedelta(hours=3),
                    duration_seconds=60,
                )
                log_event(
                    db, student, "opened_topic", topic_id=study_topic_id,
                    academic_year_id=year.id, created_at=when - timedelta(hours=2, minutes=50),
                    duration_seconds=120,
                )
                for fmt in formats:
                    resource = db.scalar(
                        select(Resource).where(Resource.topic_id == study_topic_id, Resource.type == fmt)
                    )
                    if resource is None:
                        continue
                    log_event(
                        db, student, "opened_resource", resource_id=resource.id, resource_type=fmt,
                        academic_year_id=year.id, created_at=when - timedelta(hours=2, minutes=30),
                        duration_seconds=rng.randint(240, 600),
                    )
                    log_event(
                        db, student, f"selected_{fmt}", resource_id=resource.id, resource_type=fmt,
                        academic_year_id=year.id, created_at=when - timedelta(hours=2, minutes=29),
                    )
                    log_event(
                        db, student, "completed_resource", resource_id=resource.id, resource_type=fmt,
                        academic_year_id=year.id, created_at=when - timedelta(hours=2),
                        duration_seconds=rng.randint(300, 900), result="completed",
                    )

                # ---- the attempt itself ---------------------------------
                attempt_number = 1 + (
                    db.scalar(
                        select(func.count(QuizAttempt.id)).where(
                            QuizAttempt.student_id == student.id, QuizAttempt.quiz_id == quiz.id
                        )
                    )
                    or 0
                )
                attempt = QuizAttempt(
                    quiz_id=quiz.id,
                    student_id=student.id,
                    academic_year_id=year.id,
                    attempt_number=attempt_number,
                    status="submitted",
                    started_at=when - timedelta(minutes=14),
                    submitted_at=when,
                    duration_seconds=rng.randint(300, 780),
                    created_at=when,
                    updated_at=when,
                )
                db.add(attempt)
                db.flush()

                correct_count = 0
                topic_stats: Dict[str, Dict[str, int]] = {}
                difficulty_stats: Dict[str, Dict[str, int]] = {}

                # Decide the outcome deterministically per topic so the demo
                # data is stable and the monthly trend is a real improvement
                # curve rather than noise. Hardest questions are missed first.
                verdicts: Dict[int, bool] = {}
                by_topic_questions: Dict[int, List[Question]] = {}
                for question in questions:
                    by_topic_questions.setdefault(question.topic_id, []).append(question)
                for topic_id, topic_questions in by_topic_questions.items():
                    topic = db.get(Topic, topic_id)
                    topic_target = _target_for_topic(topic, target) if topic else target
                    probability = min(0.97, max(0.05, topic_target * factor + format_effect))
                    ordered = sorted(
                        topic_questions,
                        key=lambda q: (DIFFICULTY_ORDER.get(q.difficulty, 1), q.id),
                    )
                    forced_wrong = [
                        q for q in ordered if (q.concept_tag or "").lower().startswith("kirchhoff")
                    ]
                    target_correct = int(round(probability * len(ordered)))
                    target_correct = max(0, min(len(ordered) - len(forced_wrong), target_correct))
                    remaining = [q for q in ordered if q not in forced_wrong]
                    correct_ids = {q.id for q in remaining[:target_correct]}
                    for question in ordered:
                        verdicts[question.id] = question.id in correct_ids

                for question in questions:
                    is_correct = verdicts.get(question.id, False)
                    given = question.correct_answer
                    if not is_correct:
                        options = list(question.options or [])
                        wrong = [o for o in options if o != question.correct_answer]
                        given = rng.choice(wrong) if wrong else ""
                    db.add(
                        Answer(
                            attempt_id=attempt.id,
                            question_id=question.id,
                            given_answer=given,
                            is_correct=is_correct,
                            marks_awarded=float(question.marks or 1) if is_correct else 0.0,
                            time_spent_seconds=rng.randint(25, 110),
                            created_at=when,
                        )
                    )
                    correct_count += 1 if is_correct else 0
                    bucket = topic_stats.setdefault(str(question.topic_id), {"correct": 0, "total": 0})
                    bucket["total"] += 1
                    bucket["correct"] += 1 if is_correct else 0
                    dbucket = difficulty_stats.setdefault(question.difficulty, {"correct": 0, "total": 0})
                    dbucket["total"] += 1
                    dbucket["correct"] += 1 if is_correct else 0
                    log_event(
                        db, student, "correct_answer" if is_correct else "incorrect_answer",
                        topic_id=question.topic_id, academic_year_id=year.id, created_at=when,
                        result="correct" if is_correct else "incorrect",
                        details={"question_id": question.id, "difficulty": question.difficulty},
                    )

                total = len(questions)
                attempt.score = float(correct_count)
                attempt.max_score = float(total)
                attempt.accuracy = round(100.0 * correct_count / total, 1) if total else 0.0
                attempt.topic_breakdown = topic_stats
                attempt.difficulty_breakdown = difficulty_stats
                log_event(
                    db, student, "completed_quiz" if attempt_number == 1 else "retook_quiz",
                    subject_id=subject.id, topic_id=quiz.topic_id or study_topic_id,
                    academic_year_id=year.id, created_at=when, duration_seconds=attempt.duration_seconds,
                    score=attempt.accuracy, result=f"{correct_count}/{total}",
                    details={"quiz_id": quiz.id, "attempt_id": attempt.id},
                )
                attempts_created += 1
                monthly.setdefault(period, {}).setdefault(subject.id, []).append(attempt.accuracy)

    db.flush()

    # ---- monthly history snapshots (never deleted) -----------------------
    for period, per_subject in monthly.items():
        year_number, month_number = (int(part) for part in period.split("-"))
        when = datetime(year_number, month_number, 15)
        overall: List[float] = []
        for subject_id, accuracies in per_subject.items():
            value = sum(accuracies) / len(accuracies)
            overall.append(value)
            write_snapshot(
                db, student, year.id, subject_id, value, when=when,
                quizzes_taken=len(accuracies), study_minutes=len(accuracies) * 35,
            )
        if overall:
            write_snapshot(
                db, student, year.id, None, sum(overall) / len(overall), when=when,
                quizzes_taken=sum(len(v) for v in per_subject.values()),
                study_minutes=sum(len(v) for v in per_subject.values()) * 35,
            )
    db.flush()
    return {"attempts": attempts_created}


def finalise_student(db: Session, student: Student, year: AcademicYear) -> None:
    refresh_student_mastery(db, student, year.id, topic_ids=None, snapshot=False)
    compute_learning_profile(db, student, year.id)
    db.flush()
    generate_recommendations(db, student, year.id)
    db.flush()


def seed_demo_chat(db: Session, student: Student) -> None:
    if db.scalar(select(func.count(ChatSession.id)).where(ChatSession.student_id == student.id)):
        return
    session = ChatSession(student_id=student.id, title="Explain capacitors")
    db.add(session)
    db.flush()
    db.add(
        ChatMessage(
            session_id=session.id, role="user", content="Explain capacitors", mode="offline",
            created_at=utcnow() - timedelta(days=1, minutes=5),
        )
    )
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            mode="offline",
            content=(
                "### Capacitors, Combinations and Dielectrics\n\nA capacitor stores charge at a given "
                "potential difference; its capacitance depends only on geometry and the dielectric "
                "between the plates.\n\n**Key concepts**\n- C = Q/V, unit farad\n- Series: 1/C = 1/C1 + 1/C2; "
                "Parallel: C = C1 + C2\n- Energy stored U = 1/2 CV^2\n\n_AI tutor is running in offline mode._"
            ),
            created_at=utcnow() - timedelta(days=1),
        )
    )
    db.flush()


# --------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------
def is_seeded(db: Session) -> bool:
    return bool(db.scalar(select(func.count(Subject.id))))


def seed_all(db: Session, with_history: bool = True) -> Dict[str, Any]:
    previous_year = get_or_create_year(db, _previous_label())
    year = get_or_create_year(db)
    year.is_current = True
    previous_year.is_current = False
    db.flush()

    counts = seed_catalog(db)

    teacher_user = create_user(
        db, settings.DEMO_TEACHER_EMAIL, "Priya Menon", settings.DEMO_TEACHER_PASSWORD, "teacher", "👩‍🏫"
    )
    if not db.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id)):
        db.add(Teacher(user_id=teacher_user.id, department="Science", designation="Senior Teacher"))
    admin_user = create_user(db, "admin@vidyalaya.ai", "System Admin", "Admin@123", "admin", "🛠️")
    if not db.scalar(select(Teacher).where(Teacher.user_id == admin_user.id)):
        db.add(Teacher(user_id=admin_user.id, department="Administration", designation="Administrator"))
    db.flush()

    demo_user = create_user(
        db, settings.DEMO_STUDENT_EMAIL, "Abhinav Sharma", settings.DEMO_STUDENT_PASSWORD, "student", "🎓"
    )
    demo_student = create_student(db, demo_user, year, "12A-01", previous_year)

    students = [(demo_student, DEMO_SUBJECT_TARGETS, 7)]
    for index, (name, email, level) in enumerate(EXTRA_STUDENTS):
        user = create_user(db, email, name, "Student@123", "student", "🎓")
        student = create_student(db, user, year, f"12A-{index + 2:02d}")
        targets = {
            code: max(0.25, min(0.97, level + ((index % 3) - 1) * 0.07))
            for code in DEMO_SUBJECT_TARGETS
        }
        students.append((student, targets, 11 + index))
    db.flush()

    if with_history:
        for position, (student, targets, seed_value) in enumerate(students):
            already = db.scalar(
                select(func.count(QuizAttempt.id)).where(QuizAttempt.student_id == student.id)
            )
            if already:
                continue
            simulate_history(
                db, student, year, targets,
                months=4 if position == 0 else 3,
                quizzes_per_subject_per_month=3 if position == 0 else 2,
                seed_value=seed_value,
            )
            finalise_student(db, student, year)

        # previous-year history for the demo student (never deleted)
        if not db.scalar(
            select(func.count(MasterySnapshot.id)).where(
                MasterySnapshot.student_id == demo_student.id,
                MasterySnapshot.academic_year_id == previous_year.id,
            )
        ):
            for month_offset, value in enumerate([44.0, 51.0, 57.0, 62.0]):
                write_snapshot(
                    db, demo_student, previous_year.id, None, value,
                    when=datetime(int(previous_year.label.split("-")[0]), 7 + month_offset, 15),
                    quizzes_taken=4, study_minutes=140,
                )
        seed_demo_chat(db, demo_student)

    db.commit()

    counts.update(
        {
            "students": db.scalar(select(func.count(Student.id))) or 0,
            "attempts": db.scalar(select(func.count(QuizAttempt.id))) or 0,
            "activity_events": db.scalar(select(func.count(ActivityEvent.id))) or 0,
            "recommendations": db.scalar(select(func.count(Recommendation.id))) or 0,
        }
    )
    return counts


def _previous_label() -> str:
    from app.services.academic import current_year_label

    start = int(current_year_label().split("-")[0]) - 1
    return f"{start}-{str(start + 1)[-2:]}"


def reset_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Vidyalaya AI database")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first")
    parser.add_argument("--no-history", action="store_true", help="skip simulated learning history")
    parser.add_argument("--index", action="store_true", help="rebuild the RAG vector index afterwards")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.reset:
        logger.info("Dropping and recreating tables...")
        reset_database()
    else:
        Base.metadata.create_all(engine)

    with SessionLocal() as db:
        stats = seed_all(db, with_history=not args.no_history)
        logger.info("Seed complete: %s", stats)
        if args.index:
            from app.ai.rag import index_content

            logger.info("Vector index: %s", index_content(db, force=True))
    print("Demo login ->", settings.DEMO_STUDENT_EMAIL, "/", settings.DEMO_STUDENT_PASSWORD)
    print("Teacher login ->", settings.DEMO_TEACHER_EMAIL, "/", settings.DEMO_TEACHER_PASSWORD)


if __name__ == "__main__":
    main()
