from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ActivityIn(BaseModel):
    event_type: str = Field(min_length=3, max_length=40)
    subject_id: Optional[int] = None
    chapter_id: Optional[int] = None
    topic_id: Optional[int] = None
    resource_id: Optional[int] = None
    duration_seconds: int = Field(default=0, ge=0, le=86400)
    result: str = Field(default="", max_length=40)
    score: Optional[float] = None
    details: Dict[str, Any] = {}


class ActivityOut(ORMModel):
    id: int
    event_type: str
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    resource_id: Optional[int] = None
    resource_type: Optional[str] = ""
    duration_seconds: Optional[int] = 0
    result: Optional[str] = ""
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = {}
    created_at: datetime


class RecommendationOut(ORMModel):
    id: int
    kind: str
    title: str
    reason: Optional[str] = ""
    priority: float
    estimated_minutes: Optional[int] = 20
    action_label: Optional[str] = "Start"
    action_url: Optional[str] = ""
    status: str
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    quiz_id: Optional[int] = None
    resource_id: Optional[int] = None
    created_at: datetime


class LearningProfileOut(BaseModel):
    text_effectiveness: float
    visual_effectiveness: float
    audio_effectiveness: float
    practice_effectiveness: float
    samples: Dict[str, int]
    strongest_format: str
    weakest_format: str
    preferred_difficulty: str
    average_session_minutes: float
    study_streak_days: int
    evidence: Dict[str, Any] = {}
    note: str = (
        "These are adaptive resource-effectiveness signals computed from your own "
        "results. They change as you study - they are not a fixed learning style."
    )


class TopicMasteryOut(BaseModel):
    topic_id: int
    topic_name: str
    chapter_id: int
    chapter_name: str
    subject_id: int
    subject_name: str
    mastery: float
    attempts: int
    last_score: Optional[float] = None
    average_score: Optional[float] = None
    trend: float = 0.0
    is_weak: bool = False
    weakness_confidence: str = "none"
    weakness_reason: str = ""
    last_activity_at: Optional[datetime] = None


class SubjectProgressOut(BaseModel):
    subject_id: int
    subject_name: str
    subject_slug: str
    icon: str
    color: str
    mastery: float
    topics_total: int
    topics_started: int
    topics_mastered: int
    weak_topics: int
    study_minutes: int
    last_activity_at: Optional[datetime] = None


class ProgressOut(BaseModel):
    academic_year: str
    overall_mastery: float
    subjects: List[SubjectProgressOut]
    weak_topics: List[TopicMasteryOut]
    strong_topics: List[TopicMasteryOut]
    monthly_progress: List[Dict[str, Any]]
    quiz_history: List[Dict[str, Any]]
    study_minutes_7d: int
    quizzes_taken: int
    questions_answered: int
    accuracy: float
    streak_days: int


class DashboardOut(BaseModel):
    greeting: str
    student_name: str
    academic_year: str
    overall_mastery: float
    subjects: List[SubjectProgressOut]
    needs_attention: List[TopicMasteryOut]
    recommended_today: List[RecommendationOut]
    continue_learning: List[Dict[str, Any]]
    stats: Dict[str, Any]
    learning_profile: LearningProfileOut
    monthly_progress: List[Dict[str, Any]]
    ai_status: Dict[str, Any]
