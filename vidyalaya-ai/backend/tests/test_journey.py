"""End-to-end test of the complete user journey.

    pytest backend/tests            # with pytest installed
    python -m tests.test_journey    # no test runner required

REGISTER -> LOGIN -> DASHBOARD -> SUBJECT -> CHAPTER -> TOPIC -> RESOURCE ->
QUIZ -> RESULT STORED -> MASTERY UPDATED -> WEAK TOPIC DETECTED ->
RECOMMENDATION CREATED -> AI CHAT (RAG) -> INTERACTION LOGGED ->
LEARNING PROFILE UPDATED -> DASHBOARD SHOWS PROGRESS
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app

EMAIL = f"journey-{uuid.uuid4().hex[:8]}@student.vidyalaya.ai"
PASSWORD = "Journey@123"
state: dict = {}


def client() -> TestClient:
    if "client" not in state:
        state["client"] = TestClient(app)
        state["client"].__enter__()
    return state["client"]


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {state['token']}"}


def test_01_register():
    response = client().post(
        "/api/auth/register",
        json={"full_name": "Journey Student", "email": EMAIL, "password": PASSWORD, "class_level": "12"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["role"] == "student"
    assert body["access_token"]
    state["token"] = body["access_token"]


def test_02_register_validation():
    bad = client().post(
        "/api/auth/register",
        json={"full_name": "X", "email": "not-an-email", "password": "short"},
    )
    assert bad.status_code == 422
    duplicate = client().post(
        "/api/auth/register",
        json={"full_name": "Journey Student", "email": EMAIL, "password": PASSWORD},
    )
    assert duplicate.status_code == 409


def test_03_login():
    wrong = client().post("/api/auth/login", json={"email": EMAIL, "password": "Wrong@1234"})
    assert wrong.status_code == 401
    response = client().post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert response.status_code == 200
    state["token"] = response.json()["access_token"]


def test_04_auth_required():
    assert client().get("/api/student/dashboard").status_code == 401
    assert client().get("/api/admin/analytics", headers=auth_headers()).status_code == 403


def test_05_dashboard_empty_state():
    response = client().get("/api/student/dashboard", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["student_name"] == "Journey Student"
    assert body["overall_mastery"] == 0.0
    # at least the six seeded subjects (a teacher may have added more)
    names = {subject["subject_name"] for subject in body["subjects"]}
    assert {"Mathematics", "Physics", "Chemistry", "Biology", "English",
            "Computer Science"} <= names, names


def test_06_browse_subject_chapter_topic():
    subjects = client().get("/api/subjects", headers=auth_headers()).json()
    assert len(subjects) >= 6
    physics = next(s for s in subjects if s["code"] == "PHY")
    state["subject_id"] = physics["id"]

    subject = client().get(f"/api/subjects/{physics['id']}", headers=auth_headers()).json()
    assert subject["chapters"], "physics should have chapters"
    chapter = next(c for c in subject["chapters"] if "Current Electricity" in c["name"])
    state["chapter_id"] = chapter["id"]

    chapter_detail = client().get(f"/api/chapters/{chapter['id']}", headers=auth_headers()).json()
    topic = next(t for t in chapter_detail["topics"] if "Kirchhoff" in t["name"])
    state["topic_id"] = topic["id"]

    topic_detail = client().get(f"/api/topics/{topic['id']}", headers=auth_headers()).json()
    assert topic_detail["key_concepts"], "topic must carry key concepts"
    assert topic_detail["ncert_url"].startswith("https://ncert.nic.in")
    assert {r["type"] for r in topic_detail["resources"]} == {"text", "visual", "audio", "practice"}
    state["resource_id"] = topic_detail["resources"][0]["id"]
    state["quiz_id"] = topic_detail["quizzes"][0]["id"]


def test_07_learn_using_resource():
    response = client().get(f"/api/resources/{state['resource_id']}", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["body"]
    completed = client().post(
        "/api/student/activity",
        headers=auth_headers(),
        json={
            "event_type": "completed_resource",
            "resource_id": state["resource_id"],
            "topic_id": state["topic_id"],
            "duration_seconds": 480,
        },
    )
    assert completed.status_code == 201
    events = client().get("/api/student/activity", headers=auth_headers()).json()
    assert {"opened_topic", "opened_resource", "completed_resource"} <= {e["event_type"] for e in events}


def test_08_take_quiz_and_store_result():
    attempt = client().post(f"/api/quiz/{state['quiz_id']}/attempt", headers=auth_headers()).json()
    assert attempt["questions"], "quiz must have questions"
    assert all("correct_answer" not in q for q in attempt["questions"]), "answers must not leak"
    state["attempt_id"] = attempt["attempt_id"]

    # answer deliberately badly so a weakness is detected
    answers = [
        {"question_id": q["id"], "answer": (q["options"][-1] if q["options"] else "x"), "time_spent_seconds": 30}
        for q in attempt["questions"]
    ]
    result = client().post(
        f"/api/quiz/{state['quiz_id']}/attempt/{state['attempt_id']}/submit",
        headers=auth_headers(),
        json={"answers": answers, "duration_seconds": 300},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["max_score"] > 0
    assert body["answers"] and body["answers"][0]["explanation"] is not None
    assert body["mastery_updates"], "mastery must be recomputed on submit"
    state["accuracy"] = body["accuracy"]

    stored = client().get(f"/api/attempts/{state['attempt_id']}", headers=auth_headers()).json()
    assert stored["accuracy"] == body["accuracy"]

    # a second attempt is allowed and numbered
    retry = client().post(f"/api/quiz/{state['quiz_id']}/attempt", headers=auth_headers()).json()
    assert retry["attempt_number"] == 2


def test_09_mastery_and_weakness():
    mastery = client().get("/api/student/mastery", headers=auth_headers()).json()
    entry = next(m for m in mastery if m["topic_id"] == state["topic_id"])
    assert 0 <= entry["mastery"] <= 100
    assert entry["questions_answered"] > 0
    assert entry["is_weak"] is True, entry
    assert entry["weakness_reason"], "a weak topic must explain why"


def test_10_recommendations_created():
    recommendations = client().get("/api/student/recommendations", headers=auth_headers()).json()
    assert recommendations, "the engine must produce recommendations"
    assert any(r["topic_id"] == state["topic_id"] for r in recommendations)
    assert all(r["reason"] for r in recommendations)
    state["recommendation_id"] = recommendations[0]["id"]

    done = client().post(
        f"/api/student/recommendations/{state['recommendation_id']}/complete", headers=auth_headers()
    )
    assert done.status_code == 200


def test_11_ai_chat_with_rag():
    status = client().get("/api/chat/status", headers=auth_headers()).json()
    assert status["mode"] in ("ollama", "offline")
    assert status["indexed_documents"] > 0

    response = client().post(
        "/api/chat",
        headers=auth_headers(),
        json={"message": "Explain Kirchhoff's laws"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["sources"], "RAG must return sources"
    assert "kirchhoff" in body["message"]["content"].lower()
    assert body["message"]["content"].strip()
    state["session_id"] = body["session_id"]

    practice = client().post(
        "/api/chat",
        headers=auth_headers(),
        json={"message": "Give me practice questions on Kirchhoff's laws", "session_id": state["session_id"]},
    ).json()
    assert "Q1" in practice["message"]["content"] or "practice" in practice["message"]["content"].lower()

    history = client().get(
        f"/api/chat/history?session_id={state['session_id']}", headers=auth_headers()
    ).json()
    assert len(history) >= 4, "every interaction is logged"


def test_12_learning_profile_updated():
    profile = client().get("/api/student/profile?recompute=true", headers=auth_headers()).json()
    for key in ("text_effectiveness", "visual_effectiveness", "audio_effectiveness", "practice_effectiveness"):
        assert 0.0 <= profile[key] <= 1.0
    assert profile["samples"]["text"] >= 1
    assert "not a fixed learning style" in profile["note"]


def test_13_dashboard_shows_progress():
    dashboard = client().get("/api/student/dashboard", headers=auth_headers()).json()
    assert dashboard["stats"]["quizzes_taken"] >= 1
    assert dashboard["needs_attention"], "weak topic must surface on the dashboard"
    assert dashboard["recommended_today"]
    assert dashboard["continue_learning"]

    progress = client().get("/api/student/progress", headers=auth_headers()).json()
    assert progress["quiz_history"]
    assert progress["weak_topics"]
    assert progress["academic_year"]


def test_14_student_data_isolation():
    demo = client().post(
        "/api/auth/login",
        json={"email": "abhinav@student.vidyalaya.ai", "password": "Student@123"},
    ).json()
    other_headers = {"Authorization": f"Bearer {demo['access_token']}"}
    blocked = client().get(f"/api/attempts/{state['attempt_id']}", headers=other_headers)
    assert blocked.status_code == 403, "students must not read another student's attempt"


def test_15_teacher_dashboard_and_crud():
    teacher = client().post(
        "/api/auth/login", json={"email": "teacher@vidyalaya.ai", "password": "Teacher@123"}
    ).json()
    headers = {"Authorization": f"Bearer {teacher['access_token']}"}

    analytics = client().get("/api/admin/analytics", headers=headers).json()
    assert analytics["students"] >= 8
    assert analytics["subject_performance"]
    assert analytics["common_weak_topics"]
    assert analytics["quiz_stats"]["attempts"] > 0

    students = client().get("/api/admin/students", headers=headers).json()
    assert len(students) >= 8
    detail = client().get(f"/api/admin/students/{students[0]['id']}", headers=headers).json()
    assert detail["subjects"]

    created = client().post(
        "/api/admin/questions",
        headers=headers,
        json={
            "topic_id": state["topic_id"],
            "text": "Kirchhoff's junction rule is based on conservation of ___",
            "options": ["A. charge", "B. energy", "C. mass", "D. flux"],
            "correct_answer": "A. charge",
            "explanation": "No charge accumulates at a junction.",
            "difficulty": "easy",
            "concept_tag": "Kirchhoff's Laws",
        },
    )
    assert created.status_code == 201, created.text
    question_id = created.json()["id"]

    invalid = client().post(
        "/api/admin/questions",
        headers=headers,
        json={
            "topic_id": state["topic_id"],
            "text": "Bad question with a mismatched answer",
            "options": ["A. one", "B. two"],
            "correct_answer": "C. three",
        },
    )
    assert invalid.status_code == 422

    quiz = client().post(
        "/api/admin/quizzes",
        headers=headers,
        json={
            "title": "Journey Test Quiz",
            "subject_id": state["subject_id"],
            "chapter_id": state["chapter_id"],
            "question_ids": [question_id],
            "time_limit_minutes": 5,
        },
    )
    assert quiz.status_code == 201
    assert client().delete(f"/api/admin/quizzes/{quiz.json()['id']}", headers=headers).status_code == 200


def test_16_health_and_meta():
    health = client().get("/api/health").json()
    assert health["status"] == "ok"
    assert health["seeded"] is True
    meta = client().get("/api/meta").json()
    assert meta["vector"]["documents"] > 0
    assert meta["moodle"]["capabilities"]
    assert meta["ml_models"]["weakness"]


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f"  PASS  {test.__name__}")
    print(f"\n{passed}/{len(tests)} journey checks passed.")
    if "client" in state:
        state["client"].__exit__(None, None, None)


if __name__ == "__main__":
    main()
