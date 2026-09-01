from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ResourceOut(ORMModel):
    id: int
    topic_id: int
    title: str
    type: str
    description: Optional[str] = ""
    body: Optional[str] = ""
    external_url: Optional[str] = ""
    ncert_url: Optional[str] = ""
    estimated_minutes: Optional[int] = 10
    order_index: Optional[int] = 0


class TopicOut(ORMModel):
    id: int
    chapter_id: int
    name: str
    slug: str
    summary: Optional[str] = ""
    key_concepts: Optional[List[str]] = []
    examples: Optional[List[str]] = []
    prerequisites: Optional[List[str]] = []
    ncert_url: Optional[str] = ""
    difficulty: Optional[str] = "medium"
    estimated_minutes: Optional[int] = 25
    order_index: Optional[int] = 0


class ChapterOut(ORMModel):
    id: int
    subject_id: int
    name: str
    slug: str
    number: Optional[int] = 1
    description: Optional[str] = ""
    ncert_url: Optional[str] = ""
    estimated_hours: Optional[int] = 6
    order_index: Optional[int] = 0


class SubjectOut(ORMModel):
    id: int
    code: str
    name: str
    slug: str
    description: Optional[str] = ""
    icon: Optional[str] = "📘"
    color: Optional[str] = "indigo"
    ncert_url: Optional[str] = ""
    order_index: Optional[int] = 0


class SubjectCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    icon: str = "📘"
    color: str = "indigo"
    ncert_url: str = ""
    order_index: int = 0


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    ncert_url: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class ChapterCreate(BaseModel):
    subject_id: int
    name: str = Field(min_length=2, max_length=200)
    number: int = 1
    description: str = ""
    ncert_url: str = ""
    estimated_hours: int = 6


class ChapterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    number: Optional[int] = None
    description: Optional[str] = None
    ncert_url: Optional[str] = None
    estimated_hours: Optional[int] = None
    is_active: Optional[bool] = None


class TopicCreate(BaseModel):
    chapter_id: int
    name: str = Field(min_length=2, max_length=200)
    summary: str = ""
    key_concepts: List[str] = []
    examples: List[str] = []
    prerequisites: List[str] = []
    ncert_url: str = ""
    difficulty: str = "medium"
    estimated_minutes: int = 25


class TopicUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    summary: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    ncert_url: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ResourceCreate(BaseModel):
    topic_id: int
    title: str = Field(min_length=2, max_length=220)
    type: str = Field(default="text", pattern="^(text|visual|audio|practice)$")
    description: str = ""
    body: str = ""
    external_url: str = ""
    ncert_url: str = ""
    estimated_minutes: int = 10


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=220)
    type: Optional[str] = Field(default=None, pattern="^(text|visual|audio|practice)$")
    description: Optional[str] = None
    body: Optional[str] = None
    external_url: Optional[str] = None
    ncert_url: Optional[str] = None
    estimated_minutes: Optional[int] = None
    is_active: Optional[bool] = None
