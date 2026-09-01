from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    detail: str


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20


class HealthStatus(BaseModel):
    status: str
    app: str
    version: str
    database: str
    database_url_scheme: str
    ai_mode: str
    ai_detail: str
    vector_backend: str
    embedding_backend: str
    seeded: bool
    extras: dict[str, Any] = {}
