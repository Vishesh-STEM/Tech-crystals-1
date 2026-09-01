"""Password hashing, JWT creation/validation and small security helpers.

Password hashing uses PBKDF2-HMAC-SHA256 from the standard library so that the
project has no native build dependency. ``bcrypt`` is used automatically when
it is installed (``pip install bcrypt``) and old hashes stay verifiable.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from app.core.config import settings

try:  # pragma: no cover - optional dependency
    import bcrypt as _bcrypt
except Exception:  # pragma: no cover
    _bcrypt = None

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Return a self-describing password hash string."""
    if _bcrypt is not None:
        return "bcrypt$" + _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
    salt = os.urandom(16)
    iterations = settings.PASSWORD_HASH_ITERATIONS
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("bcrypt$"):
        if _bcrypt is None:  # pragma: no cover - defensive
            return False
        try:
            return _bcrypt.checkpw(password.encode(), stored[len("bcrypt$"):].encode())
        except Exception:
            return False
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    expected = base64.b64decode(digest_b64)
    computed = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), base64.b64decode(salt_b64), int(iterations)
    )
    return hmac.compare_digest(expected, computed)


def password_problems(password: str) -> Optional[str]:
    """Basic password policy used by registration."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain at least one letter and one number."
    return None


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


# --------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------
def create_access_token(
    subject: str, role: str, extra: Optional[Dict[str, Any]] = None
) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "iss": "vidyalaya-ai",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="vidyalaya-ai",
        )
    except Exception:
        return None
