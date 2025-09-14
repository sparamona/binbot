"""
Session Management API
Handles session context and state management for multi-turn conversations
"""

from fastapi import APIRouter, HTTPException
from api_schemas import (
    StandardResponse, 
    SetContextRequest, 
    SessionContextData,
    ErrorDetail
)
from session.session_manager import session_manager
from typing import Optional

router = APIRouter()

@router.post("/create", response_model=StandardResponse)
async def create_session(session_id: Optional[str] = None):
    """Create a new session or return existing one"""
    try:
        session = session_manager.create_session(session_id)
        
        return StandardResponse(
            success=True,
            data={
                "session": session.to_dict(),
                "message": "Session created successfully"
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="SESSION_CREATION_FAILED",
                message=f"Failed to create session: {str(e)}"
            )
        )

@router.get("/{session_id}", response_model=StandardResponse)
async def get_session(session_id: str):
    """Get session information by ID"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="SESSION_NOT_FOUND",
                    message=f"Session {session_id} not found or expired"
                )
            )
        
        return StandardResponse(
            success=True,
            data={
                "session": session.to_dict()
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="SESSION_RETRIEVAL_FAILED",
                message=f"Failed to retrieve session: {str(e)}"
            )
        )

@router.post("/context", response_model=StandardResponse)
async def set_context(request: SetContextRequest):
    """Set or update session context"""
    try:
        # Get or create session
        session = session_manager.get_or_create_session(request.session_id)
        
        # Update context if bin_id provided
        if request.current_bin_id is not None:
            session = session_manager.set_current_bin(session.session_id, request.current_bin_id)
        
        return StandardResponse(
            success=True,
            data={
                "session": session.to_dict(),
                "message": f"Context updated - current bin: {session.current_bin_id or 'None'}"
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CONTEXT_UPDATE_FAILED",
                message=f"Failed to update context: {str(e)}"
            )
        )

@router.get("/{session_id}/context", response_model=StandardResponse)
async def get_context(session_id: str):
    """Get current context for a session"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="SESSION_NOT_FOUND",
                    message=f"Session {session_id} not found or expired"
                )
            )
        
        return StandardResponse(
            success=True,
            data={
                "session_id": session.session_id,
                "current_bin_id": session.current_bin_id,
                "context_active": session.current_bin_id is not None
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CONTEXT_RETRIEVAL_FAILED",
                message=f"Failed to retrieve context: {str(e)}"
            )
        )

@router.delete("/{session_id}", response_model=StandardResponse)
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        deleted = session_manager.delete_session(session_id)
        
        if not deleted:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="SESSION_NOT_FOUND",
                    message=f"Session {session_id} not found"
                )
            )
        
        return StandardResponse(
            success=True,
            data={
                "message": f"Session {session_id} deleted successfully"
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="SESSION_DELETION_FAILED",
                message=f"Failed to delete session: {str(e)}"
            )
        )

@router.post("/{session_id}/reset", response_model=StandardResponse)
async def reset_context(session_id: str):
    """Reset session context (clear current bin)"""
    try:
        session = session_manager.set_current_bin(session_id, None)
        
        if not session:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="SESSION_NOT_FOUND",
                    message=f"Session {session_id} not found or expired"
                )
            )
        
        return StandardResponse(
            success=True,
            data={
                "session": session.to_dict(),
                "message": "Context reset - no current bin set"
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CONTEXT_RESET_FAILED",
                message=f"Failed to reset context: {str(e)}"
            )
        )

@router.get("", response_model=StandardResponse)
async def list_sessions():
    """List all active sessions (for debugging/admin)"""
    try:
        sessions = session_manager.get_all_sessions()
        session_count = len(sessions)
        
        return StandardResponse(
            success=True,
            data={
                "session_count": session_count,
                "sessions": [session.to_dict() for session in sessions.values()]
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="SESSION_LIST_FAILED",
                message=f"Failed to list sessions: {str(e)}"
            )
        )
