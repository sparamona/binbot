"""
Session management endpoints for BinBot
"""

from fastapi import APIRouter, HTTPException, Response
from api_schemas import SessionResponse, SessionInfoResponse, SessionInfo
from session.session_manager import get_session_manager

router = APIRouter()


@router.post("/api/session", response_model=SessionResponse)
async def start_session(response: Response):
    """Create a new session with UUID and set secure cookie"""
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    
    # Set HTTP-only cookie (30 minutes TTL)
    # Note: secure=False for development on localhost
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # Allow HTTP for development
        samesite="lax",  # Less strict for development
        max_age=30 * 60  # 30 minutes in seconds
    )
    
    return SessionResponse(success=True, session_id=session_id)


@router.get("/api/session/{session_id}", response_model=SessionInfoResponse)
async def get_session(session_id: str):
    """Retrieve session state and information"""
    session_manager = get_session_manager()
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session_info = SessionInfo(
        session_id=session_data['session_id'],
        created_at=session_data['created_at'].isoformat(),
        last_accessed=session_data['last_accessed'].isoformat(),
        current_bin=session_data['current_bin'],
        conversation=session_data['conversation']
    )
    
    return SessionInfoResponse(success=True, session=session_info)


@router.delete("/api/session/{session_id}", response_model=SessionResponse)
async def end_session(session_id: str, response: Response):
    """End session, clear from memory, and delete cookie"""
    session_manager = get_session_manager()
    session_manager.end_session(session_id)
    
    # Delete the session cookie
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=False,  # Match the creation settings
        samesite="lax"
    )
    
    return SessionResponse(success=True, session_id=session_id)
