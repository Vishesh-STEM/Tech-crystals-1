"""Curriculum catalogue: subjects -> chapters -> topics -> resources."""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base, TimestampMixin

RESOURCE_TYPES = ("text", "visual", "audio", "practice")


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    icon = Column(String(8), default="📘")
    color = Column(String(20), default="indigo")
    class_level = Column(String(20), default="12")
    ncert_url = Column(String(500), default="")
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    chapters = relationship(
        "Chapter", back_populates="subject", cascade="all, delete-orphan",
        order_by="Chapter.order_index",
    )


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("subject_id", "slug", name="uq_chapter_slug"),)

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, index=True)
    number = Column(Integer, default=1)
    description = Column(Text, default="")
    ncert_url = Column(String(500), default="")
    estimated_hours = Column(Integer, default=6)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    subject = relationship("Subject", back_populates="chapters")
    topics = relationship(
        "Topic", back_populates="chapter", cascade="all, delete-orphan",
        order_by="Topic.order_index",
    )


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("chapter_id", "slug", name="uq_topic_slug"),)

    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(220), nullable=False, index=True)
    summary = Column(Text, default="")
    key_concepts = Column(JSON, default=list)
    examples = Column(JSON, default=list)
    prerequisites = Column(JSON, default=list)  # list of topic slugs
    ncert_url = Column(String(500), default="")
    difficulty = Column(String(20), default="medium")  # easy | medium | hard
    estimated_minutes = Column(Integer, default=25)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    chapter = relationship("Chapter", back_populates="topics")
    resources = relationship(
        "Resource", back_populates="topic", cascade="all, delete-orphan",
        order_by="Resource.order_index",
    )
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")


class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(220), nullable=False)
    type = Column(String(20), nullable=False, default="text", index=True)
    description = Column(Text, default="")
    body = Column(Text, default="")          # markdown-ish study content
    external_url = Column(String(500), default="")
    ncert_url = Column(String(500), default="")
    estimated_minutes = Column(Integer, default=10)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    topic = relationship("Topic", back_populates="resources")


Index("ix_resources_topic_type", Resource.topic_id, Resource.type)
