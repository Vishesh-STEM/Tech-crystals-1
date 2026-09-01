# Architecture

## Layers

| Layer | Location | Responsibility |
| --- | --- | --- |
| UI | `frontend/src/pages`, `components` | 21 routes, charts, states, dark mode |
| API | `backend/app/api/routes` | HTTP, validation, RBAC, no business logic |
| Services | `backend/app/services` | mastery, weakness, recommendations, learning profile, activity, quiz lifecycle, academic years |
| AI | `backend/app/ai` | tutor orchestration, RAG, embeddings, Ollama client, offline engine |
| Vector | `backend/app/vector` | `VectorStore` interface + Chroma / in-memory / Pinecone |
| ML | `backend/app/ml` | predictor interfaces, rule-based implementations, sklearn trainer |
| Integrations | `backend/app/integrations` | Moodle service layer (disabled by default) |
| Data | `backend/app/models`, `database/` | 22 tables, Alembic migrations |

Routes never touch the ORM for anything non-trivial: they call a service and
serialise the result. That is what makes the same logic reusable from the
seeder, the tests and (later) a Moodle-triggered job.

## Request flow: submitting a quiz

```
POST /api/quiz/{id}/attempt/{attempt_id}/submit
  ├─ deps: JWT → user → student  (403 if the attempt belongs to someone else)
  ├─ services.quiz.submit_attempt
  │    ├─ grade every answer      (answers + attempt rows persisted)
  │    ├─ activity events         attempted_question / correct_answer / completed_quiz
  │    ├─ services.mastery.refresh_student_mastery(touched topics)
  │    │     ├─ recompute_topic_mastery  → mastery, confidence, trend
  │    │     ├─ detect_weakness          → level + human-readable reason
  │    │     ├─ recompute_subject_mastery
  │    │     └─ write_snapshot           → monthly history
  │    ├─ services.learning_profile.compute_learning_profile
  │    └─ services.recommendations.generate_recommendations
  └─ response: score, per-question review, mastery updates, new recommendations
```

## Failure behaviour (nothing is mandatory)

| Missing | Effect |
| --- | --- |
| PostgreSQL | falls back to SQLite (`ALLOW_SQLITE_FALLBACK`), logged as a warning |
| ChromaDB | built-in numpy/JSON vector store, same interface |
| sentence-transformers | scikit-learn TF-IDF + SVD embeddings (default anyway) |
| Ollama | offline answer engine composes from syllabus + student data |
| joblib / trained model | rule-based predictors stay in place |

## Frontend structure

- `context/AuthContext` holds the JWT (localStorage) and the current user;
  a response interceptor logs out on 401.
- `lib/api.ts` is the single place every endpoint is declared, so the
  `scripts/verify_frontend.py` checker can cross-check it against the OpenAPI
  schema.
- Every page handles four states: loading (skeletons), empty, error (with retry)
  and success.
