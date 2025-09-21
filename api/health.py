"""
Health check endpoint for BinBot
"""

from fastapi import APIRouter
from api_schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for liveness/readiness probes"""
    return HealthResponse(status="ok")
