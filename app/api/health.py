from pathlib import Path

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    repo_path = settings.templates_repo
    git_initialized = (repo_path / ".git").exists()
    return {"status": "ok", "git_repo_initialized": git_initialized}
