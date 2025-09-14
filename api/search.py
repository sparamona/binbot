from fastapi import APIRouter, Query
from api_schemas import StandardResponse, ErrorDetail
from database.chromadb_client import ChromaDBClient

router = APIRouter(tags=["search"])

# This will be injected by the main app
db_client: ChromaDBClient = None


def set_dependencies(db: ChromaDBClient):
    """Set dependencies for the search router"""
    global db_client
    db_client = db


@router.get("/search", response_model=StandardResponse)
async def search_inventory(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    min_relevance: float = Query(0.6, ge=0.0, le=1.0, description="Minimum relevance score (0.0-1.0)")
):
    """Search inventory items using text matching"""
    try:
        if db_client.inventory_collection is None:
            error_detail = ErrorDetail(
                code="DATABASE_ERROR",
                message="Database not initialized",
                details={"collection": "inventory"}
            )
            return StandardResponse(
                success=False,
                error=error_detail
            )

        # Perform search
        search_results = db_client.search_documents(q, limit, offset, min_relevance)

        return StandardResponse(
            success=True,
            data={
                "query": q,
                "total_results": search_results["total_results"],
                "results": search_results["results"],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": search_results["has_more"]
                }
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="SEARCH_ERROR",
            message="Failed to search inventory",
            details={"error": str(e), "query": q}
        )
        print(f"Error searching inventory: {e}")
        return StandardResponse(
            success=False,
            error=error_detail
        )
