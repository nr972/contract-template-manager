from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.templates import router as templates_router
from app.api.versions import router as versions_router
from app.api.workflow import router as workflow_router
from app.api.diff import router as diff_router
from app.api.shutdown import router as shutdown_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(users_router)
api_router.include_router(templates_router)
api_router.include_router(versions_router)
api_router.include_router(workflow_router)
api_router.include_router(diff_router)
api_router.include_router(shutdown_router)
