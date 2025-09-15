"""
Function-Based Command Processing Engine for BinBot Natural Language Interface

This module uses OpenAI function calling to process natural language commands
instead of explicit JSON parsing. It handles conversation history, function execution,
and response formatting.
"""

import asyncio
import uuid
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .conversation_manager import conversation_manager
from .function_definitions import get_inventory_functions
from .function_handler import FunctionCallHandler, FunctionCallResult

logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """Result of executing a command"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    function_calls: List[Dict[str, Any]] = None

class FunctionCommandProcessor:
    """Processes natural language commands using OpenAI function calling"""

    def __init__(self, db_client, embedding_service, llm_client):
        self.db_client = db_client
        self.embedding_service = embedding_service
        self.llm_client = llm_client
        
        # Initialize function handler
        self.function_handler = FunctionCallHandler(db_client, embedding_service)
        
        # Get function definitions for OpenAI
        self.functions = get_inventory_functions()

    async def process_command(self, command_text: str, session_id: Optional[str] = None) -> CommandResult:
        """Process a natural language command using function calling"""

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated new session ID: {session_id}")
        else:
            logger.debug(f"Using provided session ID: {session_id}")

        logger.info(f"Processing command: '{command_text}' for session {session_id}")

        try:
            # Add user message to conversation
            conversation_manager.add_message(session_id, "user", command_text)
            
            # Get conversation history for context
            messages = conversation_manager.get_messages(session_id)
            
            # Call LLM with function calling enabled
            response = await self.llm_client.chat_completion(
                messages=messages,
                tools=self.functions,
                tool_choice="auto",  # Let OpenAI decide when to call functions
                temperature=0.7,
                max_tokens=1000
            )
            
            # Process the response
            return await self._process_llm_response(response, session_id, command_text)
            
        except Exception as e:
            logger.error(f"Error processing command '{command_text}': {e}")
            return CommandResult(
                success=False,
                message="Sorry, I encountered an error processing your request.",
                error=str(e)
            )

    async def _process_llm_response(self, response, session_id: str, original_command: str) -> CommandResult:
        """Process the LLM response and handle function calls"""
        
        try:
            choice = response.choices[0]
            message = choice.message
            
            # Check if the LLM wants to call functions
            if hasattr(message, 'tool_calls') and message.tool_calls:
                return await self._handle_function_calls(message, session_id, original_command)
            
            # If no function calls, this is a regular text response
            elif hasattr(message, 'content') and message.content:
                # Add assistant response to conversation
                conversation_manager.add_message(session_id, "assistant", message.content)
                
                return CommandResult(
                    success=True,
                    message=message.content,
                    data={"type": "text_response"}
                )
            
            else:
                logger.warning(f"Unexpected LLM response format: {response}")
                return CommandResult(
                    success=False,
                    message="I'm not sure how to help with that. Could you rephrase your request?",
                    error="Unexpected response format from LLM"
                )
                
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            return CommandResult(
                success=False,
                message="Sorry, I had trouble understanding the response.",
                error=str(e)
            )

    async def _handle_function_calls(self, message, session_id: str, original_command: str) -> CommandResult:
        """Handle function calls from the LLM"""
        
        function_results = []
        all_successful = True
        combined_message = ""
        
        try:
            # Execute each function call
            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    function_name = tool_call.function.name
                    
                    try:
                        # Parse function arguments
                        function_args = json.loads(tool_call.function.arguments)
                        logger.info(f"Calling function {function_name} with args: {function_args}")
                        
                        # Execute the function
                        result = await self.function_handler.execute_function_call(
                            function_name, function_args
                        )
                        
                        function_results.append({
                            "function_name": function_name,
                            "arguments": function_args,
                            "result": result.data,
                            "success": result.success,
                            "error": result.error
                        })
                        
                        if not result.success:
                            all_successful = False
                        
                        # Format user-friendly message
                        user_message = self.function_handler.format_function_result_for_user(result)
                        if combined_message:
                            combined_message += "\n\n" + user_message
                        else:
                            combined_message = user_message
                            
                        # Add function result to conversation for context (without full data to save tokens)
                        if result.data and isinstance(result.data, dict):
                            # Create a summary without large data like embeddings
                            summary_data = {}
                            for key, value in result.data.items():
                                if key == "added_items" and isinstance(value, list):
                                    # Summarize added items without embeddings
                                    summary_data[key] = [
                                        {k: v for k, v in item.items() if k != "embedding"}
                                        for item in value
                                    ]
                                elif key not in ["embedding"]:
                                    summary_data[key] = value
                            function_result_text = f"Function {function_name} result: {json.dumps(summary_data)}"
                        else:
                            function_result_text = f"Function {function_name} result: completed"

                        conversation_manager.add_message(
                            session_id,
                            "function",
                            function_result_text,
                            name=function_name
                        )
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in function arguments: {tool_call.function.arguments}")
                        all_successful = False
                        error_msg = f"❌ Error: Invalid function arguments for {function_name}"
                        if combined_message:
                            combined_message += "\n\n" + error_msg
                        else:
                            combined_message = error_msg
                            
                    except Exception as e:
                        logger.error(f"Error executing function {function_name}: {e}")
                        all_successful = False
                        error_msg = f"❌ Error executing {function_name}: {str(e)}"
                        if combined_message:
                            combined_message += "\n\n" + error_msg
                        else:
                            combined_message = error_msg
            
            # Add the combined response to conversation
            if combined_message:
                conversation_manager.add_message(session_id, "assistant", combined_message)
            
            return CommandResult(
                success=all_successful,
                message=combined_message or "Operations completed",
                data={"type": "function_calls", "results": function_results},
                function_calls=function_results
            )
            
        except Exception as e:
            logger.error(f"Error handling function calls: {e}")
            return CommandResult(
                success=False,
                message="Sorry, I encountered an error executing your request.",
                error=str(e)
            )

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return conversation_manager.get_messages(session_id)

    def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history for a session"""
        conversation_manager.clear_session(session_id)

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return conversation_manager.get_active_sessions()
