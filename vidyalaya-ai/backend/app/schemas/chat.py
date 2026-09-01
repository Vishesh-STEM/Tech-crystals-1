from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[int] = None
    topic_id: Optional[int] = None
    intent: Optional[str] = Field(default=None, max_length=40)


class ChatSource(BaseModel):
    title: str
    subject: str = ""
    chapter: str = ""
    topic: str = ""
    topic_id: Optional[int] = None
    ncert_url: str = ""
    score: float = 0.0
    snippet: str = ""


class ChatMessageOut(ORMModel):
    id: int
    role: str
    content: str
    mode: Optional[str] = "offline"
    model: Optional[str] = ""
    sources: Optional[List[Dict[str, Any]]] = []
    topic_id: Optional[int] = None
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: int
    message: ChatMessageOut
    sources: List[ChatSource] = []
    mode: str
    model: str = ""
    detected_subject: Optional[str] = None
    detected_topic: Optional[str] = None
    suggestions: List[str] = []
    latency_ms: float = 0.0


class ChatSessionOut(ORMModel):
    id: int
    title: str
    last_message_at: Optional[datetime] = None
    created_at: datetime
