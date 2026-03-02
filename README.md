# Contract Template Manager

A version-controlled contract template management system for legal teams. Upload `.docx` templates, track versions with Git under the hood, run approval workflows, compare versions with side-by-side diffs, and get alerts when templates go stale.

**Tech Stack:** FastAPI · Streamlit · SQLAlchemy · GitPython · python-docx

---

## Quick Start

### Option 1: Start Script (Recommended)

```bash
git clone <repo-url>
cd contract-template-manager
./start.sh          # macOS/Linux
# or
start.bat           # Windows
```

This creates a virtual environment, installs dependencies, starts the API and frontend, and opens your browser.

- **API docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:8501

### Option 2: Docker Compose

```bash
docker compose up --build
```

- **API docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:8501

### Option 3: Manual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Terminal 1 — API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
streamlit run frontend/app.py --server.port 8501
```

### Load Sample Data

With the API running:

```bash
python scripts/create_sample_docx.py   # Generate sample .docx files
python scripts/seed_sample_data.py      # Seed users, templates, workflow transitions
```

This creates sample users (drafter, reviewer, approver, admin), three templates at various workflow stages, and a stale template for demo purposes.

---

## Features

- **Template Registry** — Browse, search, and filter contract templates by type, status, and owner
- **Version Control** — Upload new `.docx` versions with Git-backed history; download any previous version
- **Approval Workflow** — State machine (draft → review → approved → published → retired) with role-based transitions
- **Side-by-Side Diff** — Compare text content between any two versions of a template
- **Stale Alerts** — Dashboard highlighting published templates past their review interval

## Architecture

```
┌──────────────┐     HTTP      ┌───────────────┐     SQLite     ┌──────────┐
│  Streamlit   │ ────────────→ │   FastAPI      │ ─────────────→ │ Database │
│  (Frontend)  │  X-User-Id   │   (Backend)    │                └──────────┘
└──────────────┘               │                │     Git
                               │  Services:     │ ─────────────→ ┌──────────┐
                               │  • template    │                │ Template │
                               │  • version     │                │ Git Repo │
                               │  • workflow    │                └──────────┘
                               │  • diff        │
                               │  • stale       │
                               └───────────────┘
```

**API-first design:** The Streamlit frontend is a thin HTTP client. All business logic lives in the FastAPI backend, which can be used independently via the interactive Swagger docs at `/docs`.

## Project Structure

```
app/
  main.py               FastAPI app with lifespan
  config.py             pydantic-settings configuration (env prefix: CTM_)
  models/               SQLAlchemy ORM models
  schemas/              Pydantic request/response schemas
  api/                  Route handlers + dependency injection
  services/             Business logic (git, template, version, workflow, diff, stale)
  core/                 Workflow states enum, custom exceptions
frontend/
  app.py                Streamlit entry point
  api_client.py         HTTP wrapper for API calls
  pages/                Individual UI pages
data/sample/            Synthetic .docx templates + seed config
scripts/                Seed scripts
tests/                  pytest tests (test_api/, test_services/)
```

## Configuration

Environment variables (prefix `CTM_`, or set in `.env`):

| Variable | Default | Description |
|---|---|---|
| `CTM_DATABASE_URL` | `sqlite:///data/app.db` | Database connection string |
| `CTM_TEMPLATES_REPO_PATH` | `data/templates_repo` | Path to Git template repository |
| `CTM_API_PORT` | `8000` | API server port |
| `CTM_API_BASE_URL` | `http://localhost:8000/api` | API base URL (used by frontend) |
| `CTM_MAX_UPLOAD_SIZE_BYTES` | `10485760` (10 MB) | Maximum upload file size |
| `CTM_DEFAULT_REVIEW_INTERVAL_DAYS` | `365` | Default review interval for stale detection |

## Tests

```bash
pip install -e ".[dev]"
pytest
```

48 tests covering API endpoints (templates, versions, workflow, users, diff) and services (git, workflow, diff, stale detection, file validation).

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET/POST` | `/api/users` | List / create users |
| `GET` | `/api/users/{id}` | Get user |
| `POST` | `/api/templates` | Create template (multipart: file + metadata) |
| `GET` | `/api/templates` | List/search/filter templates |
| `GET` | `/api/templates/stale` | List stale templates |
| `GET` | `/api/templates/{id}` | Get template details |
| `PUT` | `/api/templates/{id}` | Update template metadata |
| `DELETE` | `/api/templates/{id}` | Retire template (soft-delete) |
| `POST` | `/api/templates/{id}/versions` | Upload new version |
| `GET` | `/api/templates/{id}/versions` | List versions |
| `GET` | `/api/templates/{id}/versions/{v}/download` | Download .docx |
| `POST` | `/api/templates/{id}/workflow/transition` | Transition workflow state |
| `GET` | `/api/templates/{id}/workflow/history` | Get workflow audit log |
| `GET` | `/api/templates/{id}/workflow/available-transitions` | Get available transitions |
| `GET` | `/api/templates/{id}/diff` | Compare two versions |

## License

MIT — see [LICENSE](LICENSE) for details.
