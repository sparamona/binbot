from fastapi import APIRouter, HTTPException
from api_schemas import StandardResponse, ErrorDetail, AddItemRequest
from database.chromadb_client import ChromaDBClient
from llm.embeddings import EmbeddingService
import uuid
from datetime import datetime

router = APIRouter(prefix="/add", tags=["add"])

# These will be injected by the main app
db_client: ChromaDBClient = None
embedding_service: EmbeddingService = None


def set_dependencies(db: ChromaDBClient, embeddings: EmbeddingService):
    """Set dependencies for the add router"""
    global db_client, embedding_service
    db_client = db
    embedding_service = embeddings


@router.post("", response_model=StandardResponse)
async def add_items(request: AddItemRequest):
    """Add items to inventory"""
    try:
        if db_client.inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        if not request.items:
            error_detail = ErrorDetail(
                code="INVALID_REQUEST",
                message="No items provided",
                details={"items": request.items}
            )
            return StandardResponse(success=False, error=error_detail)

        # Generate bulk transaction ID if not provided
        bulk_transaction_id = request.bulk_transaction_id or str(uuid.uuid4())
        
        added_items = []
        failed_items = []
        
        for item_name in request.items:
            item_name = item_name.strip()
            if not item_name:
                failed_items.append({
                    "name": item_name,
                    "error": "Empty item name"
                })
                continue
                
            # Create description (for now, same as name)
            description = f"{item_name} in bin {request.bin_id}"
            
            # Generate embedding
            document_text = f"{item_name} - {description}"
            embedding = embedding_service.generate_embedding(document_text)
            
            if embedding is None:
                failed_items.append({
                    "name": item_name,
                    "error": "Failed to generate embedding"
                })
                continue
            
            # Add to database
            if db_client.add_document(item_name, request.bin_id, description, embedding):
                added_items.append({
                    "name": item_name,
                    "bin_id": request.bin_id,
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
                "action": "bulk_add",
                "bin_id": request.bin_id,
                "bulk_transaction_id": bulk_transaction_id,
                "description": f"Added {len(added_items)} items to bin {request.bin_id}",
                "reversible": True,
                "items_added": len(added_items),
                "items_failed": len(failed_items)
            }
            
            # Add audit log entry to database
            db_client.add_audit_log_entry(audit_entry)

        # Determine success status
        success = len(added_items) > 0
        
        response_data = {
            "items_added": len(added_items),
            "items_failed": len(failed_items),
            "total_items": len(request.items),
            "bulk_transaction_id": bulk_transaction_id,
            "added_items": added_items
        }
        
        if failed_items:
            response_data["failed_items"] = failed_items

        if not success:
            error_detail = ErrorDetail(
                code="ADD_FAILED",
                message="Failed to add any items",
                details=response_data
            )
            return StandardResponse(success=False, error=error_detail)

        return StandardResponse(
            success=True,
            data=response_data
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="ADD_ERROR",
            message="Failed to add items",
            details={"error": str(e)}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )
