"""AI tutor chat sessions and messages."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base, TimestampMixin, utcnow


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(220), default="New conversation")
    last_message_at = Column(DateTime, default=utcnow)

    student = relationship("Student")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)     # user | assistant
    content = Column(Text, nullable=False)
    mode = Column(String(20), default="offline")  # ollama | offline
    model = Column(String(80), default="")
    sources = Column(JSON, default=list)          # retrieved content references
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
    topic = relationship("Topic")
