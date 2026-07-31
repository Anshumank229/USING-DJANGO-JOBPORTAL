# Job Portal API

A role-based job portal backend built with Django REST Framework — recruiters post
jobs on behalf of a company, candidates search/apply/save jobs, and both sides get
email notifications as applications move through the pipeline. Built as a
DRF-only project (no HTML templates) with Swagger/Redoc docs, JWT auth,
filtering/search/pagination, custom permissions, and a full unit test suite.

## Features

- JWT authentication (access + refresh tokens)
- Two roles: **Recruiter** and **Candidate**, enforced with custom permission classes
- Company management (recruiters create/manage their own companies)
- Job posting, editing, closing (owner-only)
- Job search with filters (type, location, salary range, company) + free-text search
- Apply to jobs with a resume + cover letter
- Resume upload/management (a candidate can keep multiple resumes)
- Save/bookmark jobs for later
- Application tracking with a status pipeline: applied → reviewed → shortlisted / rejected / hired
- Recruiter dashboard: view all applicants for a job you posted
- Email notifications (console backend in dev) on new applications and status changes
- Pagination, filtering, search, and ordering on all list endpoints
- Interactive API docs via Swagger UI and Redoc
- Unit tests covering auth, permissions, and the full apply → review → hire flow

## Tech stack

- Django 6.0 + Django REST Framework
- `djangorestframework-simplejwt` for JWT auth
- `django-filter` for query filtering
- `drf-spectacular` for OpenAPI schema + Swagger/Redoc docs
- SQLite by default (swap to Postgres for production)

## Project structure

```
jobportal/
├── manage.py
├── requirements.txt
├── accounts/        # custom User (role field), Profile, register/login/me
│   └── tests/
├── companies/        # Company model + CRUD
│   └── tests/
├── jobs/             # Job, Resume, Application, SavedJob + all job/application logic
│   └── tests/
└── jobportal_project/  # settings, root urls
```

## Data model

```
User (role: candidate | recruiter)
 └── Profile (1:1)          — bio, skills, headline, avatar

Company (created_by → recruiter User)
 └── Job (company FK, posted_by → recruiter User)
      ├── Application (job FK, candidate FK, resume FK, status)
      └── SavedJob (job FK, candidate FK)

Resume (candidate FK) ── used by Application.resume
```

Key relationship decisions:
- `Company.created_by` and `Job.posted_by` both point at the recruiter — a job's
  serializer validates that the company you're posting for actually belongs to you.
- `Application` has `unique_together = (job, candidate)` so a candidate can't apply twice.
- `SavedJob` has `unique_together = (candidate, job)` — same idea for bookmarks.
- `Resume` is its own model (not a field on `Profile`) so a candidate can upload
  several and choose which one to attach per application.

## Production readiness

This project is set up the way a real deployment would expect, not just as a
local demo:

- **Secrets via environment variables** (`django-environ`) — `SECRET_KEY`, `DEBUG`,
  `ALLOWED_HOSTS`, etc. are read from the environment / a local `.env` file
  (see `.env.example`), never hardcoded.
- **One codebase, two databases** — SQLite locally by default; set `DATABASE_URL`
  and it switches to Postgres with no code change (`dj-database-url` parsing).
- **CORS** configured via `django-cors-headers` for a separate frontend to call this API.
- **Consistent API error shape** — a custom DRF exception handler
  (`common/exceptions.py`) wraps every error response as
  `{"error": {"message": ..., "details": ...}}` instead of DRF's default,
  which varies by exception type.
- **Rate limiting** — anonymous/authenticated throttles globally, plus a
  stricter scoped throttle on `register/` since it's public and unauthenticated.
- **Security headers** — HSTS, secure cookies, and SSL redirect automatically
  turn on when `DEBUG=False`.
- **Static files** served via WhiteNoise — works out of the box on Render/Railway/Heroku
  without a separate static file host.
- **CI** — `.github/workflows/django.yml` runs `manage.py check` and the full
  test suite on every push/PR.
- **Procfile** included for one-command deploys on Render/Railway/Heroku-style platforms.

## Setup

```bash
python3 -m venv myenv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Copy the env template and fill in real values (a working default is fine for local dev)
cp .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/api/docs/` — Swagger UI (try requests right in the browser)
- `http://127.0.0.1:8000/api/redoc/` — Redoc (cleaner read-only reference)
- `http://127.0.0.1:8000/api/schema/` — raw OpenAPI schema
- `http://127.0.0.1:8000/admin/` — Django admin

## Running tests

```bash
python manage.py test
```

13 tests cover: registration + JWT login, company creation permissions (recruiter-only,
owner-only edits), job posting permissions (recruiter-only, own-company-only), job
search/filtering, the full apply → notify → dashboard → status-update → notify flow,
save/unsave, and blocking a recruiter from applying to jobs.

## Auth flow

```bash
# 1. Register as a recruiter
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -d "username=acme_hr&email=hr@acme.com&password=StrongPass123!&password2=StrongPass123!&role=recruiter"

# 2. Get a JWT
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -d "username=acme_hr&password=StrongPass123!"
# -> {"access": "...", "refresh": "..."}

# 3. Use the access token on any authenticated endpoint
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer <access_token>"
```

## Key endpoints

### Auth (`/api/auth/`)
| Endpoint | Method | Purpose |
|---|---|---|
| `register/` | POST | Sign up as `candidate` or `recruiter` |
| `token/` | POST | Get JWT access/refresh token |
| `token/refresh/` | POST | Refresh an access token |
| `me/` | GET | Current user + profile |
| `profile/` | GET, PATCH | View/update your own profile (bio, skills, avatar, etc.) |

### Companies (`/api/companies/`)
| Endpoint | Method | Purpose |
|---|---|---|
| `companies/` | GET | List/search companies (public) |
| `companies/` | POST | Create a company (**recruiter only**) |
| `companies/<slug>/` | GET, PATCH, DELETE | View / edit / delete (**owner only** for writes) |

### Jobs (`/api/jobs/`)
| Endpoint | Method | Purpose |
|---|---|---|
| `jobs/` | GET | Search/filter jobs (public) — `?search=`, `?job_type=`, `?location=`, `?company=`, `?min_salary=`, `?max_salary=` |
| `jobs/` | POST | Post a job (**recruiter only**, must own the company) |
| `jobs/<slug>/` | GET, PATCH, DELETE | View / edit / delete (**owner only** for writes) |
| `jobs/<slug>/apply/` | POST | Apply with `resume` id + `cover_letter` (**candidate only**) |
| `jobs/<slug>/save/` | POST | Toggle save/unsave (**candidate only**) |
| `jobs/<slug>/applicants/` | GET | List applicants for your job (**job owner only**) |

### Resumes (`/api/resumes/`)
| Endpoint | Method | Purpose |
|---|---|---|
| `resumes/` | GET, POST | List / upload your own resumes (**candidate only**) |
| `resumes/<id>/` | GET, DELETE | View / delete your own resume |

### Applications (`/api/applications/`)
| Endpoint | Method | Purpose |
|---|---|---|
| `applications/` | GET | Your own applications (candidate) or applications to your jobs (recruiter) |
| `applications/<id>/` | GET | View a single application (candidate or job-owning recruiter) |
| `applications/<id>/update-status/` | PATCH | Move status forward (**job-owning recruiter only**) — sends candidate an email |
| `applications/<id>/withdraw/` | DELETE | Withdraw your own application (**candidate only**) |

### Saved jobs (`/api/saved-jobs/`)
| Endpoint | Method | Purpose |
|---|---|---|
| `saved-jobs/` | GET, POST, DELETE | List / bookmark / remove saved jobs (**candidate only**) |

## Deploying (Render example)

1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
4. Start command: `gunicorn jobportal_project.wsgi:application`
5. Add environment variables in Render's dashboard: `SECRET_KEY`, `DEBUG=False`,
   `ALLOWED_HOSTS=<your-render-domain>`, and `DATABASE_URL` (Render can provision
   a free Postgres instance and injects this automatically if you attach it).
6. Deploy — the `release` line in the `Procfile` runs migrations automatically on each deploy.

## Ideas to extend further

- Add Celery for async email sending instead of sending inline during the request
- Add full-text search on Postgres instead of `icontains`
- Add email verification on signup
- Add API versioning (`/api/v1/...`) before this ever goes to real users
