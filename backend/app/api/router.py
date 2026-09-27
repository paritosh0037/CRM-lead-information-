from fastapi import APIRouter
from app.api.leads import router as leads_router
from app.api.feedback import router as feedback_router
from app.api.analytics import router as analytics_router

router = APIRouter()

# Mount routes
router.include_router(leads_router)
router.include_router(feedback_router)
router.include_router(analytics_router)
