"""Authentication and profile endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Student, User
from app.schemas.auth import (
    AuthResponse, LoginRequest, PasswordChange, ProfileUpdate, RegisterRequest,
    StudentOut, UserOut,
)
from app.schemas.common import Message
from app.services.academic import ensure_enrolment, get_current_year, student_year

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_payload(db: Session, user: User) -> AuthResponse:
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    year_label = None
    if student:
        year_label = student_year(db, student).label
        db.commit()
    return AuthResponse(
        access_token=create_access_token(user.id, user.role),
        user=UserOut.model_validate(user),
        student=StudentOut.model_validate(student) if student else None,
        academic_year=year_label,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try logging in instead.",
        )
    user = User(
        email=payload.email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role="student",
    )
    db.add(user)
    db.flush()

    year = get_current_year(db)
    student = Student(
        user_id=user.id,
        class_level=payload.class_level,
        stream=payload.stream,
        school=payload.school,
        current_academic_year_id=year.id,
    )
    db.add(student)
    db.flush()
    ensure_enrolment(db, student, year)
    db.commit()
    db.refresh(user)
    return _auth_payload(db, user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled.")
    return _auth_payload(db, user)


@router.get("/me", response_model=AuthResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AuthResponse:
    return _auth_payload(db, user)


@router.patch("/me", response_model=AuthResponse)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthResponse:
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field in ("full_name", "avatar_emoji", "theme"):
        if field in data:
            setattr(user, field, data.pop(field))
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student:
        for field, value in data.items():
            if hasattr(student, field):
                setattr(student, field, value)
    db.commit()
    db.refresh(user)
    return _auth_payload(db, user)


@router.post("/change-password", response_model=Message)
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Your current password is incorrect."
        )
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return Message(detail="Password updated successfully.")


@router.get("/demo-credentials", response_model=dict)
def demo_credentials() -> dict:
    """Convenience endpoint used by the login screen's 'demo' buttons."""
    return {
        "student": {"email": settings.DEMO_STUDENT_EMAIL, "password": settings.DEMO_STUDENT_PASSWORD},
        "teacher": {"email": settings.DEMO_TEACHER_EMAIL, "password": settings.DEMO_TEACHER_PASSWORD},
    }
