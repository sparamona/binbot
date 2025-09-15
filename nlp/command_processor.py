"""
Command Processing Engine for BinBot Natural Language Interface

This module takes parsed commands and executes them by calling the appropriate API endpoints.
It handles conversation history, error handling, and response formatting.
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

# Set up logger for command processor
logger = logging.getLogger(__name__)

from .command_parser import ParsedCommand, LLMCommandParser
from .conversation_manager import conversation_manager
from api_schemas import AddItemRequest, RemoveItemRequest, MoveItemRequest, StandardResponse

@dataclass
class CommandResult:
    """Result of executing a command"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggestions: List[str] = None

class CommandProcessor:
    """Processes parsed commands and executes them via API calls"""

    def __init__(self, db_client, embedding_service, llm_client):
        self.db_client = db_client
        self.embedding_service = embedding_service
        self.llm_client = llm_client
        self.parser = LLMCommandParser(llm_client)

    async def process_command(self, command_text: str, session_id: Optional[str] = None) -> CommandResult:
        """Process a natural language command and execute it"""

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated new session ID: {session_id}")
        else:
            logger.debug(f"Using provided session ID: {session_id}")

        logger.info(f"Processing command: '{command_text}' for session {session_id}")

        # Add user message to conversation history
        conversation_manager.add_user_message(session_id, command_text)

        # Get conversation history for LLM
        messages = conversation_manager.get_messages_for_llm(session_id)
        logger.debug(f"Sending {len(messages)} messages to LLM for parsing")

        # Parse the command using LLM
        parsed_command = await self.parser.parse_command(messages)
        logger.debug(f"LLM parsed command: action={parsed_command.action}, items={parsed_command.items}, "
                    f"source_bin={parsed_command.source_bin}, target_bin={parsed_command.target_bin}, "
                    f"confidence={parsed_command.confidence}")
        if hasattr(parsed_command, 'missing_info'):
            logger.debug(f"Missing info: {parsed_command.missing_info}")
        if hasattr(parsed_command, 'clarification_needed'):
            logger.debug(f"Clarification needed: {parsed_command.clarification_needed}")

        # Check if we need clarification
        if parsed_command.clarification_needed:
            response_message = parsed_command.clarification_needed
            conversation_manager.add_assistant_message(session_id, response_message)
            return CommandResult(
                success=False,
                message=response_message,
                suggestions=[
                    "add [item] to bin [number]",
                    "remove [item] from bin [number]",
                    "move [item] from bin [number] to bin [number]",
                    "search for [item]",
                    "what's in bin [number]?"
                ]
            )

        # Validate command has all required fields
        missing_fields = self.parser.validate_command(parsed_command)
        if missing_fields:
            clarification = self._generate_clarification_message(parsed_command.action, missing_fields)
            conversation_manager.add_assistant_message(session_id, clarification)
            return CommandResult(
                success=False,
                message=clarification
            )

        # Handle low confidence commands
        if parsed_command.confidence < 0.5:
            response_message = f"I'm not sure what you mean by '{command_text}'. Try commands like 'add bolts to bin 3' or 'search for electronics'."
            conversation_manager.add_assistant_message(session_id, response_message)
            return CommandResult(
                success=False,
                message=response_message,
                suggestions=[
                    "add [item] to bin [number]",
                    "remove [item] from bin [number]",
                    "move [item] from bin [number] to bin [number]",
                    "search for [item]",
                    "what's in bin [number]?"
                ]
            )

        # Execute the command based on action
        try:
            if parsed_command.action == "add":
                result = await self._execute_add_command(parsed_command, session_id)
            elif parsed_command.action == "remove":
                result = await self._execute_remove_command(parsed_command, session_id)
            elif parsed_command.action == "move":
                result = await self._execute_move_command(parsed_command, session_id)
            elif parsed_command.action == "search":
                result = await self._execute_search_command(parsed_command)
            elif parsed_command.action == "list_bin":
                result = await self._execute_list_bin_command(parsed_command)
            elif parsed_command.action == "help":
                result = self._execute_help_command()
            else:
                result = CommandResult(
                    success=False,
                    message="I don't understand that command yet.",
                    suggestions=[
                        "add [item] to bin [number]",
                        "remove [item] from bin [number]",
                        "search for [item]"
                    ]
                )

            # Add assistant response to conversation history
            conversation_manager.add_assistant_message(session_id, result.message)

            return result

        except Exception as e:
            error_message = f"Error executing command: {str(e)}"
            conversation_manager.add_assistant_message(session_id, error_message)
            return CommandResult(
                success=False,
                message=error_message,
                error=str(e)
            )

    def _generate_clarification_message(self, action: str, missing_fields: List[str]) -> str:
        """Generate a helpful clarification message for missing fields"""

        field_prompts = {
            "items": "what items",
            "target_bin": "which bin to add them to",
            "source_bin": "which bin to remove them from",
            "search_query": "what to search for",
            "bin_id": "which bin to list"
        }

        if len(missing_fields) == 1:
            field = missing_fields[0]
            prompt = field_prompts.get(field, field)
            return f"I need to know {prompt}. Can you specify?"
        else:
            prompts = [field_prompts.get(field, field) for field in missing_fields]
            return f"I need to know {', '.join(prompts[:-1])} and {prompts[-1]}. Can you specify?"
    
    async def _execute_add_command(self, command: ParsedCommand, session_id: Optional[str]) -> CommandResult:
        """Execute an add command"""
        if not command.target_bin:
            return CommandResult(
                success=False,
                message="I need to know which bin to add items to. Try 'add [item] to bin [number]'."
            )

        if not command.items:
            return CommandResult(
                success=False,
                message="I need to know what items to add. Try 'add [item] to bin [number]'."
            )

        try:
            # Prepare items with embeddings (like the real add API does)
            prepared_items = []
            failed_items = []

            # First pass: validate and prepare all items with embeddings
            for item_name in command.items:
                item_name = item_name.strip()
                if not item_name:
                    failed_items.append({
                        "name": item_name,
                        "error": "Empty item name"
                    })
                    continue

                # Create description
                description = f"{item_name} in bin {command.target_bin}"

                # Generate embedding
                document_text = f"{item_name} - {description}"
                embedding = self.embedding_service.generate_embedding(document_text)

                if embedding is None:
                    failed_items.append({
                        "name": item_name,
                        "error": "Failed to generate embedding"
                    })
                    continue

                prepared_items.append({
                    "name": item_name,
                    "bin_id": command.target_bin,
                    "description": description,
                    "embedding": embedding
                })

            # If all items failed, return error
            if not prepared_items:
                error_messages = [f"{item['name']}: {item['error']}" for item in failed_items]
                return CommandResult(
                    success=False,
                    message=f"Failed to add items: {'; '.join(error_messages)}"
                )

            # Second pass: atomic bulk add operation
            result = self.db_client.add_documents_bulk(prepared_items)

            items_list = ", ".join([item["name"] for item in prepared_items])

            # Include warnings about failed items if any
            message = f"✅ Added {items_list} to bin {command.target_bin}"
            if failed_items:
                failed_names = [item["name"] for item in failed_items]
                message += f" (Failed to add: {', '.join(failed_names)})"

            return CommandResult(
                success=True,
                message=message,
                data=result
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to add items: {str(e)}",
                error=str(e)
            )
    
    async def _execute_remove_command(self, command: ParsedCommand, session_id: Optional[str]) -> CommandResult:
        """Execute a remove command"""
        if not command.source_bin:
            return CommandResult(
                success=False,
                message="I need to know which bin to remove items from. Try 'remove [item] from bin [number]'."
            )
        
        if not command.items:
            return CommandResult(
                success=False,
                message="I need to know what items to remove. Try 'remove [item] from bin [number]'."
            )
        
        try:
            # Search for items in the specified bin first
            removed_items = []
            for item in command.items:
                # Find matching items in the bin
                search_results = self.db_client.search_documents(
                    query=item,
                    limit=10,
                    min_relevance=0.6
                )
                
                # Filter by bin
                bin_matches = [
                    result for result in search_results.get('results', [])
                    if result.get('bin_id') == command.source_bin
                ]
                
                if bin_matches:
                    # Remove the best match
                    item_to_remove = bin_matches[0]
                    self.db_client.inventory_collection.delete(ids=[item_to_remove['id']])
                    removed_items.append(item_to_remove['name'])
                else:
                    return CommandResult(
                        success=False,
                        message=f"Could not find '{item}' in bin {command.source_bin}."
                    )
            
            items_list = ", ".join(removed_items)
            return CommandResult(
                success=True,
                message=f"✅ Removed {items_list} from bin {command.source_bin}",
                data={"removed_items": removed_items}
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to remove items: {str(e)}",
                error=str(e)
            )
    
    async def _execute_move_command(self, command: ParsedCommand, session_id: Optional[str]) -> CommandResult:
        """Execute a move command"""
        if not command.source_bin or not command.target_bin:
            return CommandResult(
                success=False,
                message="I need both source and target bins. Try 'move [item] from bin [number] to bin [number]'."
            )
        
        if not command.items:
            return CommandResult(
                success=False,
                message="I need to know what items to move."
            )
        
        try:
            moved_items = []
            for item in command.items:
                # Find item in source bin
                search_results = self.db_client.search_documents(
                    query=item,
                    limit=10,
                    min_relevance=0.6
                )
                
                bin_matches = [
                    result for result in search_results.get('results', [])
                    if result.get('bin_id') == command.source_bin
                ]
                
                if bin_matches:
                    item_to_move = bin_matches[0]
                    # Update the bin_id
                    self.db_client.inventory_collection.update(
                        ids=[item_to_move['id']],
                        metadatas=[{
                            **item_to_move,
                            'bin_id': command.target_bin,
                            'description': f"{item_to_move['name']} in bin {command.target_bin}"
                        }]
                    )
                    moved_items.append(item_to_move['name'])
                else:
                    return CommandResult(
                        success=False,
                        message=f"Could not find '{item}' in bin {command.source_bin}."
                    )
            
            items_list = ", ".join(moved_items)
            return CommandResult(
                success=True,
                message=f"✅ Moved {items_list} from bin {command.source_bin} to bin {command.target_bin}",
                data={"moved_items": moved_items}
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to move items: {str(e)}",
                error=str(e)
            )
    
    async def _execute_search_command(self, command: ParsedCommand) -> CommandResult:
        """Execute a search command"""
        if not command.search_query:
            return CommandResult(
                success=False,
                message="I need to know what to search for. Try 'search for [item]'."
            )
        
        try:
            results = self.db_client.search_documents(
                query=command.search_query,
                limit=10,
                min_relevance=0.6
            )
            
            if not results.get('results'):
                return CommandResult(
                    success=True,
                    message=f"No items found matching '{command.search_query}'.",
                    data={"results": []}
                )
            
            # Format results nicely
            result_lines = []
            for item in results['results']:
                result_lines.append(f"• {item['name']} (bin {item['bin_id']}) - {item['relevance_score']:.1%} match")
            
            message = f"Found {len(results['results'])} items matching '{command.search_query}':\n" + "\n".join(result_lines)
            
            return CommandResult(
                success=True,
                message=message,
                data=results
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Search failed: {str(e)}",
                error=str(e)
            )
    
    async def _execute_list_bin_command(self, command: ParsedCommand) -> CommandResult:
        """Execute a list bin contents command"""
        if not command.bin_id:
            return CommandResult(
                success=False,
                message="I need to know which bin to list. Try 'what's in bin [number]?'."
            )

        try:
            # Search for all items in the specified bin
            all_results = self.db_client.inventory_collection.get(include=['metadatas'])

            bin_items = [
                metadata for metadata in all_results.get('metadatas', [])
                if metadata.get('bin_id') == command.bin_id
            ]

            if not bin_items:
                return CommandResult(
                    success=True,
                    message=f"Bin {command.bin_id} is empty.",
                    data={"items": []}
                )

            # Format the items list
            item_lines = [f"• {item['name']}" for item in bin_items]
            message = f"Bin {command.bin_id} contains {len(bin_items)} items:\n" + "\n".join(item_lines)

            return CommandResult(
                success=True,
                message=message,
                data={"items": bin_items}
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to list bin contents: {str(e)}",
                error=str(e)
            )
    
    async def _execute_undo_command(self, session_id: Optional[str]) -> CommandResult:
        """Execute an undo command"""
        # This would integrate with the audit log system
        return CommandResult(
            success=False,
            message="Undo functionality is not yet implemented. This will be added in Phase 11."
        )
    
    def _execute_help_command(self) -> CommandResult:
        """Execute a help command"""
        help_text = """
🤖 **BinBot Natural Language Commands**

**Adding items:**
• "add bolts to bin 3"
• "put screws in bin 5"
• "also add nuts" (uses previous bin)

**Removing items:**
• "remove wires from bin 2"
• "take out resistors from bin 7"

**Moving items:**
• "move capacitors from bin 1 to bin 4"

**Searching:**
• "search for electronics"
• "find tools"

**Listing bin contents:**
• "what's in bin 3?"
• "show bin 7"

**Other:**
• "help" - show this help
• "undo" - undo last command (coming soon)
        """
        
        return CommandResult(
            success=True,
            message=help_text.strip()
        )
