"""
Inventory management endpoints for BinBot
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import uuid

from api_schemas import (
    AddItemsRequest, RemoveItemsRequest, MoveItemsRequest, SearchRequest,
    ItemsResponse, BinContentsResponse, Item, SuccessResponse, ItemInput
)
from database.chromadb_client import get_chromadb_client
from llm.embeddings import get_embedding_service

router = APIRouter()


# Business logic functions (non-async, reusable)
def add_items_logic(bin_id: str, items: List[ItemInput]) -> SuccessResponse:
    """Business logic for adding items to a bin"""
    db_client = get_chromadb_client()
    embedding_service = get_embedding_service()

    # Prepare items for database
    items_to_add = []
    for item_input in items:
        # Generate embedding for the item
        item_text = item_input.name
        if item_input.description:
            item_text += f" {item_input.description}"

        embedding = embedding_service.generate_embedding(item_text)

        # Create item document
        item_doc = {
            'id': str(uuid.uuid4()),
            'name': item_input.name,
            'description': item_input.description or '',
            'bin_id': bin_id,
            'created_at': datetime.now().isoformat(),
            'image_id': item_input.image_id or '',
            'embedding': embedding
        }
        items_to_add.append(item_doc)

    # Add items to database
    db_client.add_documents_bulk(items_to_add)

    return SuccessResponse(
        success=True,
        message=f"Successfully added {len(items)} items to bin {bin_id}"
    )


def remove_items_logic(item_ids: List[str], bin_id: str = "") -> SuccessResponse:
    """Business logic for removing items from inventory"""
    db_client = get_chromadb_client()

    # Remove items from database
    for item_id in item_ids:
        db_client.remove_document(item_id)

    message = f"Successfully removed {len(item_ids)} items"
    if bin_id:
        message += f" from bin {bin_id}"

    return SuccessResponse(
        success=True,
        message=message
    )


def move_items_logic(item_ids: List[str], target_bin_id: str) -> SuccessResponse:
    """Business logic for moving items between bins"""
    db_client = get_chromadb_client()

    # Move items to target bin
    for item_id in item_ids:
        db_client.update_item_bin(item_id, target_bin_id)

    return SuccessResponse(
        success=True,
        message=f"Successfully moved {len(item_ids)} items to bin {target_bin_id}"
    )


def search_items_logic(query: str, limit: int = 10) -> ItemsResponse:
    """Business logic for searching items"""
    db_client = get_chromadb_client()
    search_results = db_client.search_documents(query, limit)

    # Convert to API format
    items = []
    for item_data in search_results:
        item = Item(
            id=item_data['id'],
            name=item_data['name'],
            description=item_data.get('description', ''),
            bin_id=item_data['bin_id'],
            created_at=item_data['created_at'],
            image_id=item_data.get('image_id', ''),
            confidence_score=item_data.get('confidence_score')
        )
        items.append(item)

    return ItemsResponse(
        success=True,
        items=items,
        current_bin=""
    )


def get_bin_contents_logic(bin_id: str) -> BinContentsResponse:
    """Business logic for getting bin contents"""
    db_client = get_chromadb_client()
    bin_items = db_client.get_bin_contents(bin_id)

    # Convert to API format
    items = []
    for item_data in bin_items:
        item = Item(
            id=item_data['id'],
            name=item_data['name'],
            description=item_data.get('description', ''),
            bin_id=item_data['bin_id'],
            created_at=item_data['created_at'],
            image_id=item_data.get('image_id', ''),
            confidence_score=item_data.get('confidence_score')
        )
        items.append(item)

    return BinContentsResponse(
        success=True,
        bin_id=bin_id,
        items=items,
        total_count=len(items)
    )


@router.post("/api/inventory/add", response_model=SuccessResponse)
async def add_items(request: AddItemsRequest):
    """Add items to a bin"""
    try:
        return add_items_logic(request.bin_id, request.items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add items: {str(e)}")


@router.delete("/api/inventory/remove", response_model=SuccessResponse)
async def remove_items(request: RemoveItemsRequest):
    """Remove items from inventory"""
    try:
        return remove_items_logic(request.item_ids, request.bin_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove items: {str(e)}")


@router.put("/api/inventory/move", response_model=SuccessResponse)
async def move_items(request: MoveItemsRequest):
    """Move items between bins"""
    try:
        return move_items_logic(request.item_ids, request.target_bin_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move items: {str(e)}")


@router.post("/api/inventory/search", response_model=ItemsResponse)
async def search_items(request: SearchRequest):
    """Search for items in inventory"""
    try:
        return search_items_logic(request.query, request.limit or 10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search items: {str(e)}")


@router.get("/api/inventory/bin/{bin_id}", response_model=BinContentsResponse)
async def get_bin_contents(bin_id: str):
    """Get contents of a specific bin"""
    try:
        return get_bin_contents_logic(bin_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bin contents: {str(e)}")
