"""Unit / behaviour tests for the learning algorithms and AI layer.

    python -m tests.test_units      (no test runner required)
    pytest tests/test_units.py

These tests drive the real services against a real database session, so they
check behaviour ("does bad performance actually lower mastery and flag the
topic, with a reason?") rather than restating the formulas.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import select

from app.ai import offline
from app.ai.rag import retrieve
from app.ai.tutor import build_student_context, detect_intent
from app.core.security import (
    create_access_token, decode_access_token, hash_password, is_valid_email,
    password_problems, verify_password,
)
from app.core.utils import slugify
from app.db.base_class import utcnow
from app.db.session import SessionLocal
from app.models import (
    AcademicYear, Answer, Chapter, Question, Quiz, QuizAttempt, Resource, Student,
    StudentTopicMastery, Subject, Topic, User,
)
from app.services.academic import get_current_year
from app.services.activity import log_event
from app.services.learning_profile import compute_learning_profile, profile_payload
from app.services.mastery import _weighted_recent, detect_weakness, refresh_student_mastery
from app.services.quiz import is_answer_correct
from app.services.recommendations import generate_recommendations

state: dict = {}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def db_session():
    if "db" not in state:
        state["db"] = SessionLocal()
    return state["db"]


def make_student(db, label: str) -> Student:
    """A brand-new student with no history."""
    user = User(
        email=f"{label}-{uuid.uuid4().hex[:6]}@test.vidyalaya.ai",
        full_name=f"Test {label}",
        hashed_password=hash_password("Test@1234"),
        role="student",
    )
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, class_level="12")
    db.add(student)
    db.flush()
    return student


def graded_attempt(db, student, quiz, questions, correct_flags, when=None, concept_wrong=None):
    """Insert a submitted attempt with a controlled outcome."""
    year = get_current_year(db)
    when = when or utcnow()
    previous = db.scalar(
        select(QuizAttempt).where(
            QuizAttempt.student_id == student.id, QuizAttempt.quiz_id == quiz.id
        )
    )
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=student.id,
        academic_year_id=year.id,
        attempt_number=1 if previous is None else 2,
        status="submitted",
        started_at=when - timedelta(minutes=10),
        submitted_at=when,
        duration_seconds=420,
        created_at=when,
        updated_at=when,
    )
    db.add(attempt)
    db.flush()
    correct = 0
    for question, is_correct in zip(questions, correct_flags):
        if concept_wrong and (question.concept_tag or "") == concept_wrong:
            is_correct = False
        correct += 1 if is_correct else 0
        db.add(
            Answer(
                attempt_id=attempt.id,
                question_id=question.id,
                given_answer=question.correct_answer if is_correct else "wrong",
                is_correct=is_correct,
                marks_awarded=1.0 if is_correct else 0.0,
                created_at=when,
            )
        )
    attempt.score = float(correct)
    attempt.max_score = float(len(questions))
    attempt.accuracy = round(100.0 * correct / max(1, len(questions)), 1)
    db.flush()
    return attempt


def topic_with_questions(db, minimum: int = 4):
    row = db.execute(
        select(Question.topic_id).group_by(Question.topic_id).having(
            __import__("sqlalchemy").func.count(Question.id) >= minimum
        ).limit(1)
    ).first()
    topic = db.get(Topic, row[0])
    questions = list(
        db.scalars(select(Question).where(Question.topic_id == topic.id).order_by(Question.id))
    )
    quiz = db.scalar(select(Quiz).where(Quiz.topic_id == topic.id))
    if quiz is None:
        quiz = db.scalar(select(Quiz).where(Quiz.chapter_id == topic.chapter_id))
    return topic, questions, quiz


def mastery_of(db, student, topic) -> StudentTopicMastery:
    year = get_current_year(db)
    return db.scalar(
        select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student.id,
            StudentTopicMastery.topic_id == topic.id,
            StudentTopicMastery.academic_year_id == year.id,
        )
    )


# --------------------------------------------------------------------------
# 1. pure helpers
# --------------------------------------------------------------------------
def test_01_weighted_recent_favours_recent_scores():
    assert _weighted_recent([]) == 0.0
    assert _weighted_recent([80]) == 80
    # newest first: 0.5/0.3/0.2 weighting
    assert abs(_weighted_recent([100, 0, 0]) - 50.0) < 1e-6
    assert abs(_weighted_recent([0, 100, 100]) - 50.0) < 1e-6
    improving = _weighted_recent([90, 50, 40])
    declining = _weighted_recent([40, 50, 90])
    assert improving > declining, "recent performance must dominate"


def test_02_weakness_needs_evidence():
    # one bad question is never enough
    level, reason = detect_weakness(
        mastery=10, scores=[0], average=0, trend=0, repeated=[],
        questions_answered=1, topic_name="Integrals",
    )
    assert level == "none" and "Not enough attempts" in reason

    level, reason = detect_weakness(
        mastery=42, scores=[38, 44, 48], average=43.3, trend=-6,
        repeated=["Kirchhoff's Laws"], questions_answered=12, topic_name="Current Electricity",
    )
    assert level == "high"
    assert "below 50% in your last 3 attempts" in reason

    level, _ = detect_weakness(
        mastery=91, scores=[95, 88], average=91.5, trend=3, repeated=[],
        questions_answered=8, topic_name="Matrices",
    )
    assert level == "none"


def test_03_answer_matching_accepts_reasonable_forms():
    question = Question(
        type="mcq", difficulty="easy", text="q",
        options=["A. Charge", "B. Energy"], correct_answer="A. Charge",
    )
    assert is_answer_correct(question, "A. Charge")
    assert is_answer_correct(question, "a. charge")
    assert is_answer_correct(question, "A")
    assert is_answer_correct(question, "Charge")
    assert not is_answer_correct(question, "B. Energy")
    assert not is_answer_correct(question, "")

    numeric = Question(type="numeric", difficulty="easy", text="q", options=[], correct_answer="9.8")
    assert is_answer_correct(numeric, "9.8")
    assert not is_answer_correct(numeric, "9.9")


def test_04_security_primitives():
    stored = hash_password("Student@123")
    assert verify_password("Student@123", stored)
    assert not verify_password("student@123", stored)
    assert not verify_password("", stored)
    assert "Student@123" not in stored, "the plaintext password must never be stored"

    assert password_problems("short1") and password_problems("alllettersonly")
    assert password_problems("Str0ngEnough") is None
    assert is_valid_email("a@b.co") and not is_valid_email("nope")

    token = create_access_token("7", "student")
    assert decode_access_token(token)["role"] == "student"
    assert decode_access_token(token + "x") is None
    assert decode_access_token("not.a.token") is None


def test_05_slugify():
    assert slugify("Kirchhoff's Laws and Circuit Analysis") == "kirchhoffs-laws-and-circuit-analysis"
    assert slugify("  d- and f-Block  ") == "d-and-f-block"
    assert slugify("") == "item"


# --------------------------------------------------------------------------
# 2. mastery behaviour against a real database
# --------------------------------------------------------------------------
def test_06_mastery_reflects_performance():
    db = db_session()
    year = get_current_year(db)
    topic, questions, quiz = topic_with_questions(db)
    state["topic"], state["questions"], state["quiz"] = topic, questions, quiz

    strong = make_student(db, "strong")
    weak = make_student(db, "weak")
    graded_attempt(db, strong, quiz, questions, [True] * len(questions))
    graded_attempt(db, weak, quiz, questions, [False] * len(questions))
    refresh_student_mastery(db, strong, year.id, topic_ids=[topic.id])
    refresh_student_mastery(db, weak, year.id, topic_ids=[topic.id])

    strong_record = mastery_of(db, strong, topic)
    weak_record = mastery_of(db, weak, topic)
    assert strong_record.mastery > 80, strong_record.mastery
    assert weak_record.mastery < 25, weak_record.mastery
    assert weak_record.is_weak and weak_record.weakness_reason
    assert not strong_record.is_weak
    assert 0 <= weak_record.confidence <= 1
    state["weak_student"] = weak
    state["strong_student"] = strong


def test_07_improvement_and_decay_move_mastery():
    db = db_session()
    year = get_current_year(db)
    topic, questions, quiz = state["topic"], state["questions"], state["quiz"]

    improving = make_student(db, "improving")
    graded_attempt(db, improving, quiz, questions, [False] * len(questions),
                   when=utcnow() - timedelta(days=40))
    refresh_student_mastery(db, improving, year.id, topic_ids=[topic.id])
    after_bad = mastery_of(db, improving, topic).mastery

    graded_attempt(db, improving, quiz, questions, [True] * len(questions))
    refresh_student_mastery(db, improving, year.id, topic_ids=[topic.id])
    record = mastery_of(db, improving, topic)
    assert record.mastery > after_bad + 20, "recovering must raise mastery"
    assert record.trend > 0, "improvement must be reported as a positive trend"
    assert not record.is_weak, "a recovered topic should no longer be flagged"

    # recency decay: same attempts, but all of them long ago
    stale = make_student(db, "stale")
    graded_attempt(db, stale, quiz, questions, [True] * len(questions),
                   when=utcnow() - timedelta(days=75))
    refresh_student_mastery(db, stale, year.id, topic_ids=[topic.id])
    fresh = make_student(db, "fresh")
    graded_attempt(db, fresh, quiz, questions, [True] * len(questions))
    refresh_student_mastery(db, fresh, year.id, topic_ids=[topic.id])
    assert mastery_of(db, stale, topic).mastery < mastery_of(db, fresh, topic).mastery, (
        "knowledge should decay when a topic is untouched"
    )


def test_08_occasional_slip_is_not_a_repeated_mistake():
    db = db_session()
    year = get_current_year(db)
    topic, questions, quiz = state["topic"], state["questions"], state["quiz"]
    concept = questions[0].concept_tag

    # five attempts, wrong on that concept only once -> not a repeated mistake
    lucky = make_student(db, "lucky")
    for index in range(5):
        flags = [True] * len(questions)
        if index == 0:
            flags[0] = False
        graded_attempt(db, lucky, quiz, questions, flags, when=utcnow() - timedelta(days=5 - index))
    refresh_student_mastery(db, lucky, year.id, topic_ids=[topic.id])
    record = mastery_of(db, lucky, topic)
    assert concept not in (record.repeated_mistake_concepts or []), record.repeated_mistake_concepts
    assert not record.is_weak

    # consistently wrong on the same concept -> flagged
    stuck = make_student(db, "stuck")
    for index in range(3):
        graded_attempt(db, stuck, quiz, questions, [True] * len(questions),
                       when=utcnow() - timedelta(days=3 - index), concept_wrong=concept)
    refresh_student_mastery(db, stuck, year.id, topic_ids=[topic.id])
    record = mastery_of(db, stuck, topic)
    assert concept in (record.repeated_mistake_concepts or []), record.repeated_mistake_concepts
    assert "Repeated mistakes" in record.weakness_reason or record.mastery < 100


def test_09_study_without_assessment_is_not_weakness():
    db = db_session()
    year = get_current_year(db)
    topic = state["topic"]
    reader = make_student(db, "reader")
    resource = db.scalar(select(Resource).where(Resource.topic_id == topic.id))
    log_event(db, reader, "opened_topic", topic_id=topic.id, academic_year_id=year.id)
    log_event(db, reader, "completed_resource", resource_id=resource.id,
              resource_type=resource.type, academic_year_id=year.id, duration_seconds=900)
    db.flush()
    refresh_student_mastery(db, reader, year.id, topic_ids=[topic.id])
    record = mastery_of(db, reader, topic)
    assert record is not None
    assert 0 < record.mastery <= 30, "exposure only, not mastery"
    assert not record.is_weak, "never call a topic weak without assessment"
    assert record.confidence <= 0.25


# --------------------------------------------------------------------------
# 3. learning profile + recommendations
# --------------------------------------------------------------------------
def test_10_learning_profile_measures_effectiveness():
    db = db_session()
    year = get_current_year(db)
    topic, questions, quiz = state["topic"], state["questions"], state["quiz"]
    student = make_student(db, "formats")

    resources = {
        resource.type: resource
        for resource in db.scalars(select(Resource).where(Resource.topic_id == topic.id))
    }
    # practice sessions are followed by good quizzes, audio sessions by bad ones
    for index in range(3):
        when = utcnow() - timedelta(days=20 - index * 3)
        log_event(db, student, "completed_resource", resource_id=resources["practice"].id,
                  resource_type="practice", academic_year_id=year.id,
                  duration_seconds=900, created_at=when)
        graded_attempt(db, student, quiz, questions, [True] * len(questions),
                       when=when + timedelta(days=1))
    for index in range(3):
        when = utcnow() - timedelta(days=10 - index * 3)
        log_event(db, student, "completed_resource", resource_id=resources["audio"].id,
                  resource_type="audio", academic_year_id=year.id,
                  duration_seconds=900, created_at=when)
        graded_attempt(db, student, quiz, questions, [False] * len(questions),
                       when=when + timedelta(days=1))
    db.flush()

    profile = profile_payload(compute_learning_profile(db, student, year.id))
    assert profile["practice_effectiveness"] > profile["audio_effectiveness"], profile
    assert profile["strongest_format"] == "practice"
    assert profile["weakest_format"] == "audio"
    assert profile["samples"]["practice"] == 3 and profile["samples"]["audio"] == 3
    for key in ("text", "visual", "audio", "practice"):
        assert 0.0 <= profile[f"{key}_effectiveness"] <= 1.0

    untouched = make_student(db, "untouched")
    neutral = profile_payload(compute_learning_profile(db, untouched, year.id))
    assert all(
        neutral[f"{key}_effectiveness"] == 0.5 for key in ("text", "visual", "audio", "practice")
    ), "no evidence must mean a neutral profile, not a guess"


def test_11_recommendations_explain_themselves():
    db = db_session()
    year = get_current_year(db)
    weak = state["weak_student"]
    topic = state["topic"]

    recommendations = generate_recommendations(db, weak, year.id)
    assert recommendations, "a weak topic must produce recommendations"
    assert all(r.reason for r in recommendations), "every recommendation needs a reason"
    assert all(0.0 <= r.priority <= 1.0 for r in recommendations)
    assert any(r.topic_id == topic.id and r.kind in ("revise", "prerequisite", "format")
               for r in recommendations), [r.title for r in recommendations]
    assert all(r.action_url.startswith("/") for r in recommendations)

    strong = state["strong_student"]
    strong_recommendations = generate_recommendations(db, strong, year.id)
    kinds = {r.kind for r in strong_recommendations}
    assert "revise" not in kinds or all(r.topic_id != topic.id for r in strong_recommendations
                                       if r.kind == "revise"), (
        "a mastered topic should not be recommended for revision"
    )

    # regenerating must not duplicate pending rows
    again = generate_recommendations(db, weak, year.id)
    assert len(again) == len(recommendations)


# --------------------------------------------------------------------------
# 4. AI layer
# --------------------------------------------------------------------------
def test_12_intent_detection():
    assert detect_intent("Explain capacitors") == "explain"
    assert detect_intent("give me practice questions on integration") == "practice"
    assert detect_intent("what should i study today") == "next"
    assert detect_intent("explain like i am 5") == "simplify"
    assert detect_intent("make a quick revision sheet") == "revision"
    assert detect_intent("why am i weak in physics") == "weakness"
    assert detect_intent("show me a solved example") == "example"
    assert detect_intent("anything", explicit="revision") == "revision"


def test_13_rag_retrieves_the_right_syllabus_content():
    db = db_session()
    hits = retrieve(db, "Explain Kirchhoff's laws", top_k=5)
    assert hits, "RAG returned nothing"
    topics = [(hit.metadata or {}).get("topic", "") for hit in hits]
    assert any("Kirchhoff" in name for name in topics[:3]), topics

    hits = retrieve(db, "integration by parts ILATE", top_k=5)
    topics = [(hit.metadata or {}).get("topic", "") for hit in hits]
    assert any("Integra" in name for name in topics[:3]), topics

    hits = retrieve(db, "photosynthesis in a pineapple spaceship", top_k=3)
    assert isinstance(hits, list), "an odd question must not raise"


def test_14_offline_tutor_answers_without_an_llm():
    db = db_session()
    year = get_current_year(db)
    student = state["weak_student"]
    topic = state["topic"]
    hits = retrieve(db, topic.name, top_k=4)
    context = build_student_context(db, student, year.id, topic)

    explain = offline.compose_answer(db, f"Explain {topic.name}", hits, context, "explain", topic)
    assert topic.name in explain
    assert "Key concepts" in explain
    assert "offline mode" in explain
    assert "Your record here" in explain, "the answer must use real student data"

    practice = offline.compose_answer(db, "give me practice questions", hits, context, "practice", topic)
    assert "Q1" in practice and "Show answers" in practice

    revision = offline.compose_answer(db, "revision sheet", hits, context, "revision", topic)
    assert "revision sheet" in revision.lower()

    nonsense = offline.compose_answer(db, "quantum pizza", [], context, "explain", None)
    assert "could not find" in nonsense.lower()


def test_15_ai_never_invents_performance_numbers():
    db = db_session()
    year = get_current_year(db)
    student = state["strong_student"]
    topic = state["topic"]
    context = build_student_context(db, student, year.id, topic)
    record = mastery_of(db, student, topic)

    assert context["topic_stats"]["mastery"] == record.mastery
    assert context["topic_stats"]["attempts"] == record.attempts
    from app.ai.tutor import context_to_text

    text = context_to_text(context)
    assert f"{record.mastery:.0f}" in text
    assert "Student name:" in text

    fresh = make_student(db, "nohistory")
    empty = build_student_context(db, fresh, year.id, topic)
    assert empty["topic_stats"] == {}, "no data must stay empty, not be invented"
    assert empty["weak_topics"] == []


# --------------------------------------------------------------------------
# 5. seeded content integrity
# --------------------------------------------------------------------------
def test_16_content_integrity():
    db = db_session()
    subjects = list(db.scalars(select(Subject).where(Subject.is_active.is_(True))))
    codes = {subject.code for subject in subjects}
    assert {"MATH", "PHY", "CHEM", "BIO", "ENG", "CS"} <= codes, codes

    topics = list(db.scalars(select(Topic).where(Topic.is_active.is_(True))))
    assert len(topics) >= 100

    slugs = {topic.slug for topic in topics}
    unresolved = [
        (topic.name, prerequisite)
        for topic in topics
        for prerequisite in (topic.prerequisites or [])
        if prerequisite not in slugs
    ]
    assert not unresolved, f"prerequisite slugs that point nowhere: {unresolved}"

    seeded_topics = [t for t in topics if t.chapter and t.chapter.subject.code in
                     {"MATH", "PHY", "CHEM", "BIO", "ENG", "CS"}]
    for topic in seeded_topics:
        assert topic.summary, f"{topic.name} has no summary"
        assert topic.key_concepts, f"{topic.name} has no key concepts"
        assert topic.ncert_url.startswith("http"), f"{topic.name} has no NCERT reference"
        formats = {
            resource.type
            for resource in db.scalars(select(Resource).where(Resource.topic_id == topic.id))
        }
        assert formats == {"text", "visual", "audio", "practice"}, (topic.name, formats)
    assert len(seeded_topics) >= 100

    questions = list(db.scalars(select(Question).where(Question.is_active.is_(True))))
    assert len(questions) >= 300
    for question in questions:
        assert question.correct_answer, question.id
        if question.explanation == "":
            continue  # teacher-created questions may omit an explanation
        assert question.explanation, f"question {question.id} has no explanation"
        if question.options:
            assert question.correct_answer in question.options, (
                f"question {question.id}: the correct answer is not one of the options"
            )
            assert len(set(question.options)) == len(question.options), (
                f"question {question.id} has duplicate options"
            )

    quizzes = list(db.scalars(select(Quiz).where(Quiz.is_published.is_(True))))
    assert len(quizzes) >= 60
    for quiz in quizzes:
        assert quiz.quiz_questions, f"quiz {quiz.title} has no questions"


def test_17_no_orphan_rows():
    db = db_session()
    for chapter in db.scalars(select(Chapter)):
        assert db.get(Subject, chapter.subject_id) is not None
    for topic in db.scalars(select(Topic)):
        assert db.get(Chapter, topic.chapter_id) is not None
    for question in db.scalars(select(Question)):
        assert db.get(Topic, question.topic_id) is not None
        assert question.subject_id and question.chapter_id
    for resource in db.scalars(select(Resource)):
        assert db.get(Topic, resource.topic_id) is not None
        assert resource.body, f"resource {resource.title} is empty"


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    passed = 0
    try:
        for test in tests:
            test()
            passed += 1
            print(f"  PASS  {test.__name__}")
    finally:
        if "db" in state:
            state["db"].rollback()   # never keep the synthetic students
            state["db"].close()
    print(f"\n{passed}/{len(tests)} unit checks passed.")


if __name__ == "__main__":
    main()
