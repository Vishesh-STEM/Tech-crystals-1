"""Activity tracking, mastery, learning profile and recommendations."""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base, TimestampMixin, utcnow

EVENT_TYPES = (
    "opened_subject", "opened_chapter", "opened_topic", "opened_resource",
    "completed_resource", "spent_time", "attempted_question", "correct_answer",
    "incorrect_answer", "started_quiz", "completed_quiz", "retook_quiz",
    "asked_chatbot", "requested_explanation", "selected_text", "selected_visual",
    "selected_audio", "selected_practice", "abandoned_topic",
    "viewed_recommendation", "completed_recommendation",
)


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(40), nullable=False, index=True)
    resource_type = Column(String(20), default="")       # text|visual|audio|practice
    duration_seconds = Column(Integer, default=0)
    result = Column(String(40), default="")              # correct|incorrect|score value
    score = Column(Float, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)

    student = relationship("Student")
    subject = relationship("Subject")
    topic = relationship("Topic")
    resource = relationship("Resource")


Index("ix_activity_student_created", ActivityEvent.student_id, ActivityEvent.created_at)
Index("ix_activity_student_topic", ActivityEvent.student_id, ActivityEvent.topic_id)


class StudentTopicMastery(Base, TimestampMixin):
    __tablename__ = "student_topic_mastery"
    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", "academic_year_id", name="uq_student_topic_year"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)

    mastery = Column(Float, default=0.0)          # 0..100
    confidence = Column(Float, default=0.0)       # 0..1 (evidence strength)
    attempts = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    last_score = Column(Float, nullable=True)
    average_score = Column(Float, nullable=True)
    best_score = Column(Float, nullable=True)
    trend = Column(Float, default=0.0)            # recent minus historical
    study_minutes = Column(Integer, default=0)
    is_weak = Column(Boolean, default=False, index=True)
    weakness_confidence = Column(String(20), default="none")  # none|low|medium|high
    weakness_reason = Column(Text, default="")
    repeated_mistake_concepts = Column(JSON, default=list)
    last_activity_at = Column(DateTime, nullable=True)

    student = relationship("Student")
    topic = relationship("Topic")
    subject = relationship("Subject")


class StudentSubjectMastery(Base, TimestampMixin):
    __tablename__ = "student_subject_mastery"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "academic_year_id", name="uq_student_subject_year"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    mastery = Column(Float, default=0.0)
    topics_started = Column(Integer, default=0)
    topics_mastered = Column(Integer, default=0)
    weak_topics = Column(Integer, default=0)
    study_minutes = Column(Integer, default=0)
    last_activity_at = Column(DateTime, nullable=True)

    subject = relationship("Subject")
    student = relationship("Student")


class MasterySnapshot(Base):
    """Monthly snapshot so historical progress is never lost."""

    __tablename__ = "mastery_snapshots"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "period", name="uq_snapshot_period"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    period = Column(String(20), nullable=False)   # YYYY-MM, or YYYY-MM|overall
    mastery = Column(Float, default=0.0)
    quizzes_taken = Column(Integer, default=0)
    study_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    subject = relationship("Subject")


class StudentLearningProfile(Base, TimestampMixin):
    """Adaptive resource-effectiveness profile (NOT a fixed 'learning style')."""

    __tablename__ = "student_learning_profiles"
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="uq_profile_student_year"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)

    text_effectiveness = Column(Float, default=0.5)
    visual_effectiveness = Column(Float, default=0.5)
    audio_effectiveness = Column(Float, default=0.5)
    practice_effectiveness = Column(Float, default=0.5)

    text_samples = Column(Integer, default=0)
    visual_samples = Column(Integer, default=0)
    audio_samples = Column(Integer, default=0)
    practice_samples = Column(Integer, default=0)

    evidence = Column(JSON, default=dict)
    preferred_difficulty = Column(String(20), default="medium")
    average_session_minutes = Column(Float, default=0.0)
    study_streak_days = Column(Integer, default=0)
    last_computed_at = Column(DateTime, nullable=True)

    student = relationship("Student")


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="SET NULL"), nullable=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)

    kind = Column(String(40), default="revise")   # revise|practice|advance|resume|prerequisite|format
    title = Column(String(300), nullable=False)
    reason = Column(Text, default="")
    priority = Column(Float, default=0.5)         # 0..1, higher = more urgent
    estimated_minutes = Column(Integer, default=20)
    action_label = Column(String(80), default="Start")
    action_url = Column(String(300), default="")
    status = Column(String(20), default="pending", index=True)  # pending|done|dismissed
    generated_by = Column(String(40), default="rules")
    completed_at = Column(DateTime, nullable=True)

    subject = relationship("Subject")
    topic = relationship("Topic")
    student = relationship("Student")
