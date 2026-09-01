"""Questions, quizzes, attempts and answers."""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Index
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base, TimestampMixin, utcnow

DIFFICULTIES = ("easy", "medium", "hard")
QUESTION_TYPES = ("mcq", "true_false", "numeric", "short")


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), default="mcq", nullable=False)
    difficulty = Column(String(20), default="medium", nullable=False, index=True)
    text = Column(Text, nullable=False)
    options = Column(JSON, default=list)          # ["A ...", "B ..."]
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, default="")
    concept_tag = Column(String(160), default="")
    marks = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    topic = relationship("Topic", back_populates="questions")
    subject = relationship("Subject")
    chapter = relationship("Chapter")


class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    title = Column(String(220), nullable=False)
    description = Column(Text, default="")
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    difficulty = Column(String(20), default="mixed")
    time_limit_minutes = Column(Integer, default=15)
    pass_percentage = Column(Integer, default=60)
    is_published = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject = relationship("Subject")
    chapter = relationship("Chapter")
    topic = relationship("Topic")
    quiz_questions = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan",
        order_by="QuizQuestion.order_index",
    )
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="quiz_questions")
    question = relationship("Question")


class QuizAttempt(Base, TimestampMixin):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    status = Column(String(20), default="in_progress")  # in_progress | submitted
    started_at = Column(DateTime, default=utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    accuracy = Column(Float, default=0.0)          # 0..100
    topic_breakdown = Column(JSON, default=dict)
    difficulty_breakdown = Column(JSON, default=dict)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    given_answer = Column(String(500), default="")
    is_correct = Column(Boolean, default=False)
    marks_awarded = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")


Index("ix_attempts_student_quiz", QuizAttempt.student_id, QuizAttempt.quiz_id)
