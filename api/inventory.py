"""
Inventory management endpoints for BinBot
"""

from fastapi import APIRouter, HTTPException
from typing import List
from api_schemas import (
    AddItemsRequest, RemoveItemsRequest, MoveItemsRequest, SearchRequest,
    ItemsResponse, BinContentsResponse, Item
)
from chat.function_wrappers import get_function_wrappers
from database.chromadb_client import get_chromadb_client

router = APIRouter()


@router.post("/api/inventory/add", response_model=ItemsResponse)
async def add_items(request: AddItemsRequest, session_id: str):
    """Add items to a bin"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Use function wrappers to add items
    wrappers = get_function_wrappers(session_id)
    items_data = [item.model_dump() for item in request.items]
    result = wrappers.add_items(request.bin_id, items_data)
    
    # Get the added items to return
    db_client = get_chromadb_client()
    bin_items = db_client.get_bin_contents(request.bin_id)
    
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
    
    return ItemsResponse(
        success=True,
        items=items,
        current_bin=request.bin_id
    )


@router.delete("/api/inventory/remove", response_model=ItemsResponse)
async def remove_items(request: RemoveItemsRequest, session_id: str):
    """Remove items from inventory"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Use function wrappers to remove items
    wrappers = get_function_wrappers(session_id)
    result = wrappers.remove_items(request.item_ids)
    
    # Get remaining items in the bin
    db_client = get_chromadb_client()
    bin_items = db_client.get_bin_contents(request.bin_id)
    
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
    
    return ItemsResponse(
        success=True,
        items=items,
        current_bin=request.bin_id
    )


@router.put("/api/inventory/move", response_model=ItemsResponse)
async def move_items(request: MoveItemsRequest, session_id: str):
    """Move items between bins"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Use function wrappers to move items
    wrappers = get_function_wrappers(session_id)
    result = wrappers.move_items(request.target_bin_id, request.item_ids)
    
    # Get items in the target bin
    db_client = get_chromadb_client()
    bin_items = db_client.get_bin_contents(request.target_bin_id)
    
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
    
    return ItemsResponse(
        success=True,
        items=items,
        current_bin=request.target_bin_id
    )


@router.post("/api/inventory/search", response_model=ItemsResponse)
async def search_items(request: SearchRequest, session_id: str):
    """Search for items in inventory"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Search directly using database client
    db_client = get_chromadb_client()
    search_results = db_client.search_documents(request.query, request.limit)
    
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


@router.get("/api/inventory/bin/{bin_id}", response_model=BinContentsResponse)
async def get_bin_contents(bin_id: str, session_id: str):
    """Get contents of a specific bin"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Use function wrappers to get bin contents (updates session)
    wrappers = get_function_wrappers(session_id)
    result = wrappers.get_bin_contents(bin_id)
    
    # Get items from database
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
