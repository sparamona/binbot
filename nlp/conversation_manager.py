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
    role: str  # "user", "assistant", or "function"
    content: str
    timestamp: float
    session_id: Optional[str] = None
    name: Optional[str] = None  # Required for function messages

class ConversationHistory:
    """Manages conversation history for a single session"""
    
    def __init__(self, session_id: str, max_messages: int = 50, max_age_minutes: int = 10):
        self.session_id = session_id
        self.max_messages = max_messages
        self.max_age_seconds = max_age_minutes * 60
        self.messages: List[ConversationMessage] = []
        self._lock = threading.Lock()
    
    def add_message(self, role: str, content: str, name: Optional[str] = None) -> None:
        """Add a message to the conversation history"""
        with self._lock:
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=time.time(),
                session_id=self.session_id,
                name=name
            )
            self.messages.append(message)
            logger.debug(f"Added {role} message to session {self.session_id}: {content[:100]}...")
            logger.debug(f"Total messages in session {self.session_id}: {len(self.messages)}")
            self._cleanup_old_messages()
    
    def get_messages(self, include_system_prompt: bool = True, max_messages: int = 3) -> List[Dict[str, str]]:
        """Get conversation messages formatted for LLM, limited to recent messages"""
        with self._lock:
            self._cleanup_old_messages()

            messages = []

            # Add system prompt if requested
            if include_system_prompt:
                messages.append({
                    "role": "system",
                    "content": self._get_system_prompt()
                })

            # Add conversation history (limit to last N messages)
            recent_messages = self.messages[-max_messages:] if max_messages > 0 else self.messages
            for msg in recent_messages:
                message_dict = {
                    "role": msg.role,
                    "content": msg.content
                }
                # Add name field for function messages (required by OpenAI)
                if msg.role == "function" and msg.name:
                    message_dict["name"] = msg.name
                messages.append(message_dict)

            logger.debug(f"Returning {len(messages)} messages for session {self.session_id} (limited to last {max_messages})")
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
        return """You are BinBot, an intelligent inventory management assistant. You help users manage their inventory by understanding their natural language requests and calling the appropriate functions.

🎯 YOUR ROLE:
- Understand natural language commands about inventory management
- Call the appropriate functions to perform inventory operations
- Handle conversational and casual language naturally
- Use conversation context to understand follow-up commands
- Provide helpful responses based on function call results

🔧 AVAILABLE FUNCTIONS:
- add_items_to_bin: Add items to a specific bin
- remove_items_from_bin: Remove items from a specific bin
- move_items_between_bins: Move items from one bin to another
- search_for_items: Search for items in the inventory
- list_bin_contents: List all items in a specific bin

💬 CONVERSATION STYLE:
- Be friendly and helpful
- Use conversation context for follow-up commands like "also add nuts" or "what about bin 5"
- Ask for clarification when commands are ambiguous
- Confirm successful operations and provide clear feedback

🎯 COMMAND EXAMPLES:
- "add bolts to bin 3" → call add_items_to_bin with items=["bolts"], bin_id="3"
- "put screws and nuts in bin 5" → call add_items_to_bin with items=["screws", "nuts"], bin_id="5"
- "also add washers" (after previous add) → call add_items_to_bin with items=["washers"], bin_id=[previous bin]
- "remove wires from bin 2" → call remove_items_from_bin with items=["wires"], bin_id="2"
- "move springs from bin 1 to bin 4" → call move_items_between_bins with items=["springs"], source_bin_id="1", target_bin_id="4"
- "what's in bin 8" → call list_bin_contents with bin_id="8"
- "find my electronics" → call search_for_items with query="electronics"
- "where is the sudoku" → call search_for_items with query="sudoku"

⚠️ IMPORTANT GUIDELINES:
- Be flexible with natural language variations
- Handle casual language and different ways of expressing the same intent
- Use conversation context to resolve ambiguous references like "also add" or "that bin"
- Parse item lists naturally (handle "and", commas, multiple items)
- Extract bin numbers from various formats ("bin 3", "bin number 5", "the 3rd bin")
- If information is missing or ambiguous, ask for clarification in a helpful way
- Always call the appropriate function - don't just provide text responses about inventory"""

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

    def add_message(self, session_id: str, role: str, content: str, name: Optional[str] = None) -> None:
        """Add a message with any role to the conversation"""
        logger.debug(f"Adding {role} message to session {session_id}: {content[:100]}...")
        conversation = self.get_conversation(session_id)
        conversation.add_message(role, content, name)

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation messages formatted for LLM (alias for get_messages_for_llm)"""
        return self.get_messages_for_llm(session_id)
    
    def get_messages_for_llm(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation messages formatted for LLM (limited to last 3 messages)"""
        logger.debug(f"Getting messages for LLM for session {session_id}")
        conversation = self.get_conversation(session_id)
        messages = conversation.get_messages(include_system_prompt=True, max_messages=3)
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
