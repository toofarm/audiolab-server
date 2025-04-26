from fastapi import APIRouter
from app.api import health, auth, upload

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(upload.router, prefix="/api", tags=["Upload"])
