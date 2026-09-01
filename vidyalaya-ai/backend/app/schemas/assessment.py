from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class QuestionOut(ORMModel):
    """Question as shown to a student while attempting (no answer leaked)."""

    id: int
    topic_id: int
    chapter_id: int
    subject_id: int
    type: str
    difficulty: str
    text: str
    options: Optional[List[str]] = []
    marks: Optional[int] = 1
    concept_tag: Optional[str] = ""


class QuestionAdminOut(QuestionOut):
    correct_answer: str
    explanation: Optional[str] = ""
    is_active: Optional[bool] = True


class QuestionCreate(BaseModel):
    topic_id: int
    type: str = Field(default="mcq", pattern="^(mcq|true_false|numeric|short)$")
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    text: str = Field(min_length=5)
    options: List[str] = []
    correct_answer: str = Field(min_length=1)
    explanation: str = ""
    concept_tag: str = ""
    marks: int = Field(default=1, ge=1, le=10)


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    difficulty: Optional[str] = Field(default=None, pattern="^(easy|medium|hard)$")
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    concept_tag: Optional[str] = None
    marks: Optional[int] = Field(default=None, ge=1, le=10)
    is_active: Optional[bool] = None


class QuizOut(ORMModel):
    id: int
    title: str
    description: Optional[str] = ""
    subject_id: int
    chapter_id: Optional[int] = None
    topic_id: Optional[int] = None
    difficulty: Optional[str] = "mixed"
    time_limit_minutes: Optional[int] = 15
    pass_percentage: Optional[int] = 60
    is_published: Optional[bool] = True


class QuizDetail(QuizOut):
    questions: List[QuestionOut] = []
    subject_name: str = ""
    chapter_name: Optional[str] = None
    topic_name: Optional[str] = None
    question_count: int = 0
    best_score: Optional[float] = None
    attempts_count: int = 0


class QuizCreate(BaseModel):
    title: str = Field(min_length=3, max_length=220)
    description: str = ""
    subject_id: int
    chapter_id: Optional[int] = None
    topic_id: Optional[int] = None
    difficulty: str = "mixed"
    time_limit_minutes: int = Field(default=15, ge=1, le=240)
    pass_percentage: int = Field(default=60, ge=0, le=100)
    is_published: bool = True
    question_ids: List[int] = []


class QuizUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=220)
    description: Optional[str] = None
    difficulty: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(default=None, ge=1, le=240)
    pass_percentage: Optional[int] = Field(default=None, ge=0, le=100)
    is_published: Optional[bool] = None
    question_ids: Optional[List[int]] = None


class AnswerIn(BaseModel):
    question_id: int
    answer: str = Field(default="", max_length=500)
    time_spent_seconds: int = Field(default=0, ge=0, le=36000)


class AttemptSubmit(BaseModel):
    answers: List[AnswerIn] = Field(default_factory=list)
    duration_seconds: int = Field(default=0, ge=0, le=86400)


class AnswerReview(BaseModel):
    question_id: int
    question_text: str
    options: List[str] = []
    given_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str = ""
    difficulty: str = "medium"
    topic_id: int
    topic_name: str = ""
    concept_tag: str = ""


class AttemptResult(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    attempt_number: int
    score: float
    max_score: float
    accuracy: float
    passed: bool
    duration_seconds: int
    submitted_at: Optional[datetime] = None
    topic_breakdown: Dict[str, Any] = {}
    difficulty_breakdown: Dict[str, Any] = {}
    answers: List[AnswerReview] = []
    mastery_updates: List[Dict[str, Any]] = []
    new_recommendations: List[Dict[str, Any]] = []


class AttemptSummary(ORMModel):
    id: int
    quiz_id: int
    attempt_number: int
    score: float
    max_score: float
    accuracy: float
    duration_seconds: int
    submitted_at: Optional[datetime] = None
    status: str
