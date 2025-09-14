"""
Session Management for BinBot
Handles user sessions and context state for multi-turn conversations
"""

import uuid
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class SessionContext:
    """Represents the context state for a user session"""
    session_id: str
    current_bin_id: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if the session has expired"""
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.now() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session context to dictionary for API responses"""
        return {
            "session_id": self.session_id,
            "current_bin_id": self.current_bin_id,
            "last_activity": self.last_activity.isoformat(),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class SessionManager:
    """Manages user sessions and context state"""
    
    def __init__(self, default_timeout_minutes: int = 30):
        self.sessions: Dict[str, SessionContext] = {}
        self.default_timeout_minutes = default_timeout_minutes
    
    def create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Create a new session or return existing one"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id in self.sessions:
            # Update existing session activity
            session = self.sessions[session_id]
            session.update_activity()
            return session
        
        # Create new session
        session = SessionContext(session_id=session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get an existing session by ID"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session has expired
        if session.is_expired(self.default_timeout_minutes):
            self.delete_session(session_id)
            return None
        
        # Update activity and return
        session.update_activity()
        return session
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session(session_id)
    
    def update_session_context(self, session_id: str, **kwargs) -> Optional[SessionContext]:
        """Update session context with new values"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Update context fields
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
            else:
                session.metadata[key] = value
        
        session.update_activity()
        return session
    
    def set_current_bin(self, session_id: str, bin_id: Optional[str]) -> Optional[SessionContext]:
        """Set the current bin context for a session"""
        return self.update_session_context(session_id, current_bin_id=bin_id)
    
    def get_current_bin(self, session_id: str) -> Optional[str]:
        """Get the current bin context for a session"""
        session = self.get_session(session_id)
        return session.current_bin_id if session else None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions and return count of removed sessions"""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired(self.default_timeout_minutes):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def get_all_sessions(self) -> Dict[str, SessionContext]:
        """Get all active sessions (for debugging/admin purposes)"""
        # Clean up expired sessions first
        self.cleanup_expired_sessions()
        return self.sessions.copy()
    
    def get_session_count(self) -> int:
        """Get count of active sessions"""
        self.cleanup_expired_sessions()
        return len(self.sessions)


# Global session manager instance
session_manager = SessionManager()
