"""
Simple in-memory session management for BinBot
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.settings import SESSION_TTL_MINUTES
from utils.logging import setup_logger

# Set up logger for session management
logger = setup_logger(__name__)


class SessionManager:
    """Simple in-memory session store with TTL"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict] = {}
    
    def new_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        now = datetime.now()

        self._sessions[session_id] = {
            'session_id': session_id,
            'created_at': now,
            'last_accessed': now,
            'current_bin': '',
            'conversation': []
        }

        logger.info(f"NEW_SESSION created: {session_id[:8]}... (current_bin: '')")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data if it exists and hasn't expired"""
        if session_id not in self._sessions:
            logger.warning(f"GET_SESSION: Session {session_id[:8]}... not found")
            return None

        session = self._sessions[session_id]

        # Check if expired
        if self._is_expired(session):
            logger.info(f"GET_SESSION: Session {session_id[:8]}... expired, removing")
            del self._sessions[session_id]
            return None

        # Update last accessed
        session['last_accessed'] = datetime.now()
        logger.debug(f"GET_SESSION: {session_id[:8]}... (current_bin: '{session['current_bin']}')")
        return session
    
    def end_session(self, session_id: str):
        """Remove a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def set_current_bin(self, session_id: str, bin_id: str):
        """Set the current bin for a session"""
        session = self.get_session(session_id)
        if session:
            old_bin = session['current_bin']
            session['current_bin'] = bin_id
            logger.info(f"SET_CURRENT_BIN: {session_id[:8]}... '{old_bin}' → '{bin_id}'")
        else:
            logger.error(f"SET_CURRENT_BIN: Failed - session {session_id[:8]}... not found or expired")
        
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation"""
        session = self.get_session(session_id)
        if session:
            session['conversation'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_conversation(self, session_id: str) -> List[Dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        return session['conversation'] if session else []
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_ids = []
        for session_id, session in self._sessions.items():
            if self._is_expired(session):
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            del self._sessions[session_id]
        
        return len(expired_ids)
    
    def _is_expired(self, session: Dict) -> bool:
        """Check if a session has expired"""
        ttl = timedelta(minutes=SESSION_TTL_MINUTES)
        return datetime.now() - session['last_accessed'] > ttl


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager"""
    return _session_manager
