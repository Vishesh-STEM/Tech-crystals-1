"""Minimal Ollama HTTP client (free, local LLM) with cached health checks."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaUnavailable(RuntimeError):
    pass


_health_cache: Dict[str, Any] = {"checked_at": 0.0, "available": False, "detail": "", "models": []}


def check_health(force: bool = False) -> Tuple[bool, str, List[str]]:
    """Return (available, human readable detail, installed models)."""
    now = time.time()
    if not force and now - _health_cache["checked_at"] < settings.AI_HEALTH_CACHE_SECONDS:
        return _health_cache["available"], _health_cache["detail"], _health_cache["models"]

    available, detail, models = False, "", []
    if not settings.OLLAMA_ENABLED:
        detail = "Ollama disabled by configuration (OLLAMA_ENABLED=false)."
    else:
        try:
            response = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.5)
            response.raise_for_status()
            models = [m.get("name", "") for m in response.json().get("models", [])]
            base_names = {name.split(":")[0] for name in models}
            if settings.OLLAMA_MODEL in models or settings.OLLAMA_MODEL.split(":")[0] in base_names:
                available = True
                detail = f"Connected to Ollama - model {settings.OLLAMA_MODEL}."
            elif models:
                available = True
                detail = (
                    f"Ollama is running but {settings.OLLAMA_MODEL} is not pulled. "
                    f"Using {models[0]}. Run: ollama pull {settings.OLLAMA_MODEL}"
                )
            else:
                detail = (
                    f"Ollama is running but has no models. Run: ollama pull {settings.OLLAMA_MODEL}"
                )
        except Exception as exc:
            detail = f"Ollama not reachable at {settings.OLLAMA_BASE_URL} ({exc.__class__.__name__})."

    _health_cache.update(
        {"checked_at": now, "available": available, "detail": detail, "models": models}
    )
    return available, detail, models


def active_model() -> str:
    available, _detail, models = check_health()
    if not available:
        return ""
    if settings.OLLAMA_MODEL in models:
        return settings.OLLAMA_MODEL
    base_names = {name.split(":")[0]: name for name in models}
    if settings.OLLAMA_MODEL.split(":")[0] in base_names:
        return base_names[settings.OLLAMA_MODEL.split(":")[0]]
    return models[0] if models else settings.OLLAMA_MODEL


def generate(prompt: str, system: str = "", model: Optional[str] = None) -> str:
    """Single-turn completion. Raises OllamaUnavailable on any failure."""
    model = model or active_model()
    if not model:
        raise OllamaUnavailable("No Ollama model available.")
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": settings.OLLAMA_TEMPERATURE,
            "num_predict": settings.OLLAMA_NUM_PREDICT,
        },
    }
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        text = (response.json().get("response") or "").strip()
        if not text:
            raise OllamaUnavailable("Empty response from Ollama.")
        return text
    except OllamaUnavailable:
        raise
    except Exception as exc:
        raise OllamaUnavailable(str(exc)) from exc
