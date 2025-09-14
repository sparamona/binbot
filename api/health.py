import time
from fastapi import APIRouter
from api_schemas import StandardResponse, ErrorDetail
from database.chromadb_client import ChromaDBClient
from llm.client import LLMClient

router = APIRouter(tags=["health"])

# These will be injected by the main app
db_client: ChromaDBClient = None
llm_client: LLMClient = None
startup_time: float = 0


def set_dependencies(db: ChromaDBClient, llm: LLMClient, start_time: float):
    """Set dependencies for the health router"""
    global db_client, llm_client, startup_time
    db_client = db
    llm_client = llm
    startup_time = start_time


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """System health check endpoint"""
    try:
        # Check database connection
        db_connected = db_client.validate_connection()

        # Check LLM connection
        llm_connected = llm_client.validate_connection()

        # Calculate uptime
        uptime = time.time() - startup_time

        # Get collection statistics
        collection_stats = db_client.get_collection_stats()

        # Determine overall status
        status = "healthy" if db_connected and llm_connected else "degraded"

        # Create enhanced health data
        health_data = {
            "status": status,
            "database_connected": db_connected,
            "llm_connected": llm_connected,
            "version": "1.0.0",
            "uptime_seconds": uptime,
            "collections": collection_stats
        }

        return StandardResponse(
            success=True,
            data=health_data
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="HEALTH_CHECK_ERROR",
            message="Failed to perform health check",
            details={"error": str(e)}
        )

        return StandardResponse(
            success=False,
            error=error_detail
        )
