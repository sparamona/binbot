"""
Conversation History Manager for BinBot Natural Language Interface

Manages conversation history for context-aware natural language processing.
Keeps up to 50 messages, with no messages over 10 minutes old.
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import logging

# Set up logger for conversation manager
logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    session_id: Optional[str] = None

class ConversationHistory:
    """Manages conversation history for a single session"""
    
    def __init__(self, session_id: str, max_messages: int = 50, max_age_minutes: int = 10):
        self.session_id = session_id
        self.max_messages = max_messages
        self.max_age_seconds = max_age_minutes * 60
        self.messages: List[ConversationMessage] = []
        self._lock = threading.Lock()
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history"""
        with self._lock:
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=time.time(),
                session_id=self.session_id
            )
            self.messages.append(message)
            logger.debug(f"Added {role} message to session {self.session_id}: {content[:100]}...")
            logger.debug(f"Total messages in session {self.session_id}: {len(self.messages)}")
            self._cleanup_old_messages()
    
    def get_messages(self, include_system_prompt: bool = True) -> List[Dict[str, str]]:
        """Get conversation messages formatted for LLM"""
        with self._lock:
            self._cleanup_old_messages()

            messages = []

            # Add system prompt if requested
            if include_system_prompt:
                messages.append({
                    "role": "system",
                    "content": self._get_system_prompt()
                })

            # Add conversation history
            for msg in self.messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            logger.debug(f"Returning {len(messages)} messages for session {self.session_id}")
            message_summary = [f"{m['role']}: {m['content'][:50]}..." for m in messages]
            logger.debug(f"Messages: {message_summary}")

            return messages
    
    def _cleanup_old_messages(self) -> None:
        """Remove old messages and enforce message limit"""
        current_time = time.time()
        
        # Remove messages older than max_age_seconds
        self.messages = [
            msg for msg in self.messages
            if current_time - msg.timestamp <= self.max_age_seconds
        ]
        
        # Enforce message limit (keep most recent messages)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are BinBot, an AI assistant for inventory management. Users can give you natural language commands to manage their inventory bins.

CRITICAL: You MUST ALWAYS respond with valid JSON only. Never respond with natural language text.

Your job is to parse user commands and return structured JSON that can be used to call inventory APIs.

Supported actions:
- "add": Add items to a bin (requires: items, target_bin)
- "remove": Remove items from a bin (requires: items, source_bin)
- "move": Move items between bins (requires: items, source_bin, target_bin)
- "search": Search for items (requires: search_query)
- "list_bin": List contents of a bin (requires: bin_id)

ALWAYS return JSON in this exact format:
{
  "action": "add|remove|move|search|list_bin",
  "items": ["item1", "item2"],
  "source_bin": "1",
  "target_bin": "3",
  "search_query": "electronics",
  "bin_id": "5",
  "confidence": 0.95,
  "missing_info": ["target_bin"],
  "clarification_needed": "Which bin should I add the items to?"
}

Rules:
1. Use conversation context to fill in missing information from previous messages
2. If information is missing, set "missing_info" and "clarification_needed"
3. Parse item lists carefully (handle "and", commas, etc.)
4. Extract bin numbers from text like "bin 3" or "bin number 5"
5. For "also add" commands, look at the conversation history to find the bin number from the previous add command
6. Set confidence based on how clear the command is
7. ALWAYS use actual bin numbers, never placeholders like "[previous_bin]"
8. NEVER respond with natural language - ONLY JSON

Examples:
- "add bolts to bin 3" → {"action": "add", "items": ["bolts"], "target_bin": "3", "confidence": 0.95}
- "also add nuts" (after "add bolts to bin 3") → {"action": "add", "items": ["nuts"], "target_bin": "3", "confidence": 0.9}
- "remove wires" → {"action": "remove", "items": ["wires"], "missing_info": ["source_bin"], "clarification_needed": "Which bin should I remove the wires from?", "confidence": 0.7}"""

    def clear(self) -> None:
        """Clear all messages from the conversation"""
        with self._lock:
            self.messages.clear()
    
    def get_message_count(self) -> int:
        """Get the current number of messages"""
        with self._lock:
            return len(self.messages)

class ConversationManager:
    """Manages conversation histories for multiple sessions"""
    
    def __init__(self, max_messages: int = 50, max_age_minutes: int = 10):
        self.max_messages = max_messages
        self.max_age_minutes = max_age_minutes
        self.conversations: Dict[str, ConversationHistory] = {}
        self._lock = threading.Lock()
    
    def get_conversation(self, session_id: str) -> ConversationHistory:
        """Get or create a conversation history for a session"""
        with self._lock:
            if session_id not in self.conversations:
                logger.debug(f"Creating new conversation for session {session_id}")
                self.conversations[session_id] = ConversationHistory(
                    session_id=session_id,
                    max_messages=self.max_messages,
                    max_age_minutes=self.max_age_minutes
                )
            else:
                logger.debug(f"Retrieved existing conversation for session {session_id}")
            return self.conversations[session_id]
    
    def add_user_message(self, session_id: str, content: str) -> None:
        """Add a user message to the conversation"""
        logger.debug(f"Adding user message to session {session_id}: {content}")
        conversation = self.get_conversation(session_id)
        conversation.add_message("user", content)

    def add_assistant_message(self, session_id: str, content: str) -> None:
        """Add an assistant message to the conversation"""
        logger.debug(f"Adding assistant message to session {session_id}: {content[:100]}...")
        conversation = self.get_conversation(session_id)
        conversation.add_message("assistant", content)
    
    def get_messages_for_llm(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation messages formatted for LLM"""
        logger.debug(f"Getting messages for LLM for session {session_id}")
        conversation = self.get_conversation(session_id)
        messages = conversation.get_messages(include_system_prompt=True)
        logger.debug(f"Returning {len(messages)} messages to LLM for session {session_id}")
        return messages
    
    def clear_conversation(self, session_id: str) -> None:
        """Clear a specific conversation"""
        with self._lock:
            if session_id in self.conversations:
                self.conversations[session_id].clear()
    
    def cleanup_old_conversations(self) -> None:
        """Remove conversations with no recent activity"""
        current_time = time.time()
        max_age_seconds = self.max_age_minutes * 60
        
        with self._lock:
            sessions_to_remove = []
            for session_id, conversation in self.conversations.items():
                if not conversation.messages:
                    sessions_to_remove.append(session_id)
                    continue
                
                # Check if the most recent message is too old
                latest_message = conversation.messages[-1]
                if current_time - latest_message.timestamp > max_age_seconds:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.conversations[session_id]
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        with self._lock:
            return list(self.conversations.keys())
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about conversations"""
        with self._lock:
            total_sessions = len(self.conversations)
            total_messages = sum(
                len(conv.messages) for conv in self.conversations.values()
            )
            
            return {
                "active_sessions": total_sessions,
                "total_messages": total_messages,
                "max_messages_per_session": self.max_messages,
                "max_age_minutes": self.max_age_minutes
            }

# Global conversation manager instance
conversation_manager = ConversationManager(max_messages=50, max_age_minutes=10)
