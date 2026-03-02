from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.models import Base  # noqa: F401 — registers all models
from app.models.base import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.services.git_service import GitService

    GitService()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

from app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api")
