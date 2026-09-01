# API notes

Base URL `http://localhost:8000/api` · interactive docs at `/docs`.

## Authentication

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"abhinav@student.vidyalaya.ai","password":"Student@123"}' | jq -r .access_token)

curl -s localhost:8000/api/student/dashboard -H "Authorization: Bearer $TOKEN" | jq
```

Tokens are HS256 JWTs (`sub`, `role`, `iat`, `exp`, `iss=vidyalaya-ai`).
Self-service registration always creates a **student**; teacher and admin
accounts are created by an administrator or the seeder.

## Errors

All errors return `{"detail": "human readable sentence"}`. Validation errors add
a structured `errors` array and use 422. The frontend shows `detail` directly in
a toast or inline message.

| Code | Meaning |
| --- | --- |
| 401 | missing/expired token (the client clears it and redirects to /login) |
| 403 | wrong role, or another student's data |
| 404 | unknown id, or an unpublished quiz |
| 409 | duplicate email, or re-submitting a submitted attempt |
| 422 | validation failure |

## Taking a quiz

```bash
# 1. start
curl -s -X POST localhost:8000/api/quiz/7/attempt -H "Authorization: Bearer $TOKEN"
# → {"attempt_id": 42, "questions": [...]}   (no correct answers included)

# 2. submit
curl -s -X POST localhost:8000/api/quiz/7/attempt/42/submit \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"answers":[{"question_id":11,"answer":"B. Charge","time_spent_seconds":25}],
       "duration_seconds":180}'
```

The response carries the score, a per-question review with explanations, the
recomputed mastery for every touched topic, and the freshly generated
recommendations.

Answer matching accepts the full option text (`"B. Charge"`), the bare letter
(`"b"`), the option text without its label (`"charge"`), and numeric tolerance
for numeric questions.

## Activity tracking

`POST /api/student/activity` accepts any of the tracked event types
(`opened_topic`, `completed_resource`, `spent_time`, `abandoned_topic`,
`asked_chatbot`, …) with optional subject/chapter/topic/resource ids, duration,
result and free-form `details`. Parent ids are filled in automatically from the
topic or resource, so the client only needs to send what it knows.

## AI tutor

`POST /api/chat` with `{"message": "...", "session_id": 3, "topic_id": 12,
"intent": "practice"}` — `session_id`, `topic_id` and `intent` are optional.
The response includes the answer, the retrieved sources (subject, chapter,
topic, NCERT link, score, snippet), the mode (`ollama` or `offline`), the model
name, follow-up suggestions and latency.

`GET /api/chat/status` reports the tutor mode, the configured and installed
models, the vector backend and the number of indexed passages.
