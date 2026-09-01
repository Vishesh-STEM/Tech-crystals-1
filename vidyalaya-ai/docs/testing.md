# Testing

```bash
./scripts/test.sh          # everything: 59 backend checks + 804 frontend checks
```

Every suite runs without a test runner (`python -m tests.<name>`) and under
`pytest backend/tests -v` if you prefer. No network access is required: the
LLM and vector-store suites start their own stubs.

## What each suite covers

| Suite | Checks | Focus |
| --- | --- | --- |
| `backend/tests/test_journey.py` | 16 | the complete specified user journey, end to end |
| `backend/tests/test_units.py` | 17 | mastery / weakness / learning-profile / recommendation behaviour, RAG, offline tutor, seeded-content integrity |
| `backend/tests/test_security.py` | 12 | authentication, RBAC, token forgery, student isolation, injection, secret exposure |
| `backend/tests/test_ollama.py` | 7 | the local-LLM path against a stub Ollama server, including every failure mode |
| `backend/tests/test_vector_stores.py` | 7 | in-memory, Chroma and Pinecone adapters plus factory degradation |
| `scripts/verify_frontend.py` | 804 | imports, API client, routes, OpenAPI paths, JSX structure, third-party exports |

### `test_journey.py`
REGISTER → validation errors → LOGIN → auth guards → empty dashboard → SUBJECT →
CHAPTER → TOPIC (four resource formats, NCERT link) → open and complete a
RESOURCE → start QUIZ (answers never leaked) → submit → RESULT STORED →
MASTERY UPDATED → WEAK TOPIC DETECTED with a reason → RECOMMENDATION CREATED →
AI CHAT with RAG sources → INTERACTION LOGGED → LEARNING PROFILE UPDATED →
DASHBOARD SHOWS PROGRESS, plus student isolation and the teacher workspace.

### `test_units.py`
Drives the real services against the database rather than restating formulas:

- mastery rises when performance improves, falls when it does not, and decays
  when a topic is left untouched for weeks;
- one slip is not a "repeated mistake", a persistent one is, and a mistake that
  has since been fixed stops counting;
- studying without being assessed never produces a weakness verdict;
- the learning profile ranks practice above audio only because the data says so,
  and stays neutral (0.5) with no evidence;
- every recommendation carries a reason, priorities are in range, regeneration
  does not duplicate, and mastered topics are not recommended for revision;
- RAG returns the right topic for "Kirchhoff's laws" and "integration by parts";
- the offline tutor produces explanations, practice sets and revision sheets
  without an LLM, and uses only real student numbers;
- content integrity: 4 resource formats per topic, correct answers present in
  the options, all 27 prerequisite slugs resolve, no orphan rows.

### `test_security.py`
10 protected routes reject anonymous calls; 10 admin routes reject students;
tampered, wrongly-signed, expired, wrong-issuer and unknown-user tokens are all
rejected; registration cannot grant a staff role; a student cannot read another
student's attempt, chat or recommendation; quiz answers are absent from every
pre-submission payload; a submitted attempt cannot be re-submitted; injection
strings are treated as text; no response contains a password hash or the secret
key; password changes need the current password; deletes archive rather than
destroy.

### `test_ollama.py`
Starts a stub server implementing `/api/tags` and `/api/generate`, then checks
health detection, the exact request payload (model, stream, system, options),
that the prompt actually contains retrieved syllabus content and the student's
own data, and that **every** failure mode - HTTP 500, empty response, no models
installed, server down, timeout, `OLLAMA_ENABLED=false` - falls back to offline
mode instead of erroring. Finally it drives `POST /api/chat` and checks the
answer is persisted with `mode=ollama` and the model name.

### `test_vector_stores.py`
Round-trips the built-in store (cosine ranking, metadata filter, persistence,
reset), then exercises the Chroma adapter through a stub package (metadata
cleaning, distance→similarity conversion, `where` filters) and the Pinecone
adapter (index creation, 100-item batching, text in metadata, score mapping).
It also checks the factory degrades pinecone → chroma → memory, and indexes the
real 530-document corpus through the Chroma adapter.

### `scripts/verify_frontend.py`
A Node-free stand-in for the build. It resolves every relative import, checks
every `endpoints.*` call exists in the API client, cross-checks each API path
against the live OpenAPI schema, verifies router wiring, scans every `.tsx`
file for unbalanced JSX tags, confirms each capitalised JSX tag is imported or
defined, and validates every symbol imported from `lucide-react`, `recharts`,
`react-router-dom`, `react` and `axios` against export lists extracted from the
upstream sources (`scripts/package_exports.json`).

It is a safety net, not a type checker: run `npm run typecheck` and
`npm run build` for the authoritative answer.

## Verified environments

| | Result |
| --- | --- |
| SQLite (default dev database) | all suites pass |
| PostgreSQL 16 | all suites pass; 22 tables, 88 indexes, 50 foreign keys, 9 unique constraints created cleanly |
| Alembic on PostgreSQL and SQLite | `upgrade head` → `downgrade base` → `upgrade head` all clean; `alembic check` reports no drift from `app/models` |
| Ollama available | stub server: answers generated, logged with the model name |
| Ollama unavailable | offline engine answers from syllabus + student data |
| ChromaDB installed | stub package: 530 documents indexed and queried |
| ChromaDB missing | built-in numpy/JSON store, same interface |
| Driver missing / bad URL | falls back to SQLite with an explanatory log line |
| `ALLOW_SQLITE_FALLBACK=false` | fails loudly, as intended |

## Performance (seeded database, 8 students, ~4 200 events)

| Endpoint | p50 |
| --- | --- |
| `GET /student/dashboard` | 26 ms |
| `GET /student/progress` | 31 ms |
| `GET /subjects` | 9 ms |
| `GET /quizzes` | 55 ms |
| `GET /admin/analytics` | 17 ms |
| `POST /chat` (offline RAG) | 51 ms |

Cold start from an empty database - schema, seed and RAG index - takes about
9 seconds.
