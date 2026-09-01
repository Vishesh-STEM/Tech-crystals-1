"""Small shared helpers."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Optional


def slugify(value: str, max_length: int = 200) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    # Drop apostrophes instead of turning them into separators, so
    # "Kirchhoff's Laws" -> "kirchhoffs-laws" (matters for prerequisite slugs).
    value = re.sub(r"['\u2019\u02bc]", "", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    value = re.sub(r"-{2,}", "-", value)
    return value[:max_length] or "item"


def greeting_for(now: Optional[datetime] = None) -> str:
    hour = (now or datetime.now()).hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def percent(part: float, whole: float) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


def unique_slug(db, model, base: str, scope_column=None, scope_value=None) -> str:
    """Return a slug that is free for ``model`` (optionally within a scope).

    Two chapters called "Revision" in different subjects are fine, two in the
    same subject are not - so the caller passes the scope column when the
    uniqueness constraint is scoped.
    """
    from sqlalchemy import select

    candidate = slugify(base)
    suffix = 1
    while True:
        query = select(model).where(model.slug == candidate)
        if scope_column is not None:
            query = query.where(scope_column == scope_value)
        if db.scalar(query) is None:
            return candidate
        suffix += 1
        candidate = f"{slugify(base)}-{suffix}"
