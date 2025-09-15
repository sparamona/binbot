from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Standard Response Format
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class DisambiguationOption(BaseModel):
    item_id: str
    name: str
    description: str
    bin_id: str
    confidence_score: float
    image_path: Optional[str] = None

class DisambiguationInfo(BaseModel):
    required: bool
    options: List[DisambiguationOption]
    query_id: str

class StandardResponse(BaseModel):
    success: bool
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    error: Optional[ErrorDetail] = None
    disambiguation: Optional[DisambiguationInfo] = None

# Request Schemas
class AddItemRequest(BaseModel):
    items: List[str] = Field(..., description="List of item names to add")
    bin_id: str = Field(..., description="Bin ID where items should be added")
    bulk_transaction_id: Optional[str] = None

class AddItemWithImageRequest(BaseModel):
    items: List[str] = Field(..., description="List of item names to add")
    bin_id: str = Field(..., description="Bin ID where items should be added")
    bulk_transaction_id: Optional[str] = None

class RemoveItemRequest(BaseModel):
    query: str = Field(..., description="Description of item to remove")
    item_ids: Optional[List[str]] = Field(None, description="Specific item IDs to remove (for disambiguation)")
    confirm_all: bool = Field(False, description="Confirm removal of all matching items")
    bulk_transaction_id: Optional[str] = None

class MoveItemRequest(BaseModel):
    query: str = Field(..., description="Description of item to move")
    target_bin_id: str = Field(..., description="Target bin ID to move items to")
    item_ids: Optional[List[str]] = Field(None, description="Specific item IDs to move (for disambiguation)")
    confirm_all: bool = Field(False, description="Confirm moving all matching items")
    bulk_transaction_id: Optional[str] = None



class SearchRequest(BaseModel):
    q: str = Field(..., description="Search query")
    bin_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)

class UndoRequest(BaseModel):
    operation_id: str = Field(..., description="Operation ID from audit log to undo")

# Response Data Models
class ItemData(BaseModel):
    item_id: str
    name: str
    description: str
    bin_id: str
    image_path: Optional[str] = None  # Deprecated - use images instead
    images: List[str] = []  # List of image IDs
    primary_image: Optional[str] = None  # Primary image ID
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class ImageMetadata(BaseModel):
    image_id: str
    item_id: str
    bin_id: str
    original_filename: Optional[str] = None
    file_path: str
    thumbnail_small: str
    thumbnail_medium: str
    width: int
    height: int
    file_size: int
    format: str
    file_hash: str
    created_at: datetime
    updated_at: datetime

class ImageUploadRequest(BaseModel):
    item_id: str = Field(..., description="Item ID to associate the image with")
    set_as_primary: bool = Field(False, description="Set this image as the primary image for the item")

class HealthData(BaseModel):
    status: str
    database_connected: bool
    llm_connected: bool
    version: str = "1.0.0"
    uptime_seconds: float

class AuditLogEntry(BaseModel):
    operation_id: str
    timestamp: datetime
    action: str
    bin_id: str
    item_id: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    bulk_transaction_id: Optional[str] = None
    description: str
    reversible: bool

# Session Management Schemas
class SessionContextData(BaseModel):
    session_id: str
    current_bin_id: Optional[str] = None
    last_activity: str  # ISO format datetime string
    created_at: str     # ISO format datetime string
    metadata: Dict[str, Any] = {}

class SetContextRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID (will create new if not provided)")
    current_bin_id: Optional[str] = Field(None, description="Current bin ID to set as context")

class ContextAwareAddRequest(BaseModel):
    items: List[str] = Field(..., description="List of item names to add")
    bin_id: Optional[str] = Field(None, description="Bin ID where items should be added (uses session context if not provided)")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    bulk_transaction_id: Optional[str] = None

class ContextAwareRemoveRequest(BaseModel):
    query: str = Field(..., description="Description of item to remove")
    item_ids: Optional[List[str]] = Field(None, description="Specific item IDs to remove (for disambiguation)")
    confirm_all: bool = Field(False, description="Confirm removal of all matching items")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    bulk_transaction_id: Optional[str] = None

class ContextAwareMoveRequest(BaseModel):
    query: str = Field(..., description="Description of item to move")
    target_bin_id: Optional[str] = Field(None, description="Target bin ID to move items to (uses session context if not provided)")
    item_ids: Optional[List[str]] = Field(None, description="Specific item IDs to move (for disambiguation)")
    confirm_all: bool = Field(False, description="Confirm moving all matching items")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    bulk_transaction_id: Optional[str] = None
