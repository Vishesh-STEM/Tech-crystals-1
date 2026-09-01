"""Users, students and teachers."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base, TimestampMixin

ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"
ROLE_ADMIN = "admin"
ROLES = (ROLE_STUDENT, ROLE_TEACHER, ROLE_ADMIN)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(160), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=ROLE_STUDENT, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    avatar_emoji = Column(String(8), default="🎓")
    theme = Column(String(10), default="system")  # light | dark | system

    student = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher = relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def is_staff(self) -> bool:
        return self.role in (ROLE_TEACHER, ROLE_ADMIN)


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    class_level = Column(String(20), nullable=False, default="12")
    stream = Column(String(40), default="Science")
    school = Column(String(160), default="")
    roll_number = Column(String(40), default="")
    guardian_name = Column(String(160), default="")
    phone = Column(String(30), default="")
    current_academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)
    daily_goal_minutes = Column(Integer, default=45)

    user = relationship("User", back_populates="student")
    current_academic_year = relationship("AcademicYear")
    enrollments = relationship(
        "StudentAcademicYear", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def name(self) -> str:
        return self.user.full_name if self.user else ""


class Teacher(Base, TimestampMixin):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department = Column(String(80), default="")
    designation = Column(String(80), default="Teacher")

    user = relationship("User", back_populates="teacher")
