"""
Natural Language Command Parser for BinBot Inventory System

This module uses LLM to parse natural language commands like:
- "add bolts to bin 3"
- "also add nuts"
- "remove wires from bin 2"
- "move screws from bin 1 to bin 5"
- "search for electronics"
- "what's in bin 7?"
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CommandType(Enum):
    ADD = "add"
    REMOVE = "remove"
    MOVE = "move"
    SEARCH = "search"
    LIST_BIN = "list_bin"
    HELP = "help"
    UNKNOWN = "unknown"

@dataclass
class ParsedCommand:
    """Represents a parsed natural language command"""
    action: str
    items: List[str] = None
    source_bin: Optional[str] = None
    target_bin: Optional[str] = None
    search_query: Optional[str] = None
    bin_id: Optional[str] = None
    confidence: float = 0.0
    missing_info: List[str] = None
    clarification_needed: Optional[str] = None
    raw_command: str = ""

    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.missing_info is None:
            self.missing_info = []

class LLMCommandParser:
    """LLM-based parser for natural language inventory commands"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def parse_command(self, messages: List[Dict[str, str]]) -> ParsedCommand:
        """Parse a natural language command using LLM with conversation context"""

        if not self.llm_client:
            return ParsedCommand(
                action="unknown",
                raw_command=messages[-1]["content"] if messages else "",
                confidence=0.0,
                clarification_needed="LLM client not available"
            )

        try:
            # Get the user's latest message
            user_message = messages[-1]["content"] if messages else ""

            # Call LLM to parse the command
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=500
            )

            # Parse the LLM response as JSON
            response_text = response.content.strip()
            logger.debug(f"Raw LLM response: {response_text}")

            # Handle cases where LLM returns text instead of JSON
            if not response_text.startswith('{'):
                logger.warning(f"LLM returned non-JSON response: {response_text}")
                # Try to extract useful information from the response
                if any(word in response_text.lower() for word in ['bin', 'add', 'remove', 'search', 'move', 'find']):
                    return ParsedCommand(
                        action="unknown",
                        raw_command=user_message,
                        confidence=0.0,
                        clarification_needed=f"I understood you want to do something with inventory, but need you to be more specific. Try commands like 'add [item] to bin [number]' or 'what's in bin [number]'."
                    )
                else:
                    return ParsedCommand(
                        action="unknown",
                        raw_command=user_message,
                        confidence=0.0,
                        clarification_needed="I can help you manage your inventory. Try commands like 'add bolts to bin 3', 'what's in bin 5', or 'search for electronics'."
                    )

            # Parse JSON response
            parsed_json = json.loads(response_text)
            logger.debug(f"Parsed JSON: {parsed_json}")

            # Create ParsedCommand from JSON
            return ParsedCommand(
                action=parsed_json.get("action", "unknown"),
                items=parsed_json.get("items", []),
                source_bin=parsed_json.get("source_bin"),
                target_bin=parsed_json.get("target_bin"),
                search_query=parsed_json.get("search_query"),
                bin_id=parsed_json.get("bin_id"),
                confidence=parsed_json.get("confidence", 0.0),
                missing_info=parsed_json.get("missing_info", []),
                clarification_needed=parsed_json.get("clarification_needed"),
                raw_command=user_message
            )

        except json.JSONDecodeError as e:
            return ParsedCommand(
                action="unknown",
                raw_command=user_message,
                confidence=0.0,
                clarification_needed=f"Could not parse command. Please try rephrasing."
            )
        except Exception as e:
            return ParsedCommand(
                action="unknown",
                raw_command=user_message,
                confidence=0.0,
                clarification_needed=f"Error parsing command: {str(e)}"
            )

    def validate_command(self, parsed_command: ParsedCommand) -> List[str]:
        """Validate that a parsed command has all required fields"""

        required_fields = {
            "add": ["items", "target_bin"],
            "remove": ["items", "source_bin"],
            "move": ["items", "source_bin", "target_bin"],
            "search": ["search_query"],
            "list_bin": ["bin_id"]
        }

        action = parsed_command.action
        if action not in required_fields:
            return []  # No validation needed for unknown/help commands

        missing = []
        for field in required_fields[action]:
            value = getattr(parsed_command, field, None)
            if not value or (isinstance(value, list) and len(value) == 0):
                missing.append(field)

        return missing
