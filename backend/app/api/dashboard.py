from fastapi import APIRouter, Depends

from app.api.dashboard_routes.conversations import router as conversations_router
from app.api.dashboard_routes.faqs import router as faq_router
from app.api.dashboard_routes.stats import router as stats_router
from app.security.auth import get_current_user, require_roles

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)
router.include_router(stats_router)
router.include_router(conversations_router)
router.include_router(faq_router, dependencies=[Depends(require_roles("admin"))])
