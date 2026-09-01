"""Security and access-control tests.

    python -m tests.test_security
    pytest tests/test_security.py

Covers: authentication, role-based access control, token tampering, student
data isolation, privilege escalation, injection-style input, answer leakage,
and secret exposure in responses.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

state: dict = {}

PROTECTED_ROUTES = [
    ("GET", "/api/student/dashboard"),
    ("GET", "/api/student/progress"),
    ("GET", "/api/student/recommendations"),
    ("GET", "/api/student/profile"),
    ("GET", "/api/student/activity"),
    ("GET", "/api/subjects"),
    ("GET", "/api/quizzes"),
    ("GET", "/api/chat/history"),
    ("GET", "/api/admin/analytics"),
    ("GET", "/api/admin/students"),
]

ADMIN_ROUTES = [
    ("GET", "/api/admin/analytics", None),
    ("GET", "/api/admin/students", None),
    ("GET", "/api/admin/subjects", None),
    ("GET", "/api/admin/questions", None),
    ("GET", "/api/admin/quizzes", None),
    ("POST", "/api/admin/subjects", {"code": "HACK", "name": "Hacked subject"}),
    ("POST", "/api/admin/questions", {"topic_id": 1, "text": "x" * 10, "correct_answer": "y"}),
    ("PATCH", "/api/admin/subjects/1", {"name": "Renamed"}),
    ("DELETE", "/api/admin/subjects/1", None),
    ("POST", "/api/admin/reindex", None),
]


def client() -> TestClient:
    if "client" not in state:
        state["client"] = TestClient(app)
        state["client"].__enter__()
    return state["client"]


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def call(method: str, path: str, token: str | None = None, json=None):
    kwargs = {"headers": headers(token) if token else {}}
    if json is not None:
        kwargs["json"] = json
    return client().request(method, path, **kwargs)


def test_01_setup_accounts():
    student = client().post(
        "/api/auth/login",
        json={"email": "abhinav@student.vidyalaya.ai", "password": "Student@123"},
    )
    assert student.status_code == 200, student.text
    state["student_token"] = student.json()["access_token"]

    teacher = client().post(
        "/api/auth/login", json={"email": "teacher@vidyalaya.ai", "password": "Teacher@123"}
    )
    assert teacher.status_code == 200
    state["teacher_token"] = teacher.json()["access_token"]

    email = f"victim-{uuid.uuid4().hex[:8]}@student.vidyalaya.ai"
    other = client().post(
        "/api/auth/register",
        json={"full_name": "Other Student", "email": email, "password": "Other@1234"},
    )
    assert other.status_code == 201
    state["other_token"] = other.json()["access_token"]


def test_02_protected_routes_require_a_token():
    for method, path in PROTECTED_ROUTES:
        response = call(method, path)
        assert response.status_code == 401, f"{path} answered {response.status_code} without a token"
        assert "detail" in response.json()


def test_03_students_cannot_touch_admin_routes():
    for method, path, payload in ADMIN_ROUTES:
        response = call(method, path, state["student_token"], payload)
        assert response.status_code == 403, f"{method} {path} -> {response.status_code}"
    # ...and the teacher can
    assert call("GET", "/api/admin/analytics", state["teacher_token"]).status_code == 200


def test_04_tokens_cannot_be_forged():
    token = state["student_token"]
    # tampered signature
    assert call("GET", "/api/student/dashboard", token[:-3] + "abc").status_code == 401
    # signed with the wrong key
    forged = jwt.encode(
        {"sub": "1", "role": "admin", "iss": "vidyalaya-ai",
         "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        "not-the-real-secret",
        algorithm="HS256",
    )
    assert call("GET", "/api/admin/analytics", forged).status_code == 401
    # expired
    expired = jwt.encode(
        {"sub": "1", "role": "student", "iss": "vidyalaya-ai",
         "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp())},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    assert call("GET", "/api/student/dashboard", expired).status_code == 401
    # wrong issuer
    wrong_issuer = jwt.encode(
        {"sub": "1", "role": "student", "iss": "someone-else",
         "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    assert call("GET", "/api/student/dashboard", wrong_issuer).status_code == 401
    # unknown user id
    ghost = jwt.encode(
        {"sub": "999999", "role": "student", "iss": "vidyalaya-ai",
         "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    assert call("GET", "/api/student/dashboard", ghost).status_code == 401
    # garbage
    assert call("GET", "/api/student/dashboard", "Bearer-nonsense").status_code == 401


def test_05_registration_cannot_grant_privileges():
    email = f"escalate-{uuid.uuid4().hex[:8]}@student.vidyalaya.ai"
    response = client().post(
        "/api/auth/register",
        json={"full_name": "Escalation Attempt", "email": email,
              "password": "Escalate@123", "role": "admin"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "student", "self-registration must never create staff"
    assert call("GET", "/api/admin/analytics", body["access_token"]).status_code == 403


def test_06_students_cannot_read_another_students_data():
    student, other = state["student_token"], state["other_token"]

    # the demo student's first quiz attempt
    progress = call("GET", "/api/student/progress", student).json()
    assert progress["quiz_history"], "the demo student should have attempts"
    attempt_id = progress["quiz_history"][0]["attempt_id"]
    assert call("GET", f"/api/attempts/{attempt_id}", other).status_code == 403

    # recommendations of another student
    recommendations = call("GET", "/api/student/recommendations", student).json()
    if recommendations:
        target = recommendations[0]["id"]
        assert call("POST", f"/api/student/recommendations/{target}/complete", other).status_code == 404

    # chat sessions of another student
    sessions = call("GET", "/api/chat/sessions", student).json()
    if sessions:
        session_id = sessions[0]["id"]
        assert call("GET", f"/api/chat/history?session_id={session_id}", other).status_code == 404
        assert call("DELETE", f"/api/chat/sessions/{session_id}", other).status_code == 404

    # a student's own data is scoped to them
    own = call("GET", "/api/student/activity", other).json()
    assert own == [] or all("student" not in item for item in own)


def test_07_quiz_answers_are_not_leaked_before_submission():
    token = state["student_token"]
    quizzes = call("GET", "/api/quizzes", token).json()
    quiz_id = quizzes[0]["id"]

    detail = call("GET", f"/api/quiz/{quiz_id}", token).json()
    serialised = str(detail)
    for question in detail["questions"]:
        assert "correct_answer" not in question
        assert "explanation" not in question
    assert "correct_answer" not in serialised

    attempt = call("POST", f"/api/quiz/{quiz_id}/attempt", token).json()
    assert all("correct_answer" not in q for q in attempt["questions"])
    state["attempt"] = (quiz_id, attempt["attempt_id"], attempt["questions"])


def test_08_attempt_submission_is_guarded():
    quiz_id, attempt_id, questions = state["attempt"]
    student, other = state["student_token"], state["other_token"]
    payload = {
        "answers": [{"question_id": q["id"], "answer": "A", "time_spent_seconds": 5} for q in questions],
        "duration_seconds": 60,
    }
    # another student cannot submit into this attempt
    assert call("POST", f"/api/quiz/{quiz_id}/attempt/{attempt_id}/submit", other, payload).status_code == 403
    # the owner can
    first = call("POST", f"/api/quiz/{quiz_id}/attempt/{attempt_id}/submit", student, payload)
    assert first.status_code == 200, first.text
    # ...but only once
    assert call("POST", f"/api/quiz/{quiz_id}/attempt/{attempt_id}/submit", student, payload).status_code == 409
    # unknown attempt / quiz
    assert call("POST", f"/api/quiz/{quiz_id}/attempt/99999/submit", student, payload).status_code == 404
    assert call("POST", "/api/quiz/999999/attempt", student).status_code == 404


def test_09_input_validation_and_injection_attempts():
    token = state["student_token"]
    teacher = state["teacher_token"]

    # classic SQL injection strings must be treated as plain text
    for payload in ["' OR 1=1 --", "\"; DROP TABLE users; --", "%' UNION SELECT * FROM users --"]:
        response = call("GET", f"/api/admin/students?search={payload}", teacher)
        assert response.status_code == 200
        assert response.json() == [] or isinstance(response.json(), list)
        response = call("GET", f"/api/admin/questions?search={payload}", teacher)
        assert response.status_code == 200
    # the tables are still there
    assert call("GET", "/api/admin/students", teacher).json(), "students table must be intact"

    # body validation
    assert client().post("/api/auth/register", json={"full_name": "A", "email": "x", "password": "1"}).status_code == 422
    assert client().post("/api/auth/login", json={"email": "a@b.co"}).status_code == 422
    bad = client().post(
        "/api/auth/register",
        json={"full_name": "Weak Password", "email": f"weak-{uuid.uuid4().hex[:6]}@x.co",
              "password": "onlyletters"},
    )
    assert bad.status_code == 422 and "letter and one number" in bad.text

    # query validation
    assert call("GET", "/api/student/recommendations?status=everything", token).status_code == 422
    assert call("GET", "/api/student/activity?limit=99999", token).status_code == 422
    assert call("POST", "/api/student/activity", token, {"event_type": "x"}).status_code == 422

    # teacher content validation
    invalid_question = call("POST", "/api/admin/questions", teacher, {
        "topic_id": 1, "text": "Mismatched answer question",
        "options": ["A. one", "B. two"], "correct_answer": "C. three",
    })
    assert invalid_question.status_code == 422
    assert call("POST", "/api/admin/questions", teacher, {
        "topic_id": 999999, "text": "Orphan question", "options": ["A", "B"], "correct_answer": "A",
    }).status_code == 404


def test_10_responses_never_expose_secrets():
    token = state["student_token"]
    for path in ["/api/auth/me", "/api/student/dashboard", "/api/student/profile", "/api/meta", "/api/health"]:
        body = call("GET", path, token).text.lower()
        for forbidden in ("hashed_password", "password_hash", "pbkdf2", "bcrypt$", settings.SECRET_KEY.lower()):
            assert forbidden not in body, f"{path} leaked '{forbidden}'"

    teacher = state["teacher_token"]
    students = call("GET", "/api/admin/students", teacher).text.lower()
    assert "hashed_password" not in students


def test_11_password_change_requires_the_current_password():
    email = f"pw-{uuid.uuid4().hex[:8]}@student.vidyalaya.ai"
    registered = client().post(
        "/api/auth/register",
        json={"full_name": "Password Tester", "email": email, "password": "First@1234"},
    ).json()
    token = registered["access_token"]

    assert call("POST", "/api/auth/change-password", token,
                {"current_password": "Wrong@1234", "new_password": "Second@1234"}).status_code == 400
    assert call("POST", "/api/auth/change-password", token,
                {"current_password": "First@1234", "new_password": "weak"}).status_code == 422
    assert call("POST", "/api/auth/change-password", token,
                {"current_password": "First@1234", "new_password": "Second@1234"}).status_code == 200

    assert client().post("/api/auth/login", json={"email": email, "password": "First@1234"}).status_code == 401
    assert client().post("/api/auth/login", json={"email": email, "password": "Second@1234"}).status_code == 200


def test_12_soft_delete_preserves_history():
    teacher = state["teacher_token"]
    created = call("POST", "/api/admin/subjects", teacher, {
        "code": f"T{uuid.uuid4().hex[:4].upper()}", "name": "Temporary Subject",
    })
    assert created.status_code == 201
    subject_id = created.json()["id"]

    assert call("DELETE", f"/api/admin/subjects/{subject_id}", teacher).status_code == 200
    listed = call("GET", "/api/admin/subjects", teacher).json()
    archived = [s for s in listed if s["id"] == subject_id]
    assert archived and archived[0]["is_active"] is False, "delete must archive, not destroy"

    # students no longer see it
    student_subjects = call("GET", "/api/subjects", state["student_token"]).json()
    assert all(s["id"] != subject_id for s in student_subjects)


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f"  PASS  {test.__name__}")
    print(f"\n{passed}/{len(tests)} security checks passed.")
    if "client" in state:
        state["client"].__exit__(None, None, None)


if __name__ == "__main__":
    main()
