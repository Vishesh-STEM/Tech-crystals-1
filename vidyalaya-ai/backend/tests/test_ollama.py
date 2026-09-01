"""Tests for the local-LLM path, using a stub Ollama server.

    python -m tests.test_ollama
    pytest tests/test_ollama.py

Ollama does not have to be installed: this suite starts a tiny HTTP server that
speaks the same API (`/api/tags`, `/api/generate`), points the client at it, and
checks the whole chain - health detection, prompt construction, the answer
reaching the database, and every failure mode falling back to offline mode
instead of erroring.
"""
from __future__ import annotations

import atexit
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai import ollama_client
from app.ai.tutor import answer as tutor_answer
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Student, User
from app.services.academic import student_year

STUB = {
    "mode": "ok",            # ok | error | empty | slow | no-models
    "requests": [],          # every payload the stub received
    "reply": "**Capacitors** store charge. C = Q/V. Next step: attempt the topic quiz.",
}
state: dict = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):        # keep the test output clean
        return

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/tags":
            if STUB["mode"] == "no-models":
                return self._send(200, {"models": []})
            if STUB["mode"] == "down":
                return self._send(500, {"error": "boom"})
            return self._send(200, {"models": [{"name": settings.OLLAMA_MODEL}]})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        STUB["requests"].append(payload)
        if self.path != "/api/generate":
            return self._send(404, {"error": "not found"})
        if STUB["mode"] == "error":
            return self._send(500, {"error": "model crashed"})
        if STUB["mode"] == "empty":
            return self._send(200, {"response": "   "})
        if STUB["mode"] == "slow":
            threading.Event().wait(3.0)
        return self._send(200, {"response": STUB["reply"], "model": payload.get("model")})


def start_stub() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state["server"] = server
    host, port = server.server_address[0], server.server_address[1]
    return f"http://{host}:{port}"


def reset_health() -> None:
    ollama_client._health_cache.update({"checked_at": 0.0, "available": False, "detail": "", "models": []})


def client() -> TestClient:
    if "client" not in state:
        state["client"] = TestClient(app)
        state["client"].__enter__()
    return state["client"]


def _restore_settings() -> None:
    """Undo the global settings changes even when run under pytest."""
    if "original_url" in state:
        settings.OLLAMA_BASE_URL = state["original_url"]
    settings.OLLAMA_ENABLED = True
    reset_health()
    server = state.pop("server", None)
    if server is not None:
        server.shutdown()


def test_01_start_stub_and_detect_it():
    state["original_url"] = settings.OLLAMA_BASE_URL
    atexit.register(_restore_settings)
    settings.OLLAMA_BASE_URL = start_stub()
    settings.OLLAMA_ENABLED = True
    STUB["mode"] = "ok"
    reset_health()

    available, detail, models = ollama_client.check_health(force=True)
    assert available is True, detail
    assert settings.OLLAMA_MODEL in models
    assert settings.OLLAMA_MODEL in detail
    assert ollama_client.active_model() == settings.OLLAMA_MODEL


def test_02_generate_reaches_the_model():
    STUB["requests"].clear()
    text = ollama_client.generate("Say hello", system="You are a tutor.")
    assert text == STUB["reply"]
    sent = STUB["requests"][-1]
    assert sent["model"] == settings.OLLAMA_MODEL
    assert sent["stream"] is False
    assert sent["system"] == "You are a tutor."
    assert sent["options"]["temperature"] == settings.OLLAMA_TEMPERATURE
    assert sent["options"]["num_predict"] == settings.OLLAMA_NUM_PREDICT


def test_03_tutor_uses_the_llm_and_grounds_the_prompt():
    db = SessionLocal()
    student = db.scalar(
        select(Student).join(User).where(User.email == settings.DEMO_STUDENT_EMAIL)
    )
    year = student_year(db, student)
    STUB["requests"].clear()
    reset_health()

    result = tutor_answer(db, student, "Explain capacitors", year.id)
    assert result["mode"] == "ollama", result
    assert result["model"] == settings.OLLAMA_MODEL
    assert result["content"] == STUB["reply"]
    assert result["sources"], "the LLM answer must still cite retrieved content"

    prompt = STUB["requests"][-1]["prompt"]
    system = STUB["requests"][-1]["system"]
    assert "COURSE CONTENT" in prompt and "Capacitor" in prompt, "syllabus content must be injected"
    assert "STUDENT CONTEXT" in prompt
    assert student.user.full_name.split(" ")[0] in prompt, "the student's own data must be injected"
    assert "Explain capacitors" in prompt
    assert "Never invent the student's marks" in system
    db.close()


def test_04_server_error_falls_back_to_offline():
    db = SessionLocal()
    student = db.scalar(
        select(Student).join(User).where(User.email == settings.DEMO_STUDENT_EMAIL)
    )
    year = student_year(db, student)

    STUB["mode"] = "error"
    reset_health()
    result = tutor_answer(db, student, "Explain capacitors", year.id)
    assert result["mode"] == "offline", "a failing model must not break the tutor"
    assert "offline mode" in result["content"]
    assert result["sources"]

    STUB["mode"] = "empty"
    reset_health()
    assert tutor_answer(db, student, "Explain capacitors", year.id)["mode"] == "offline"

    STUB["mode"] = "no-models"
    reset_health()
    available, detail, _ = ollama_client.check_health(force=True)
    assert available is False and "no models" in detail.lower()
    assert tutor_answer(db, student, "Explain capacitors", year.id)["mode"] == "offline"

    STUB["mode"] = "down"
    reset_health()
    assert ollama_client.check_health(force=True)[0] is False
    assert tutor_answer(db, student, "Explain capacitors", year.id)["mode"] == "offline"
    db.close()


def test_05_timeout_falls_back_to_offline():
    db = SessionLocal()
    student = db.scalar(
        select(Student).join(User).where(User.email == settings.DEMO_STUDENT_EMAIL)
    )
    year = student_year(db, student)
    original_timeout = settings.OLLAMA_TIMEOUT_SECONDS
    settings.OLLAMA_TIMEOUT_SECONDS = 0.5
    STUB["mode"] = "slow"
    reset_health()
    try:
        result = tutor_answer(db, student, "Explain capacitors", year.id)
        assert result["mode"] == "offline", "a slow model must time out into offline mode"
    finally:
        settings.OLLAMA_TIMEOUT_SECONDS = original_timeout
        db.close()


def test_06_chat_endpoint_records_the_llm_answer():
    STUB["mode"] = "ok"
    reset_health()
    login = client().post(
        "/api/auth/login",
        json={"email": settings.DEMO_STUDENT_EMAIL, "password": settings.DEMO_STUDENT_PASSWORD},
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    status = client().get("/api/chat/status", headers=headers).json()
    assert status["mode"] == "ollama", status

    response = client().post(
        "/api/chat", headers=headers, json={"message": "Explain capacitors"}
    ).json()
    assert response["mode"] == "ollama"
    assert response["model"] == settings.OLLAMA_MODEL
    assert response["message"]["content"] == STUB["reply"]
    assert response["message"]["mode"] == "ollama"

    history = client().get(
        f"/api/chat/history?session_id={response['session_id']}", headers=headers
    ).json()
    assert history[-1]["content"] == STUB["reply"]
    assert history[-1]["mode"] == "ollama"
    assert history[-1]["model"] == settings.OLLAMA_MODEL

    # the dashboard reports the live AI mode too
    dashboard = client().get("/api/student/dashboard", headers=headers).json()
    assert dashboard["ai_status"]["mode"] == "ollama"


def test_07_disabling_ollama_is_respected():
    settings.OLLAMA_ENABLED = False
    reset_health()
    available, detail, _ = ollama_client.check_health(force=True)
    assert available is False
    assert "disabled" in detail.lower()
    settings.OLLAMA_ENABLED = True
    reset_health()


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    passed = 0
    try:
        for test in tests:
            test()
            passed += 1
            print(f"  PASS  {test.__name__}")
    finally:
        _restore_settings()
        if "client" in state:
            state["client"].__exit__(None, None, None)
    print(f"\n{passed}/{len(tests)} Ollama-path checks passed.")


if __name__ == "__main__":
    main()
