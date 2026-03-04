from contextlib import asynccontextmanager

from fastapi import FastAPI

from ctm_app.config import settings
from ctm_app.models import Base  # noqa: F401 — registers all models
from ctm_app.models.base import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from ctm_app.services.git_service import GitService

    GitService()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

from ctm_app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api")
