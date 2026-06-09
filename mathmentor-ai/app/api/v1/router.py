"""API v1 router assembly."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, sessions, users, wiki
from app.api.v1.endpoints.admin import dashboard as admin_dashboard, evaluation, wiki as admin_wiki

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(wiki.router, prefix="/wiki", tags=["wiki"])
router.include_router(
    evaluation.router,
    prefix="/admin/evaluation",
    tags=["admin", "evaluation"],
)
router.include_router(admin_wiki.router, prefix="/admin/wiki", tags=["admin", "wiki"])
router.include_router(
    admin_dashboard.router,
    prefix="/admin/dashboard",
    tags=["admin", "dashboard"],
)
