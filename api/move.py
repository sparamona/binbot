from fastapi import APIRouter, HTTPException
from api_schemas import MoveItemRequest, StandardResponse, DisambiguationOption, DisambiguationInfo
import uuid
from datetime import datetime

router = APIRouter(prefix="/move", tags=["move"])

# Dependencies will be injected
db_client = None
embedding_service = None

def set_dependencies(db, embedding):
    global db_client, embedding_service
    db_client = db
    embedding_service = embedding

@router.post("", response_model=StandardResponse)
async def move_items(request: MoveItemRequest):
    """
    Move items from their current bin to a target bin.
    Supports disambiguation when multiple items match the query.
    """
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Generate bulk transaction ID if not provided
        bulk_transaction_id = getattr(request, 'bulk_transaction_id', None) or str(uuid.uuid4())
        
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
        
        # If specific item IDs are provided, filter to those items
        item_ids = getattr(request, 'item_ids', None)

        if item_ids:
            search_results = [item for item in search_results if item.get("id") in item_ids]

            if not search_results:
                return StandardResponse(
                    success=False,
                    error={
                        "code": "INVALID_ITEM_IDS",
                        "message": "None of the specified item IDs were found"
                    }
                )

        # Check if disambiguation is needed (only if no specific item IDs were provided)

        if not item_ids:
            confirm_all = getattr(request, 'confirm_all', False)
            if len(search_results) > 1 and not confirm_all:
                # Return disambiguation options
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
                        "message": f"Found {len(search_results)} items matching '{request.query}'. Please specify which items to move."
                    },
                    disambiguation=DisambiguationInfo(
                        required=True,
                        options=disambiguation_options,
                        query_id=str(uuid.uuid4())
                    )
                )
        
        # Move the items
        moved_items = []
        failed_items = []
        
        for item in search_results:
            item_id = item.get("id")
            current_bin_id = item.get("bin_id")
            
            # Skip if already in target bin
            if current_bin_id == request.target_bin_id:
                failed_items.append({
                    "id": item_id,
                    "name": item.get("name"),
                    "error": f"Item already in bin {request.target_bin_id}"
                })
                continue
            
            try:
                # Update the item's bin_id metadata
                success = db_client.update_document_metadata(
                    document_id=item_id,
                    metadata_updates={
                        "bin_id": request.target_bin_id,
                        "moved_at": datetime.now().isoformat(),
                        "previous_bin_id": current_bin_id,
                        "bulk_transaction_id": bulk_transaction_id
                    }
                )
                
                if success:
                    # Create audit log entry
                    audit_entry = {
                        "action": "move",
                        "item_id": item_id,
                        "item_name": item.get("name"),
                        "from_bin_id": current_bin_id,
                        "to_bin_id": request.target_bin_id,
                        "bulk_transaction_id": bulk_transaction_id,
                        "timestamp": datetime.now().isoformat(),
                        "query": request.query
                    }
                    
                    db_client.add_audit_log_entry(audit_entry)
                    
                    moved_items.append({
                        "id": item_id,
                        "name": item.get("name"),
                        "from_bin_id": current_bin_id,
                        "to_bin_id": request.target_bin_id,
                        "description": item.get("description"),
                        "bulk_transaction_id": bulk_transaction_id
                    })
                else:
                    failed_items.append({
                        "id": item_id,
                        "name": item.get("name"),
                        "error": "Failed to update item metadata"
                    })
                    
            except Exception as e:
                failed_items.append({
                    "id": item_id,
                    "name": item.get("name"),
                    "error": str(e)
                })
        
        return StandardResponse(
            success=True,
            data={
                "items_moved": len(moved_items),
                "items_failed": len(failed_items),
                "total_items": len(moved_items) + len(failed_items),
                "bulk_transaction_id": bulk_transaction_id,
                "moved_items": moved_items,
                "failed_items": failed_items if failed_items else None
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move operation failed: {str(e)}")
