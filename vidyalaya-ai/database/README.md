# Database

PostgreSQL is the intended production database; SQLite is the zero-setup
development fallback (`app/db/session.py` switches automatically when the
configured PostgreSQL server cannot be reached and `ALLOW_SQLITE_FALLBACK=true`).

## Migrations (Alembic)

```bash
# from the repository root, with backend requirements installed
alembic upgrade head                       # create / update the schema
alembic revision --autogenerate -m "..."   # after changing app/models
alembic downgrade -1                       # roll back one revision
```

`alembic.ini` lives at the repository root, the revisions in
`database/migrations/versions/`. The environment reads `DATABASE_URL` from your
`.env` and the metadata from `backend/app/models`, so autogenerate always
compares against the real models.

For a quick start you can skip Alembic entirely: the backend calls
`Base.metadata.create_all()` on boot and seeds itself when the database is empty.

## Seeding

```bash
cd backend
python -m app.seed.seed --reset --index   # drop, recreate, seed, build the RAG index
python -m app.seed.seed --no-history      # curriculum only, no demo learning history
```

## Schema (22 tables)

| Group | Tables |
| --- | --- |
| Identity | `users`, `students`, `teachers` |
| Academic years | `academic_years`, `student_academic_years` |
| Curriculum | `subjects`, `chapters`, `topics`, `resources` |
| Assessment | `questions`, `quizzes`, `quiz_questions`, `quiz_attempts`, `answers` |
| Analytics | `activity_events`, `student_topic_mastery`, `student_subject_mastery`, `mastery_snapshots`, `student_learning_profiles`, `recommendations` |
| AI tutor | `chat_sessions`, `chat_messages` |

Key relationships:

```
users 1─1 students ─┬─* student_academic_years *─1 academic_years
                    ├─* quiz_attempts *─1 quizzes *─1 subjects
                    │        └─* answers *─1 questions *─1 topics
                    ├─* activity_events
                    ├─* student_topic_mastery   (student × topic × year, unique)
                    ├─* student_subject_mastery (student × subject × year, unique)
                    ├─* mastery_snapshots       (student × subject × month, unique)
                    ├─1 student_learning_profiles (student × year, unique)
                    ├─* recommendations
                    └─* chat_sessions ─* chat_messages

subjects 1─* chapters 1─* topics 1─* resources
                              └─* questions
```

Every table carries `created_at` / `updated_at` timestamps (except append-only
event tables which carry `created_at` only), foreign keys with sensible
`ON DELETE` behaviour, unique constraints on all natural keys, and indexes on
every column used for filtering (`student_id`, `topic_id`, `created_at`,
`event_type`, `is_weak`, ...).

Deleting content from the admin UI is a **soft delete** (`is_active = false`) so
student history is never lost.
