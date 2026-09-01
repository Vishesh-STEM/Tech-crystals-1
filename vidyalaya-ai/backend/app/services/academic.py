"""Academic-year helpers. Progress from previous years is never deleted."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicYear, Student, StudentAcademicYear


def current_year_label(today: Optional[date] = None) -> str:
    today = today or date.today()
    start = today.year if today.month >= 4 else today.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def get_or_create_year(db: Session, label: Optional[str] = None) -> AcademicYear:
    label = label or current_year_label()
    year = db.scalar(select(AcademicYear).where(AcademicYear.label == label))
    if year:
        return year
    start_year = int(label.split("-")[0])
    year = AcademicYear(
        label=label,
        start_date=date(start_year, 4, 1),
        end_date=date(start_year + 1, 3, 31),
        is_current=label == current_year_label(),
    )
    db.add(year)
    db.flush()
    return year


def get_current_year(db: Session) -> AcademicYear:
    year = db.scalar(select(AcademicYear).where(AcademicYear.is_current.is_(True)))
    return year or get_or_create_year(db)


def ensure_enrolment(db: Session, student: Student, year: AcademicYear) -> StudentAcademicYear:
    link = db.scalar(
        select(StudentAcademicYear).where(
            StudentAcademicYear.student_id == student.id,
            StudentAcademicYear.academic_year_id == year.id,
        )
    )
    if not link:
        link = StudentAcademicYear(
            student_id=student.id, academic_year_id=year.id, class_level=student.class_level
        )
        db.add(link)
        db.flush()
    if student.current_academic_year_id is None:
        student.current_academic_year_id = year.id
    return link


def student_year(db: Session, student: Student) -> AcademicYear:
    """The academic year a student's activity should be recorded against."""
    if student.current_academic_year_id:
        year = db.get(AcademicYear, student.current_academic_year_id)
        if year:
            return year
    year = get_current_year(db)
    ensure_enrolment(db, student, year)
    return year
