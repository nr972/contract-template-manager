# Contract Template Manager — CLAUDE.md

## Project Overview

A Contract Template Version Control & Approval System for legal teams. Manages the lifecycle of .docx contract templates: drafting, version control (Git-based), approval workflows, publication, and retirement. Includes side-by-side diff between versions and stale template detection.

**Target users:** Non-technical legal professionals (in-house counsel, legal ops, paralegals).

## How to Run

### API (FastAPI)
```bash
uvicorn ctm_app.main:app --host 0.0.0.0 --port 8000 --reload
```
API docs: http://localhost:8000/docs

### Frontend (Streamlit)
```bash
streamlit run ctm_frontend/app.py --server.port 8501
```
UI: http://localhost:8501

### Both at once
```bash
./start.sh          # macOS/Linux
start.bat           # Windows
docker compose up   # Docker
```

### Tests
```bash
pip install ".[dev]"
pytest
```

### Seed sample data
```bash
python scripts/seed_sample_data.py
```

## Architecture

**API-first:** FastAPI handles all business logic. Streamlit is a thin HTTP client that calls `http://localhost:8000/api`. The API is independently usable via Swagger docs / curl.

**Template storage:** .docx files stored in a Git repository at `data/templates_repo/`. Metadata (name, type, status, owner, versions) tracked in SQLite via SQLAlchemy. Git commit SHAs link DB version records to file content.

**Auth (MVP):** Simple user selection dropdown — no passwords. User ID passed via `X-User-Id` header. Roles (drafter, reviewer, approver, admin) enforced in the workflow state machine.

## Project Structure

```
ctm_app/                # FastAPI backend
  main.py               # App factory, lifespan (table creation, Git repo init)
  config.py             # pydantic-settings configuration
  models/               # SQLAlchemy ORM models (User, Template, TemplateVersion, WorkflowTransition)
  schemas/              # Pydantic request/response schemas
  api/                  # Route handlers (templates, versions, workflow, diff, users, health)
    deps.py             # Dependency injection (get_db, get_current_user)
    router.py           # Aggregates all route modules
  services/             # Business logic (git_service, template, version, workflow, diff, stale, file_validator)
  core/                 # Shared definitions (workflow_states enum, exceptions)
ctm_frontend/           # Streamlit UI
  app.py                # Entry point with sidebar nav + user selector
  api_client.py         # HTTP wrapper for API calls
  pages/                # Individual pages (registry, detail, upload, diff, stale)
data/
  sample/               # Synthetic .docx templates + seed_data.json
  templates_repo/       # Git repo for template files (created at runtime, gitignored)
  app.db                # SQLite database (created at runtime, gitignored)
scripts/                # Seed scripts (create_sample_docx.py, seed_sample_data.py)
tests/                  # pytest tests (test_api/, test_services/)
```

## Coding Conventions

- **Python 3.11+** with type hints on all function signatures
- **Pydantic v2** for request/response validation
- **SQLAlchemy 2.0** style: `DeclarativeBase`, `mapped_column`, `Mapped`
- **UUIDs as String(36)** for SQLite/PostgreSQL compatibility
- **FastAPI dependency injection** for DB sessions and current user
- Keep modules small and focused
- Don't over-engineer — minimum complexity for the current task

## Tech Stack

- FastAPI + Uvicorn (backend)
- SQLAlchemy + SQLite (database, designed for PostgreSQL migration)
- Pydantic v2 + pydantic-settings (validation, config)
- GitPython (template version control)
- python-docx (text extraction for diffs)
- Streamlit (frontend)
- filelock (Git write serialization)
- pytest + httpx (testing)

## Security Rules

- **File uploads:** Validate .docx extension, enforce 10MB size limit, verify parseable with python-docx. Never execute uploaded content.
- **Path traversal prevention:** Template IDs are UUIDs, validated before constructing Git paths. Filenames in Git are always hardcoded as `template.docx`.
- **SQL injection:** Prevented by SQLAlchemy ORM (never raw SQL with user input).
- **Input validation:** All API inputs validated through Pydantic schemas.
- **Soft-delete only:** Templates are retired (status change), never hard-deleted.
- **Git write safety:** filelock serializes concurrent writes to the template Git repo.

## Workflow States

```
draft → review → approved → published → retired
         ↓←↑       ↓←↑                    ↓→ draft
```

Transitions are role-restricted (see `app/core/workflow_states.py`).

## Key Patterns

- **Git repo path:** `data/templates_repo/{template_uuid}/template.docx`
- **API prefix:** all endpoints under `/api`
- **User context:** `X-User-Id` header on every request
- **Config:** Environment variables prefixed with `CTM_`, loaded from `.env`
- **Database URL default:** `sqlite:///data/app.db`
