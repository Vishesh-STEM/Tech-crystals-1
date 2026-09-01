# Vidyalaya AI

**Learn smarter. Study what matters.**

A complete, working, personalised Class 12 (CBSE / NCERT-aligned) Learning
Management System: mastery tracking, weak-topic detection with reasons, an
adaptive recommendation engine, a resource-effectiveness learning profile, a
full quiz system, teacher analytics and an AI tutor that answers from *your*
syllabus using RAG — running on a **free local LLM (Ollama)** with an **offline
answer engine** so nothing breaks when Ollama is not installed.

No paid APIs. No API keys. Everything runs on your own machine.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Quick start (Docker)](#quick-start-docker)
- [Quick start (local, no Docker)](#quick-start-local-no-docker)
- [Demo credentials](#demo-credentials)
- [Environment variables](#environment-variables)
- [Database setup and migrations](#database-setup-and-migrations)
- [Seed data](#seed-data)
- [Ollama setup](#ollama-setup)
- [How the algorithms work](#how-the-algorithms-work)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Moodle integration plan](#moodle-integration-plan)
- [Pinecone migration plan](#pinecone-migration-plan)
- [Troubleshooting](#troubleshooting)
- [Content and licensing note](#content-and-licensing-note)

---

## Features

**For students**

- **Dashboard** — greeting, overall progress, per-subject mastery, "needs
  attention" with the reason each topic was flagged, today's ranked plan, and
  "continue learning".
- **Six subjects** — Mathematics, Physics, Chemistry, Biology, English,
  Computer Science → 65 chapters → 106 topics → 424 resources → 348 questions →
  84 quizzes, all NCERT-aligned with official reference links.
- **Four resource formats per topic** — text, visual (diagram walkthrough),
  audio (revision script) and practice. No audio/video files are generated;
  the platform tracks *format effectiveness*, which is the point.
- **Real quiz system** — start, answer, submit, score, correct answers,
  explanations, per-topic and per-difficulty breakdown, retry, full history.
- **Topic mastery 0–100** — transparent formula (recent scores, historical
  scores, attempts, question difficulty, repeated mistakes, improvement,
  recency). Never flags a topic from one bad question.
- **Weak-topic detection** — multi-signal, with a plain-English reason:
  *"You have scored below 50% in your last 3 attempts on this topic."*
- **Recommendation engine** — revision, targeted practice, prerequisite
  repair, spaced refresh, stretch work and format nudges, each with a reason
  and a priority.
- **Learning profile** — measured effectiveness of text / visual / audio /
  practice, computed from quizzes taken *after* using each format. It is an
  adaptive resource-preference signal, explicitly **not** a permanent
  "visual learner" label.
- **AI tutor (/chat)** — question → embedding → vector search over your own
  content → student context → Ollama → answer → logged → analytics updated.
  Explains, simplifies, gives examples, generates practice, plans revision.
- **Progress** — subject mastery chart, monthly improvement, weak/strong
  topics, resource-effectiveness radar, activity chart, full quiz history,
  multi-year history that is never deleted.

**For teachers / admins**

- Class overview: students, class average, subject performance, most common
  weak topics, live activity feed, leaderboard, quiz statistics.
- Full CRUD for subjects, chapters, topics, resources, questions and quizzes.
- Per-student drill-down with weak topics and recent attempts.
- One-click rebuild of the AI vector index after editing content.
- Role-based access control; students cannot reach any admin route.

**Platform**

- JWT auth, hashed passwords, request validation, SQL-injection-safe ORM
  queries, strict student data isolation, soft deletes that preserve history.
- Light/dark mode, responsive layout, sidebar + top navigation, cards,
  progress bars, charts, toasts, loading/empty/error states everywhere.
- Works with PostgreSQL (production) or SQLite (development fallback).

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│  React 18 + TypeScript + Tailwind (Vite)                               │
│  pages/ (21 routes)  components/  context/ (auth, theme, toast)        │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ REST  /api/*  (JWT bearer)
┌───────────────────────────────▼────────────────────────────────────────┐
│  FastAPI                                                               │
│  api/routes: auth · catalog · quiz · student · chat · admin · system   │
│  ├── services/   mastery · recommendations · learning_profile ·        │
│  │               activity · quiz · academic                            │
│  ├── ai/         tutor · rag · embeddings · ollama_client · offline    │
│  ├── vector/     VectorStore → Chroma | in-memory | Pinecone (ready)   │
│  ├── ml/         predictor interfaces + rule-based impls + trainer     │
│  ├── integrations/ moodle service layer (disabled by default)          │
│  └── seed/       editable content packs + realistic demo history       │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ SQLAlchemy 2.0 (+ Alembic)
┌───────────────────────────────▼────────────────────────────────────────┐
│  PostgreSQL (production)  ·  SQLite (development fallback)             │
└────────────────────────────────────────────────────────────────────────┘
        │                                   │
        │ embeddings (TF-IDF+SVD, local)    │ HTTP
┌───────▼───────────────┐          ┌────────▼─────────────┐
│ ChromaDB (local)      │          │ Ollama (local LLM)   │
│ → in-memory fallback  │          │ → offline fallback   │
└───────────────────────┘          └──────────────────────┘
```

Design rules that matter:

- **Nothing is mandatory.** ChromaDB missing → built-in numpy/JSON vector
  store. Ollama missing → offline answer engine. PostgreSQL missing → SQLite.
  The app never crashes because an optional dependency is absent.
- **The AI never invents student data.** Performance numbers are passed to the
  model as facts and the system prompt forbids extending them.
- **Every service is behind an interface** (`VectorStore`, `Embedder`,
  `WeaknessPredictor`, `MasteryPredictor`, `RecommendationRanker`,
  `MoodleService`) so implementations can be swapped without touching callers.

---

## Requirements

| | |
| --- | --- |
| Python | 3.10+ (3.11 recommended) |
| Node | 18+ (20 recommended) |
| Database | PostgreSQL 14+ (optional — SQLite works out of the box) |
| Ollama | optional, for the local LLM |
| Docker | optional, for the one-command setup |

---

## Quick start (Docker)

```bash
git clone <your-repo> vidyalaya-ai && cd vidyalaya-ai
cp .env.example .env            # optional: edit SECRET_KEY
docker compose up --build
```

- Frontend → <http://localhost:5173>
- API docs → <http://localhost:8000/docs>

The backend creates the schema, seeds all six subjects with demo students and
builds the RAG index on first boot.

With a local model too:

```bash
docker compose --profile ai up --build
docker exec -it vidyalaya-ollama ollama pull llama3.2:1b
```

---

## Quick start (local, no Docker)

**1. Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# optional extras (ChromaDB + sentence-transformers):
# pip install -r requirements-ai.txt

cp ../.env.example ../.env                             # optional
python -m app.seed.seed --reset --index                # seed + build the AI index
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (second terminal)

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api to :8000)
```

Open <http://localhost:5173> and log in with the demo student below.

---

## Demo credentials

| Role | Email | Password |
| --- | --- | --- |
| **Student** | `abhinav@student.vidyalaya.ai` | `Student@123` |
| **Teacher** | `teacher@vidyalaya.ai` | `Teacher@123` |
| **Admin** | `admin@vidyalaya.ai` | `Admin@123` |
| Other students | `ananya@…`, `rohan@…`, `meera@…`, `kabir@…`, `ishita@…`, `aarav@…`, `zoya@…` (`@student.vidyalaya.ai`) | `Student@123` |

The login screen has one-click buttons that fill these in. The demo student
arrives with four months of simulated study history — quiz attempts, resource
usage and activity events — from which the platform *computes* mastery, weak
topics, the learning profile and recommendations. None of those numbers are
hard-coded.

You can also register a brand-new account to see the empty states and walk the
whole journey yourself.

---

## Environment variables

Copy `.env.example` → `.env`. Everything has a working default; the ones you are
most likely to change:

| Variable | Default | Meaning |
| --- | --- | --- |
| `SECRET_KEY` | dev placeholder | **Change in production.** Signs JWTs. |
| `DATABASE_URL` | `sqlite:///./vidyalaya.db` | Use `postgresql+psycopg2://user:pass@host:5432/db` in production. |
| `ALLOW_SQLITE_FALLBACK` | `true` | Fall back to SQLite if PostgreSQL is unreachable. |
| `OLLAMA_ENABLED` / `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `true` / `http://localhost:11434` / `llama3.2:1b` | Local LLM. |
| `EMBEDDING_BACKEND` | `local` | `local` (TF-IDF+SVD, no downloads) or `sentence-transformers`. |
| `VECTOR_BACKEND` | `chroma` | `chroma`, `memory` or `pinecone`. |
| `RAG_TOP_K` | `5` | Passages retrieved per question. |
| `SEED_ON_STARTUP` | `true` | Seed automatically when the database is empty. |
| `MOODLE_ENABLED` | `false` | Turns on the Moodle service layer. |

Frontend (`frontend/.env`): `VITE_API_BASE_URL` (leave empty to use the dev
proxy) and `VITE_API_TARGET`.

---

## Database setup and migrations

SQLite needs nothing. For PostgreSQL:

```bash
createdb vidyalaya
export DATABASE_URL=postgresql+psycopg2://vidyalaya:vidyalaya@localhost:5432/vidyalaya
alembic upgrade head        # from the repository root
```

See [`database/README.md`](database/README.md) for the full schema map and the
Alembic workflow (`alembic revision --autogenerate -m "..."`).

---

## Seed data

```bash
cd backend
python -m app.seed.seed --reset --index   # everything, from scratch
python -m app.seed.seed --no-history      # curriculum only (no demo history)
```

What gets created: 2 academic years, 6 subjects, 65 chapters, 106 topics,
424 resources (4 formats each), 348 questions, 84 quizzes, 1 teacher, 1 admin,
8 students, ~170 quiz attempts with answers, ~2 500 activity events, monthly
mastery snapshots, learning profiles and recommendations.

The curriculum lives in editable Python packs — `backend/app/seed/content/`
(`physics.py`, `mathematics.py`, …). Add a chapter or topic there and re-run the
seeder; nothing else needs to change.

---

## Ollama setup

```bash
# 1. install (https://ollama.com/download) - macOS/Linux one-liner:
curl -fsSL https://ollama.com/install.sh | sh

# 2. pull a small free model
ollama pull llama3.2:1b        # ~1.3 GB, runs on a laptop CPU
# alternatives: llama3.2:3b, qwen2.5:1.5b, phi3:mini

# 3. Ollama serves on http://localhost:11434 automatically
ollama list                    # confirm the model is there
```

Set `OLLAMA_MODEL` in `.env` to whatever you pulled. Check the wiring at
`GET /api/chat/status` or in **Settings → Platform status**.

**Without Ollama nothing breaks.** The tutor switches to offline mode: it
retrieves the same syllabus passages, adds your mastery data and the
recommendation engine, and composes a structured answer. The UI shows an
unobtrusive *"AI tutor is running in offline mode"* note.

---

## How the algorithms work

### Topic mastery (0–100)

For every (student, topic, academic year):

1. Group all graded answers on that topic by attempt → a chronological list of
   per-attempt scores.
2. `recent` = recency-weighted mean of the last three scores (0.5 / 0.3 / 0.2).
3. `base = 0.65 × recent + 0.35 × mean(all scores)`.
4. Blend in a **difficulty-aware accuracy** (easy 0.8, medium 1.0, hard 1.3):
   `mastery = 0.75 × base + 0.25 × difficulty_accuracy`.
5. `+ improvement` (trend × 0.15, capped −6 … +8).
6. `− repeated mistakes` (a concept missed ≥2 times **and** in ≥50% of the times
   it was asked): −2 each, max −6.
7. `+ engagement` (completed resources): max +4.
8. `− recency decay` once a topic is untouched for 14+ days, max −10.
9. Clamp to 0–100 and store a `confidence` from the amount of evidence.

A topic with study activity but no assessment gets a low-confidence "exposure"
score instead, and is never called weak.

### Weak-topic detection

Requires at least 3 answered questions, then scores signals: mastery < 50 (2),
average < 50 (2), last three attempts all below 50% (2), repeated concept
mistakes (2), declining trend (1), softer variants (1 each). Totals map to
`high` (≥5), `medium` (3–4), `low` (1–2); `is_weak` is medium or high. The
stored `weakness_reason` is the sentence the UI shows.

### Recommendation engine

Candidates: revise weak topics · repair prerequisites · targeted practice for
45–75 mastery · stretch work above 85 · spaced refresh after 14 idle days ·
resume opened-but-unassessed topics · format nudge from the learning profile.
Each gets a priority (0–1), duplicates per topic are removed, the top 8 are
persisted with their reason and an action URL.

### Learning profile (resource effectiveness)

For each format, find quizzes taken on the same topic within 7 days *after*
using a resource of that format, take the accuracy, weight it by completion and
sample size, and blend with a neutral prior (0.5, weight 2) so a single quiz
cannot swing it. Result: four numbers in 0–1 that move as the student studies.

### RAG pipeline

`question → embedding (TF-IDF+SVD or MiniLM) → vector search (Chroma or the
built-in store) → top-k syllabus passages → student context (mastery, weak
topics, learning profile, pending recommendations) → Ollama → answer → chat
message + activity event → learning profile recomputed`. If the vector search
returns nothing useful, a database keyword search takes over.

More detail in [`docs/algorithms.md`](docs/algorithms.md).

---

## API reference

Interactive docs: <http://localhost:8000/docs> (OpenAPI at `/openapi.json`).

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create a student account |
| `POST` | `/api/auth/login` | Get a JWT |
| `GET/PATCH` | `/api/auth/me` | Current user / update profile |
| `POST` | `/api/auth/change-password` | Change password |
| `GET` | `/api/subjects`, `/api/subjects/{id}` | Subjects with progress |
| `GET` | `/api/chapters/{id}`, `/api/topics/{id}` | Chapter / topic detail |
| `GET` | `/api/topics/{id}/resources`, `/api/topics/{id}/questions` | Study material, practice |
| `GET` | `/api/resources/{id}` | Open a resource (tracked) |
| `GET` | `/api/quizzes`, `/api/quiz/{id}` | Quiz list / detail |
| `POST` | `/api/quiz/{id}/attempt` | Start an attempt |
| `POST` | `/api/quiz/{id}/attempt/{attempt_id}/submit` | Submit → grade → update mastery → recommend |
| `GET` | `/api/attempts/{id}` | Review a stored attempt |
| `GET` | `/api/student/dashboard`, `/progress`, `/mastery`, `/profile`, `/years`, `/heatmap` | Student analytics |
| `GET/POST` | `/api/student/activity` | Activity feed / track an event |
| `GET/POST` | `/api/student/recommendations`, `/refresh`, `/{id}/{action}` | Study plan |
| `POST` | `/api/chat` · `GET /api/chat/history`, `/sessions`, `/status` | AI tutor |
| `GET` | `/api/admin/analytics`, `/students`, `/students/{id}` | Teacher analytics |
| `GET/POST/PATCH/DELETE` | `/api/admin/{subjects,chapters,topics,resources,questions,quizzes}` | Content CRUD |
| `POST` | `/api/admin/reindex` | Rebuild the vector index |
| `GET` | `/api/health`, `/api/meta` | Status of DB, AI, vector store, ML, Moodle |

---

## Project structure

```
vidyalaya-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI app, CORS, bootstrap
│   │   ├── core/                   config, security (JWT + hashing), utils
│   │   ├── db/                     engine with PostgreSQL→SQLite fallback
│   │   ├── models/                 22 SQLAlchemy tables
│   │   ├── schemas/                pydantic request/response models
│   │   ├── api/routes/             auth, catalog, quiz, student, chat, admin, system
│   │   ├── services/               mastery, recommendations, learning_profile, …
│   │   ├── ai/                     tutor, rag, embeddings, ollama_client, offline
│   │   ├── vector/                 VectorStore + chroma/memory/pinecone
│   │   ├── ml/                     predictor interfaces, rules, sklearn trainer
│   │   ├── integrations/           moodle.py
│   │   └── seed/                   content packs, question/resource builders, seeder
│   ├── tests/test_journey.py       end-to-end journey test
│   ├── requirements.txt
│   └── requirements-ai.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                  21 routes incl. admin/
│   │   ├── components/             layout, UI primitives, charts, markdown
│   │   ├── context/                auth, theme, toast
│   │   └── lib/                    api client, types, formatters
│   ├── package.json  vite.config.ts  tailwind.config.js
├── database/                       Alembic migrations + schema docs
├── docker/                         backend/frontend Dockerfiles, nginx.conf
├── docs/                           architecture, algorithms, API, Moodle, Pinecone
├── scripts/                        dev helpers
├── docker-compose.yml
├── alembic.ini
├── .env.example
└── README.md
```

> The specification listed `ai/`, `ml/` and `vector/` as top-level folders. They
> are Python packages that import from the rest of the backend, so they live at
> `backend/app/ai`, `backend/app/ml` and `backend/app/vector` — same separation,
> no import gymnastics.

---

## Testing

```bash
./scripts/test.sh          # everything: 59 backend checks + 804 frontend checks
```

| Suite | Checks | Focus |
| --- | --- | --- |
| `backend/tests/test_journey.py` | 16 | the complete specified journey, end to end |
| `backend/tests/test_units.py` | 17 | mastery / weakness / learning profile / recommendations, RAG, offline tutor, content integrity |
| `backend/tests/test_security.py` | 12 | auth, RBAC, token forgery, student isolation, injection, secret exposure |
| `backend/tests/test_ollama.py` | 7 | the local-LLM path against a stub Ollama server, including every failure mode |
| `backend/tests/test_vector_stores.py` | 7 | in-memory, Chroma and Pinecone adapters plus factory degradation |
| `scripts/verify_frontend.py` | 804 | imports, API client, routes, OpenAPI paths, JSX structure, third-party exports |

Every suite runs with plain `python -m tests.<name>` (no test runner needed),
under `pytest backend/tests -v` if you prefer, and without network access - the
LLM and vector-store suites start their own stubs.

Verified in both databases: **SQLite** and **PostgreSQL 16** (all suites pass on
each), with Alembic `upgrade → downgrade → upgrade` clean on both and
`alembic check` reporting no drift from `app/models`. Cold start from an empty
database to a seeded, indexed, usable platform takes about 9 seconds; dashboard
and analytics endpoints answer in 9-55 ms on the seeded dataset.

`scripts/verify_frontend.py` is a Node-free stand-in for the build: it resolves
every import, checks every API call against the live OpenAPI schema, scans all
JSX for unbalanced tags and undefined components, and validates every symbol
imported from `lucide-react`, `recharts`, `react-router-dom`, `react` and
`axios` against export lists taken from the upstream sources. It is a safety
net, not a type checker - run `npm run typecheck` for that.

Full detail: [`docs/testing.md`](docs/testing.md).

---

## Moodle integration plan

The codebase is **not** coupled to Moodle. Everything sits behind
`backend/app/integrations/moodle.py::MoodleService`, disabled by default, and
`GET /api/meta` reports its status.

1. **Authentication** — `MoodleService.authenticate()` exchanges Moodle
   credentials for a token via `login/token.php`, reads the profile with
   `core_webservice_get_site_info`, then maps it onto a local user (create on
   first login). The rest of the app keeps using its own JWTs, so no route
   changes are needed.
2. **Web services** — `MoodleService.call()` is a thin REST wrapper; add
   functions such as `core_course_get_courses` or `core_enrol_get_enrolled_users`
   to sync classes and rosters onto `subjects` / `students`.
3. **Grade sync** — `sync_grade()` pushes quiz results into the Moodle
   gradebook (`core_grades_update_grades`); call it from
   `services/quiz.submit_attempt` behind the `MOODLE_ENABLED` flag.
4. **LTI 1.3** — `lti_launch_claims()` sketches the claim set for launching
   Vidyalaya AI as an external tool. Add a `/lti/launch` route that validates
   the JWT from the platform, maps `sub` → user, and issues a local token.
5. **Packaging** — the frontend is a static bundle, so it can be served from a
   Moodle plugin or iframed after step 4.

Details: [`docs/moodle-integration.md`](docs/moodle-integration.md).

---

## Pinecone migration plan

ChromaDB is the local default; the chatbot only ever talks to the abstract
`VectorStore` (`upsert`, `query`, `count`, `reset`).

1. `pip install pinecone`
2. Set `VECTOR_BACKEND=pinecone`, `PINECONE_API_KEY=…`, `PINECONE_INDEX=…`
3. `POST /api/admin/reindex` (or `python -m app.seed.seed --index`)

`backend/app/vector/pinecone_store.py` already implements the interface against
the Pinecone SDK — no RAG, API or UI code changes.
Details: [`docs/pinecone-migration.md`](docs/pinecone-migration.md).

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Cannot reach the Vidyalaya AI server` in the UI | Backend not running: `uvicorn app.main:app --port 8000` from `backend/`. |
| Login fails with the demo account | Database not seeded: `python -m app.seed.seed --reset --index`. |
| `sqlalchemy.exc.OperationalError` on start | PostgreSQL unreachable. Fix `DATABASE_URL`, or keep `ALLOW_SQLITE_FALLBACK=true` and let it use SQLite. |
| Chat says "offline mode" | Ollama is not running or the model is not pulled: `ollama serve`, `ollama pull llama3.2:1b`, check `OLLAMA_BASE_URL`. Everything still works. |
| Chat answers feel generic | Rebuild the index: `POST /api/admin/reindex`, or `python -m app.seed.seed --index`. |
| `No module named chromadb` in the logs | Expected — the built-in vector store is used. Install extras with `pip install -r requirements-ai.txt` to switch to Chroma. |
| CORS error in the browser | Add your origin to `CORS_ORIGINS`, or use the Vite dev proxy (default). |
| Frontend 404 on refresh in production | Serve `index.html` as the SPA fallback (already handled in `docker/nginx.conf`). |
| Port already in use | `uvicorn … --port 8001` and set `VITE_API_TARGET=http://localhost:8001`. |
| Want a clean slate | `python -m app.seed.seed --reset --index` (drops and recreates every table). |

---

## Content and licensing note

Vidyalaya AI follows the **NCERT Class 12 structure** (subjects, chapters,
topics) and links to the **official NCERT textbook pages** for every chapter. It
contains only original short summaries, concept statements, examples and
practice questions written for this project — no NCERT text is reproduced.
Some seeded questions are generated from a topic's own concept statements and
are marked as such in the admin question bank so teachers can replace them.

Built with free and open-source software throughout: FastAPI, SQLAlchemy,
PostgreSQL, React, Tailwind, Recharts, scikit-learn, ChromaDB and Ollama.
