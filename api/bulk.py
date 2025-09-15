from fastapi import APIRouter, HTTPException
from api_schemas import StandardResponse, ErrorDetail
from database.chromadb_client import ChromaDBClient
from llm.embeddings import EmbeddingService
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

router = APIRouter(prefix="/bulk", tags=["bulk"])

# These will be injected by the main app
db_client: ChromaDBClient = None
embedding_service: EmbeddingService = None


def set_dependencies(db: ChromaDBClient, embeddings: EmbeddingService):
    """Set dependencies for the bulk router"""
    global db_client, embedding_service
    db_client = db
    embedding_service = embeddings


class BulkAddRequest(BaseModel):
    items: List[str] = Field(..., description="List of item names to add")
    bin_id: str = Field(..., description="Bin ID where items should be added")
    transaction_id: Optional[str] = Field(None, description="Optional transaction ID for grouping operations")
    rollback_on_partial_failure: bool = Field(True, description="Whether to rollback all items if any fail")


class BulkTransactionRequest(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID to rollback")


@router.post("/add", response_model=StandardResponse)
async def bulk_add_items(request: BulkAddRequest):
    """Add multiple items with transaction management and rollback capability"""
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

        # Generate transaction ID if not provided
        transaction_id = request.transaction_id or str(uuid.uuid4())
        
        # Prepare items for bulk processing
        prepared_items = []
        failed_items = []
        
        # First pass: validate and prepare all items
        for item_name in request.items:
            item_name = item_name.strip()
            if not item_name:
                failed_items.append({
                    "name": item_name,
                    "error": "Empty item name"
                })
                continue
                
            # Create description
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
            
            prepared_items.append({
                "name": item_name,
                "bin_id": request.bin_id,
                "description": description,
                "embedding": embedding
            })

        # Check if we should proceed with partial failures
        if failed_items and request.rollback_on_partial_failure:
            error_detail = ErrorDetail(
                code="PARTIAL_FAILURE_ROLLBACK",
                message=f"Rolling back due to {len(failed_items)} failed items",
                details={
                    "failed_items": failed_items,
                    "prepared_items_count": len(prepared_items),
                    "transaction_id": transaction_id
                }
            )
            return StandardResponse(success=False, error=error_detail)

        # Atomic bulk add operation
        added_items = []
        doc_ids_to_rollback = []
        
        if prepared_items:
            bulk_result = db_client.add_documents_bulk(prepared_items)
            
            if bulk_result["success"]:
                added_items = bulk_result["added_items"]
                doc_ids_to_rollback = bulk_result["doc_ids"]
                
                # Add transaction_id to each item
                for item in added_items:
                    item["transaction_id"] = transaction_id
                    
                # Create audit log entry for successful bulk operation
                import json
                audit_entry = {
                    "operation_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "action": "bulk_add_transaction",
                    "bin_id": request.bin_id,
                    "transaction_id": transaction_id,
                    "description": f"Bulk transaction: Added {len(added_items)} items to bin {request.bin_id}",
                    "reversible": True,
                    "items_added": len(added_items),
                    "items_failed": len(failed_items),
                    "doc_ids": json.dumps(doc_ids_to_rollback),  # Convert list to JSON string
                    "item_details": json.dumps([{"name": item["name"], "id": item["id"]} for item in added_items]),  # Convert list to JSON string
                    "rollback_on_partial_failure": request.rollback_on_partial_failure
                }
                
                # Add audit log entry to database
                db_client.add_audit_log_entry(audit_entry)
                
            else:
                # Bulk operation failed completely
                error_detail = ErrorDetail(
                    code="BULK_ADD_FAILED",
                    message="Bulk add operation failed",
                    details={
                        "error": bulk_result.get("error", "Unknown error"),
                        "transaction_id": transaction_id,
                        "prepared_items_count": len(prepared_items)
                    }
                )
                return StandardResponse(success=False, error=error_detail)

        # Determine success status
        success = len(added_items) > 0
        
        response_data = {
            "items_added": len(added_items),
            "items_failed": len(failed_items),
            "total_items": len(request.items),
            "transaction_id": transaction_id,
            "added_items": added_items,
            "rollback_on_partial_failure": request.rollback_on_partial_failure
        }
        
        if failed_items:
            response_data["failed_items"] = failed_items

        if not success:
            error_detail = ErrorDetail(
                code="BULK_ADD_NO_SUCCESS",
                message="No items were successfully added",
                details=response_data
            )
            return StandardResponse(success=False, error=error_detail)

        return StandardResponse(
            success=True,
            data=response_data
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="BULK_ADD_ERROR",
            message="Failed to perform bulk add operation",
            details={"error": str(e)}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.post("/rollback", response_model=StandardResponse)
async def rollback_transaction(request: BulkTransactionRequest):
    """Rollback a bulk transaction by transaction ID"""
    try:
        if db_client.audit_log_collection is None:
            raise HTTPException(status_code=500, detail="Audit log not initialized")

        # Find the transaction in audit log using get with where clause
        try:
            audit_results = db_client.audit_log_collection.get(
                where={"transaction_id": request.transaction_id},
                include=['metadatas']
            )
        except Exception as e:
            # If where clause fails, try getting all and filtering manually
            try:
                all_results = db_client.audit_log_collection.get(include=['metadatas'])
                matching_indices = []
                for i, metadata in enumerate(all_results['metadatas']):
                    if metadata.get("transaction_id") == request.transaction_id:
                        matching_indices.append(i)

                if matching_indices:
                    audit_results = {
                        'ids': [all_results['ids'][i] for i in matching_indices],
                        'metadatas': [all_results['metadatas'][i] for i in matching_indices]
                    }
                else:
                    audit_results = {'ids': [], 'metadatas': []}
            except Exception as e2:
                error_detail = ErrorDetail(
                    code="AUDIT_LOG_ERROR",
                    message="Failed to query audit log",
                    details={"error": str(e2), "transaction_id": request.transaction_id}
                )
                return StandardResponse(success=False, error=error_detail)

        if not audit_results['ids'] or len(audit_results['ids']) == 0:
            error_detail = ErrorDetail(
                code="TRANSACTION_NOT_FOUND",
                message="Transaction not found",
                details={"transaction_id": request.transaction_id}
            )
            return StandardResponse(success=False, error=error_detail)

        # Get the most recent transaction entry (should be the bulk_add_transaction)
        transaction_metadata = audit_results['metadatas'][0]
        
        if not transaction_metadata.get("reversible", False):
            error_detail = ErrorDetail(
                code="TRANSACTION_NOT_REVERSIBLE",
                message="Transaction is not reversible",
                details={"transaction_id": request.transaction_id}
            )
            return StandardResponse(success=False, error=error_detail)

        # Get document IDs to rollback
        import json
        doc_ids_str = transaction_metadata.get("doc_ids", "[]")
        try:
            doc_ids = json.loads(doc_ids_str) if isinstance(doc_ids_str, str) else doc_ids_str
        except json.JSONDecodeError:
            doc_ids = []
        
        if not doc_ids:
            error_detail = ErrorDetail(
                code="NO_ITEMS_TO_ROLLBACK",
                message="No items found to rollback",
                details={"transaction_id": request.transaction_id}
            )
            return StandardResponse(success=False, error=error_detail)

        # Perform rollback
        rollback_success = db_client.rollback_bulk_add(doc_ids)
        
        if rollback_success:
            # Create audit log entry for rollback
            rollback_audit_entry = {
                "operation_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "action": "bulk_rollback",
                "transaction_id": request.transaction_id,
                "description": f"Rolled back transaction {request.transaction_id} ({len(doc_ids)} items)",
                "reversible": False,  # Rollbacks are not reversible
                "items_rolled_back": len(doc_ids),
                "original_transaction_id": request.transaction_id
            }
            
            db_client.add_audit_log_entry(rollback_audit_entry)
            
            return StandardResponse(
                success=True,
                data={
                    "transaction_id": request.transaction_id,
                    "items_rolled_back": len(doc_ids),
                    "rollback_operation_id": rollback_audit_entry["operation_id"]
                }
            )
        else:
            error_detail = ErrorDetail(
                code="ROLLBACK_FAILED",
                message="Failed to rollback transaction",
                details={"transaction_id": request.transaction_id}
            )
            return StandardResponse(success=False, error=error_detail)

    except Exception as e:
        error_detail = ErrorDetail(
            code="ROLLBACK_ERROR",
            message="Failed to rollback transaction",
            details={"error": str(e), "transaction_id": request.transaction_id}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )
