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

class RemoveItemRequest(BaseModel):
    query: str = Field(..., description="Description of item to remove")
    bin_id: Optional[str] = None
    confirmation_id: Optional[str] = None

class MoveItemRequest(BaseModel):
    query: str = Field(..., description="Description of item to move")
    source_bin_id: Optional[str] = None
    target_bin_id: str = Field(..., description="Destination bin ID")
    confirmation_id: Optional[str] = None

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
    image_path: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

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
