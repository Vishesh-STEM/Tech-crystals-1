"""All ORM models (import this module to register the full metadata)."""
from app.db.base_class import Base  # noqa: F401
from app.models.academic import AcademicYear, StudentAcademicYear  # noqa: F401
from app.models.analytics import (  # noqa: F401
    EVENT_TYPES, ActivityEvent, MasterySnapshot, Recommendation,
    StudentLearningProfile, StudentSubjectMastery, StudentTopicMastery,
)
from app.models.assessment import (  # noqa: F401
    Answer, DIFFICULTIES, Question, Quiz, QuizAttempt, QuizQuestion,
)
from app.models.catalog import Chapter, RESOURCE_TYPES, Resource, Subject, Topic  # noqa: F401
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.user import ROLES, ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER, Student, Teacher, User  # noqa: F401

__all__ = [
    "Base", "User", "Student", "Teacher", "AcademicYear", "StudentAcademicYear",
    "Subject", "Chapter", "Topic", "Resource", "Question", "Quiz", "QuizQuestion",
    "QuizAttempt", "Answer", "ActivityEvent", "StudentTopicMastery",
    "StudentSubjectMastery", "StudentLearningProfile", "Recommendation",
    "MasterySnapshot", "ChatSession", "ChatMessage",
    "ROLES", "ROLE_STUDENT", "ROLE_TEACHER", "ROLE_ADMIN",
    "RESOURCE_TYPES", "DIFFICULTIES", "EVENT_TYPES",
]
