"""FastAPI dependencies: authentication, roles and per-request context."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import AcademicYear, Student, User
from app.models.user import ROLE_ADMIN, ROLE_TEACHER
from app.services.academic import student_year

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise CREDENTIALS_ERROR
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise CREDENTIALS_ERROR
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


def get_current_student(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Student:
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available to student accounts.",
        )
    return student


def require_staff(user: User = Depends(get_current_user)) -> User:
    if user.role not in (ROLE_TEACHER, ROLE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required.",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def get_active_year(
    student: Student = Depends(get_current_student), db: Session = Depends(get_db)
) -> AcademicYear:
    return student_year(db, student)
