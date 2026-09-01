# Moodle integration plan

Vidyalaya AI runs standalone today (its own JWT authentication) and is **not**
coupled to Moodle anywhere. Every future touch point goes through one file:
`backend/app/integrations/moodle.py`.

```python
class MoodleService:
    enabled                # MOODLE_ENABLED and base_url and token
    call(function, **params)                 # REST wrapper over webservice/rest/server.php
    authenticate(username, password)         # login/token.php  -> MoodleUser
    list_courses()                           # core_course_get_courses
    sync_grade(user_id, course_id, item, g)  # core_grades_update_grades
    lti_launch_claims(user_id, link_id)      # LTI 1.3 claim set
```

`GET /api/meta` and the teacher dashboard both surface its status.

## Step 1 — Configure a Moodle web service

1. Site administration → Advanced features → enable web services.
2. Enable the REST protocol.
3. Create an external service exposing at least
   `core_webservice_get_site_info`, `core_course_get_courses`,
   `core_enrol_get_enrolled_users`, `core_grades_update_grades`.
4. Create a token for a service account.
5. Set `MOODLE_ENABLED=true`, `MOODLE_BASE_URL=https://moodle.example.edu`,
   `MOODLE_WS_TOKEN=…`.

## Step 2 — Authentication

Add a route `POST /api/auth/moodle-login` that calls
`MoodleService.authenticate()`, then finds-or-creates the local `User`
(role from the Moodle role list) and issues the normal Vidyalaya JWT. Nothing
downstream changes: every existing endpoint keeps working because it only knows
about local users.

Store `moodle_user_id` on `users` (one Alembic migration) to link the accounts.

## Step 3 — Course and roster sync

A scheduled job (or an admin button) maps Moodle courses to `subjects` and
enrolled users to `students` / `student_academic_years`. Because the seeder and
the API both go through the same models, imported content behaves exactly like
seeded content.

## Step 4 — Grade sync

In `services/quiz.submit_attempt`, after the attempt is graded:

```python
if settings.MOODLE_ENABLED:
    get_moodle_service().sync_grade(user.moodle_user_id, course_id, quiz.title, accuracy)
```

Keep it behind the flag and wrap it in try/except: a failing LMS must never
break a student's quiz submission.

## Step 5 — LTI 1.3 launch

Add `/lti/launch` that validates the platform's signed JWT (JWKS from Moodle),
maps the `sub` claim to a local user, issues a Vidyalaya token and redirects
into the SPA. `lti_launch_claims()` already documents the expected claim set.
Deep linking can point at `/topics/{id}` or `/quiz/{id}`.

## Step 6 — Packaging

The frontend is a static bundle (`npm run build` → `dist/`), so it can be served
from a Moodle plugin directory or embedded in an iframe after step 5. The API
can stay on its own host; only `CORS_ORIGINS` needs the Moodle origin.

## What is deliberately *not* done yet

- No Moodle tables, no Moodle-specific columns beyond the optional link id.
- No hard dependency: with `MOODLE_ENABLED=false` the service raises a clear
  error if called, and nothing calls it.
