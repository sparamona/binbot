"""
Remove items API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from api_schemas import RemoveItemRequest, StandardResponse

router = APIRouter(prefix="/remove", tags=["remove"])

# Dependencies (will be set by main app)
db_client = None
embedding_service = None

def set_dependencies(database_client, llm_service):
    """Set dependencies for the remove router"""
    global db_client, embedding_service
    db_client = database_client
    embedding_service = llm_service

@router.post("", response_model=StandardResponse)
async def remove_items(request: RemoveItemRequest):
    """Remove items from inventory with disambiguation support"""
    try:
        if not db_client or not embedding_service:
            raise HTTPException(status_code=500, detail="Services not initialized")
        
        # Search for items matching the query
        search_response = db_client.search_documents(
            query=request.query,
            limit=50,  # Get more results for disambiguation
            offset=0
        )

        search_results = search_response.get("results", []) if search_response else []

        if not search_results or len(search_results) == 0:
            return StandardResponse(
                success=False,
                error={
                    "code": "NO_ITEMS_FOUND",
                    "message": f"No items found matching '{request.query}'"
                }
            )
        
        # If specific item IDs provided, filter to those
        if request.item_ids:
            filtered_results = [item for item in search_results if item.get("id") in request.item_ids]
            if not filtered_results:
                return StandardResponse(
                    success=False,
                    error={
                        "code": "INVALID_ITEM_IDS",
                        "message": "None of the specified item IDs were found"
                    }
                )
            items_to_remove = filtered_results
        else:
            # Check if disambiguation is needed
            if len(search_results) > 1 and not request.confirm_all:
                # Return disambiguation options
                from api_schemas import DisambiguationOption, DisambiguationInfo

                disambiguation_options = []
                for item in search_results:
                    disambiguation_options.append(DisambiguationOption(
                        item_id=item.get("id"),
                        name=item.get("name"),
                        description=item.get("description"),
                        bin_id=item.get("bin_id"),
                        confidence_score=item.get("relevance_score", 0.0)
                    ))

                return StandardResponse(
                    success=False,
                    error={
                        "code": "DISAMBIGUATION_REQUIRED",
                        "message": f"Found {len(search_results)} items matching '{request.query}'. Please specify which items to remove."
                    },
                    disambiguation=DisambiguationInfo(
                        required=True,
                        options=disambiguation_options,
                        query_id=str(uuid.uuid4())
                    )
                )
            
            items_to_remove = search_results
        
        # Generate bulk transaction ID for audit logging
        bulk_transaction_id = request.bulk_transaction_id or str(uuid.uuid4())
        
        # Remove items and track results
        removed_items = []
        failed_items = []
        
        for item in items_to_remove:
            try:
                item_id = item.get("id")
                item_name = item.get("name")
                bin_id = item.get("bin_id")
                
                # Remove from database
                success = db_client.remove_document(item_id)
                
                if success:
                    # Create audit log entry
                    audit_entry = {
                        "operation_id": str(uuid.uuid4()),
                        "operation_type": "remove",
                        "bulk_transaction_id": bulk_transaction_id,
                        "item_id": item_id,
                        "item_name": item_name,
                        "bin_id": bin_id,
                        "description": f"Removed '{item_name}' from bin {bin_id}",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "original_query": request.query,
                            "relevance_score": item.get("relevance_score", 0.0)
                        }
                    }
                    
                    db_client.add_audit_log_entry(audit_entry)
                    
                    removed_items.append({
                        "id": item_id,
                        "name": item_name,
                        "bin_id": bin_id,
                        "description": item.get("description"),
                        "bulk_transaction_id": bulk_transaction_id
                    })
                else:
                    failed_items.append({
                        "id": item_id,
                        "name": item_name,
                        "error": "Failed to remove from database"
                    })
                    
            except Exception as e:
                failed_items.append({
                    "id": item.get("id", "unknown"),
                    "name": item.get("name", "unknown"),
                    "error": str(e)
                })
        
        # Determine success status
        items_removed = len(removed_items)
        items_failed = len(failed_items)
        total_items = len(items_to_remove)
        
        if items_removed == 0:
            return StandardResponse(
                success=False,
                error={
                    "code": "REMOVE_FAILED",
                    "message": "Failed to remove any items",
                    "details": {
                        "items_removed": items_removed,
                        "items_failed": items_failed,
                        "total_items": total_items,
                        "bulk_transaction_id": bulk_transaction_id,
                        "removed_items": removed_items,
                        "failed_items": failed_items
                    }
                }
            )
        
        return StandardResponse(
            success=True,
            data={
                "items_removed": items_removed,
                "items_failed": items_failed,
                "total_items": total_items,
                "bulk_transaction_id": bulk_transaction_id,
                "removed_items": removed_items,
                "failed_items": failed_items if failed_items else None
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remove operation failed: {str(e)}")
