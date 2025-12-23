"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, str]:
    """Check API health."""
    return {"status": "healthy", "service": "PolySaaS"}


@router.get("/readiness")
async def readiness_check() -> dict[str, str]:
    """Check if service is ready."""
    return {"status": "ready"}


@router.get("/liveness")
async def liveness_check() -> dict[str, str]:
    """Check if service is alive."""
    return {"status": "alive"}
