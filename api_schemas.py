"""
Simple Pydantic models for BinBot API
"""

from typing import List, Optional
from pydantic import BaseModel


# Item Models
class ItemInput(BaseModel):
    """Input model for adding items"""
    name: str
    description: Optional[str] = ""
    image_id: Optional[str] = ""


class Item(BaseModel):
    """Item response model"""
    id: str
    name: str
    description: str
    bin_id: str
    created_at: str
    image_id: Optional[str] = ""
    confidence_score: Optional[float] = None


# Request Models
class AddItemsRequest(BaseModel):
    """Request to add items to a bin"""
    bin_id: str
    items: List[ItemInput]


class RemoveItemsRequest(BaseModel):
    """Request to remove items from a bin"""
    bin_id: str
    item_ids: List[str]


class MoveItemsRequest(BaseModel):
    """Request to move items between bins"""
    target_bin_id: str
    item_ids: List[str]


class SearchRequest(BaseModel):
    """Request to search for items"""
    query: str
    limit: Optional[int] = 10


class ChatRequest(BaseModel):
    """Request for chat completion"""
    message: str
    session_id: str


class ImageAnalysisRequest(BaseModel):
    """Request for image analysis"""
    pass


# Response Models
class ItemsResponse(BaseModel):
    """Response with list of items"""
    success: bool
    items: List[Item]
    current_bin: Optional[str] = ""


class BinContentsResponse(BaseModel):
    """Response with bin contents"""
    success: bool
    bin_id: str
    items: List[Item]
    total_count: int


class ChatResponse(BaseModel):
    """Response from chat completion"""
    success: bool
    response: str


class SessionResponse(BaseModel):
    """Response with session info"""
    success: bool
    session_id: str


class ImageUploadResponse(BaseModel):
    """Response from image upload"""
    success: bool
    image_id: str
    analyzed_items: List[ItemInput]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str


# Session Models
class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    created_at: str
    last_accessed: str
    current_bin: str
    conversation: List[dict]


class SessionInfoResponse(BaseModel):
    """Response with session information"""
    success: bool
    session: SessionInfo
