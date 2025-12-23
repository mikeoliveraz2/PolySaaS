"""API v1 router."""
from fastapi import APIRouter

from polysaas.api.v1 import orchestration, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(orchestration.router, prefix="/orchestration", tags=["orchestration"])
