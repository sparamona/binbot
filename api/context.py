"""
Context-Aware Operations API
Enhanced add/remove/move operations that use session context
"""

from fastapi import APIRouter, HTTPException
from api_schemas import (
    StandardResponse, 
    ContextAwareAddRequest,
    ContextAwareRemoveRequest, 
    ContextAwareMoveRequest,
    ErrorDetail,
    DisambiguationInfo,
    DisambiguationOption
)
from session.session_manager import session_manager
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter()

# Dependencies (will be injected)
db_client = None
embedding_service = None

def set_dependencies(db_client_instance, embedding_service_instance):
    """Set the database and embedding service dependencies"""
    global db_client, embedding_service
    db_client = db_client_instance
    embedding_service = embedding_service_instance

@router.post("/add", response_model=StandardResponse)
async def context_aware_add(request: ContextAwareAddRequest):
    """Add items with session context awareness"""
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.session_id)
        
        # Determine bin_id: use provided bin_id or session context
        bin_id = request.bin_id
        if not bin_id:
            bin_id = session.current_bin_id
            
        if not bin_id:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="NO_BIN_CONTEXT",
                    message="No bin_id provided and no current bin set in session context. Use 'set context bin 5' or provide bin_id explicitly."
                )
            )
        
        # Generate bulk transaction ID if not provided
        bulk_transaction_id = request.bulk_transaction_id or str(uuid.uuid4())
        
        # Add items using the determined bin_id
        added_items = []
        failed_items = []

        for item_name in request.items:
            # Generate embedding for the item
            description = f"{item_name} in bin {bin_id}"
            embedding = embedding_service.generate_embedding(description)

            if not embedding:
                failed_items.append({
                    "name": item_name,
                    "error": "Failed to generate embedding"
                })
                continue

            # Add to database
            if db_client.add_document(item_name, bin_id, description, embedding):
                added_items.append({
                    "name": item_name,
                    "bin_id": bin_id,
                    "description": description,
                    "bulk_transaction_id": bulk_transaction_id
                })
            else:
                failed_items.append({
                    "name": item_name,
                    "error": "Failed to add to database"
                })

        # Create audit log entry for bulk operation
        if added_items:
            audit_entry = {
                "operation_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "action": "context_bulk_add",
                "bin_id": bin_id,
                "bulk_transaction_id": bulk_transaction_id,
                "description": f"Added {len(added_items)} items to bin {bin_id} via context-aware operation",
                "reversible": True,
                "items_added": len(added_items),
                "items_failed": len(failed_items),
                "session_id": session.session_id
            }

            # Add audit log entry to database
            db_client.add_audit_log_entry(audit_entry)
        
        # Update session activity
        session.update_activity()

        # Determine success status
        success = len(added_items) > 0

        response_data = {
            "items_added": len(added_items),
            "items_failed": len(failed_items),
            "added_items": added_items,
            "failed_items": failed_items,
            "bin_id": bin_id,
            "bulk_transaction_id": bulk_transaction_id,
            "session_id": session.session_id,
            "used_context": request.bin_id is None
        }

        return StandardResponse(
            success=success,
            data=response_data
        )
        
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CONTEXT_ADD_FAILED",
                message=f"Failed to add items with context: {str(e)}"
            )
        )

@router.post("/remove", response_model=StandardResponse)
async def context_aware_remove(request: ContextAwareRemoveRequest):
    """Remove items with session context awareness"""
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.session_id)
        
        # Search for items matching the query
        search_response = db_client.search_documents(
            query=request.query,
            limit=50,  # Get more results for disambiguation
            offset=0
        )
        
        if not search_response.get("results"):
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="NO_ITEMS_FOUND",
                    message=f"No items found matching '{request.query}'"
                )
            )
        
        items = search_response["results"]
        
        # Handle disambiguation or direct removal
        if request.item_ids:
            # Specific items selected for removal
            items_to_remove = [item for item in items if item["id"] in request.item_ids]
        elif request.confirm_all:
            # Remove all matching items
            items_to_remove = items
        else:
            # Need disambiguation
            if len(items) > 1:
                disambiguation_options = []
                for item in items:
                    disambiguation_options.append(DisambiguationOption(
                        item_id=item["id"],
                        name=item["name"],
                        description=item["description"],
                        bin_id=item["bin_id"],
                        confidence_score=item.get("relevance_score", 1.0),
                        image_path=item.get("image_path")
                    ))
                
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="DISAMBIGUATION_REQUIRED",
                        message=f"Found {len(items)} items matching '{request.query}'. Please select specific items to remove."
                    ),
                    disambiguation=DisambiguationInfo(
                        required=True,
                        options=disambiguation_options,
                        query_id=str(uuid.uuid4())
                    )
                )
            else:
                items_to_remove = items
        
        # Remove the selected items
        bulk_transaction_id = request.bulk_transaction_id or str(uuid.uuid4())
        removed_items = []
        failed_items = []
        
        for item in items_to_remove:
            item_id = item["id"]

            # Remove from database
            success = db_client.remove_document(item_id)
            if success:
                removed_items.append({
                    "item_id": item_id,
                    "name": item["name"],
                    "bin_id": item["bin_id"]
                })
            else:
                failed_items.append({
                    "item_id": item_id,
                    "name": item["name"],
                    "error": "Failed to remove from database"
                })

        # Create audit log entry for bulk operation
        if removed_items:
            audit_entry = {
                "operation_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "action": "context_bulk_remove",
                "bulk_transaction_id": bulk_transaction_id,
                "description": f"Removed {len(removed_items)} items via context-aware operation",
                "reversible": True,
                "items_removed": len(removed_items),
                "items_failed": len(failed_items),
                "session_id": session.session_id
            }

            # Add audit log entry to database
            db_client.add_audit_log_entry(audit_entry)
        
        # Update session activity
        session.update_activity()
        
        # Determine success status
        success = len(removed_items) > 0

        response_data = {
            "items_removed": len(removed_items),
            "items_failed": len(failed_items),
            "removed_items": removed_items,
            "failed_items": failed_items,
            "bulk_transaction_id": bulk_transaction_id,
            "session_id": session.session_id,
            "used_context": request.bin_id is None if hasattr(request, 'bin_id') else False
        }

        return StandardResponse(
            success=success,
            data=response_data
        )
        
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CONTEXT_REMOVE_FAILED",
                message=f"Failed to remove items with context: {str(e)}"
            )
        )

@router.post("/move", response_model=StandardResponse)
async def context_aware_move(request: ContextAwareMoveRequest):
    """Move items with session context awareness"""
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.session_id)

        # Determine target_bin_id: use provided target_bin_id or session context
        target_bin_id = request.target_bin_id
        if not target_bin_id:
            target_bin_id = session.current_bin_id

        if not target_bin_id:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="NO_TARGET_BIN_CONTEXT",
                    message="No target_bin_id provided and no current bin set in session context. Use 'set context bin 5' or provide target_bin_id explicitly."
                )
            )

        # Search for items matching the query
        search_response = db_client.search_documents(
            query=request.query,
            limit=50,  # Get more results for disambiguation
            offset=0
        )

        if not search_response.get("results"):
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="NO_ITEMS_FOUND",
                    message=f"No items found matching '{request.query}'"
                )
            )

        items = search_response["results"]

        # Handle disambiguation or direct move
        if request.item_ids:
            # Specific items selected for move
            items_to_move = [item for item in items if item["id"] in request.item_ids]
        elif request.confirm_all:
            # Move all matching items
            items_to_move = items
        else:
            # Need disambiguation
            if len(items) > 1:
                disambiguation_options = []
                for item in items:
                    disambiguation_options.append(DisambiguationOption(
                        item_id=item["id"],
                        name=item["name"],
                        description=item["description"],
                        bin_id=item["bin_id"],
                        confidence_score=item.get("relevance_score", 1.0),
                        image_path=item.get("image_path")
                    ))

                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="DISAMBIGUATION_REQUIRED",
                        message=f"Found {len(items)} items matching '{request.query}'. Please select specific items to move."
                    ),
                    disambiguation=DisambiguationInfo(
                        required=True,
                        options=disambiguation_options,
                        query_id=str(uuid.uuid4())
                    )
                )
            else:
                items_to_move = items

        # Check if any items are already in the target bin
        items_already_in_target = [item for item in items_to_move if item["bin_id"] == target_bin_id]
        if items_already_in_target:
            item_names = [item["name"] for item in items_already_in_target]
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="ITEMS_ALREADY_IN_TARGET_BIN",
                    message=f"Items already in target bin {target_bin_id}: {', '.join(item_names)}"
                )
            )

        # Move the selected items
        bulk_transaction_id = request.bulk_transaction_id or str(uuid.uuid4())
        moved_items = []
        failed_items = []

        for item in items_to_move:
            item_id = item["id"]
            old_bin_id = item["bin_id"]
            new_description = f"{item['name']} in bin {target_bin_id}"

            # Update in database
            success = db_client.update_document_metadata(item_id, {"bin_id": target_bin_id, "description": new_description})
            if success:
                moved_items.append({
                    "item_id": item_id,
                    "name": item["name"],
                    "from_bin_id": old_bin_id,
                    "to_bin_id": target_bin_id
                })
            else:
                failed_items.append({
                    "item_id": item_id,
                    "name": item["name"],
                    "error": "Failed to update in database"
                })

        # Create audit log entry for bulk operation
        if moved_items:
            audit_entry = {
                "operation_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "action": "context_bulk_move",
                "target_bin_id": target_bin_id,
                "bulk_transaction_id": bulk_transaction_id,
                "description": f"Moved {len(moved_items)} items to bin {target_bin_id} via context-aware operation",
                "reversible": True,
                "items_moved": len(moved_items),
                "items_failed": len(failed_items),
                "session_id": session.session_id
            }

            # Add audit log entry to database
            db_client.add_audit_log_entry(audit_entry)

        # Update session activity
        session.update_activity()

        # Determine success status
        success = len(moved_items) > 0

        response_data = {
            "items_moved": len(moved_items),
            "items_failed": len(failed_items),
            "moved_items": moved_items,
            "failed_items": failed_items,
            "target_bin_id": target_bin_id,
            "bulk_transaction_id": bulk_transaction_id,
            "session_id": session.session_id,
            "used_context": request.target_bin_id is None
        }

        return StandardResponse(
            success=success,
            data=response_data
        )

    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CONTEXT_MOVE_FAILED",
                message=f"Failed to move items with context: {str(e)}"
            )
        )
