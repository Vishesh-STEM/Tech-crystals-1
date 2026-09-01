from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.security import is_valid_email, password_problems
from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    class_level: str = Field(default="12", max_length=20)
    school: str = Field(default="", max_length=160)
    stream: str = Field(default="Science", max_length=40)
    role: str = Field(default="student")

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not is_valid_email(v):
            raise ValueError("Enter a valid email address.")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        problem = password_problems(v)
        if problem:
            raise ValueError(problem)
        return v

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        # Self-service registration can only create students; teacher/admin
        # accounts are created by an administrator.
        return "student"


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    role: str
    avatar_emoji: Optional[str] = "🎓"
    theme: Optional[str] = "system"
    is_active: bool


class StudentOut(ORMModel):
    id: int
    class_level: str
    stream: Optional[str] = None
    school: Optional[str] = None
    roll_number: Optional[str] = None
    guardian_name: Optional[str] = None
    phone: Optional[str] = None
    daily_goal_minutes: Optional[int] = 45
    current_academic_year_id: Optional[int] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    student: Optional[StudentOut] = None
    academic_year: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    school: Optional[str] = Field(default=None, max_length=160)
    stream: Optional[str] = Field(default=None, max_length=40)
    roll_number: Optional[str] = Field(default=None, max_length=40)
    guardian_name: Optional[str] = Field(default=None, max_length=160)
    phone: Optional[str] = Field(default=None, max_length=30)
    avatar_emoji: Optional[str] = Field(default=None, max_length=8)
    daily_goal_minutes: Optional[int] = Field(default=None, ge=10, le=600)
    theme: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password(cls, v: str) -> str:
        problem = password_problems(v)
        if problem:
            raise ValueError(problem)
        return v
