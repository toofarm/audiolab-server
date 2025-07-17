from fastapi import APIRouter
from app.api import health, auth, upload, tracks, samples

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(upload.router, prefix="/api", tags=["Upload"])
router.include_router(tracks.router, prefix="/api", tags=["Tracks"])
router.include_router(samples.router, prefix="/api", tags=["Samples"])
