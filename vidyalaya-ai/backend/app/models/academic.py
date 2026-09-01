"""Academic years and per-year enrolment (history is never deleted)."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base, TimestampMixin


class AcademicYear(Base, TimestampMixin):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True)
    label = Column(String(20), unique=True, nullable=False, index=True)  # e.g. 2026-27
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)


class StudentAcademicYear(Base, TimestampMixin):
    __tablename__ = "student_academic_years"
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="uq_student_year"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    class_level = Column(String(20), default="12")
    is_active = Column(Boolean, default=True)

    student = relationship("Student", back_populates="enrollments")
    academic_year = relationship("AcademicYear")
