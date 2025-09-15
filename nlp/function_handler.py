"""
Function Call Handler for OpenAI Function Calling

This module handles the execution of OpenAI function calls and maps them
to the appropriate inventory API operations.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from nlp.function_definitions import get_all_function_names

logger = logging.getLogger(__name__)

@dataclass
class FunctionCallResult:
    """Result of executing a function call"""
    success: bool
    data: Any = None
    error: str = None
    function_name: str = None
    parameters: Dict[str, Any] = None

class FunctionCallHandler:
    """Handles execution of OpenAI function calls for inventory operations"""

    def __init__(self, db_client, embedding_service):
        self.db_client = db_client
        self.embedding_service = embedding_service
        self.supported_functions = set(get_all_function_names())
    
    async def execute_function_call(self, function_name: str, parameters: Dict[str, Any]) -> FunctionCallResult:
        """
        Execute a function call with the given parameters.
        
        Args:
            function_name: Name of the function to execute
            parameters: Parameters for the function call
            
        Returns:
            FunctionCallResult with the execution result
        """
        logger.info(f"Executing function call: {function_name} with parameters: {parameters}")
        
        if function_name not in self.supported_functions:
            return FunctionCallResult(
                success=False,
                error=f"Unknown function: {function_name}",
                function_name=function_name,
                parameters=parameters
            )
        
        try:
            if function_name == "add_items_to_bin":
                return await self._handle_add_items(parameters)
            elif function_name == "remove_items_from_bin":
                return await self._handle_remove_items(parameters)
            elif function_name == "move_items_between_bins":
                return await self._handle_move_items(parameters)
            elif function_name == "search_for_items":
                return await self._handle_search_items(parameters)
            elif function_name == "list_bin_contents":
                return await self._handle_list_bin(parameters)
            else:
                return FunctionCallResult(
                    success=False,
                    error=f"Function {function_name} not implemented",
                    function_name=function_name,
                    parameters=parameters
                )
                
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error executing {function_name}: {str(e)}",
                function_name=function_name,
                parameters=parameters
            )
    
    async def _handle_add_items(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle add_items_to_bin function call"""
        items = parameters.get("items", [])
        bin_id = parameters.get("bin_id")

        if not items or not bin_id:
            return FunctionCallResult(
                success=False,
                error="Missing required parameters: items and bin_id",
                function_name="add_items_to_bin",
                parameters=parameters
            )

        try:
            # Prepare items with embeddings (like the real add API does)
            prepared_items = []
            failed_items = []

            # First pass: validate and prepare all items with embeddings
            for item_name in items:
                item_name = item_name.strip()
                if not item_name:
                    failed_items.append({
                        "name": item_name,
                        "error": "Empty item name"
                    })
                    continue

                # Create description
                description = f"{item_name} in bin {bin_id}"

                try:
                    # Generate embedding for the item
                    embedding = self.embedding_service.generate_embedding(description)

                    prepared_items.append({
                        "id": str(uuid.uuid4()),
                        "name": item_name,
                        "description": description,
                        "bin_id": bin_id,
                        "embedding": embedding,
                        "created_at": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Failed to generate embedding for item '{item_name}': {e}")
                    failed_items.append({
                        "name": item_name,
                        "error": f"Failed to generate embedding: {str(e)}"
                    })

            # Second pass: add all prepared items to database using bulk add
            if prepared_items:
                try:
                    # Use bulk add for better performance and transaction safety
                    bulk_result = self.db_client.add_documents_bulk(prepared_items)

                    if bulk_result.get("success", False):
                        added_items = prepared_items
                        for item in added_items:
                            logger.info(f"Added item '{item['name']}' to bin {bin_id}")
                    else:
                        # If bulk add failed, add individual error for each item
                        error_msg = bulk_result.get("error", "Unknown bulk add error")
                        for item in prepared_items:
                            failed_items.append({
                                "name": item["name"],
                                "error": f"Bulk add failed: {error_msg}"
                            })
                except Exception as e:
                    logger.error(f"Failed to bulk add items to database: {e}")
                    # If bulk add failed, add individual error for each item
                    for item in prepared_items:
                        failed_items.append({
                            "name": item["name"],
                            "error": f"Database error: {str(e)}"
                        })

            # Prepare response
            success = len(added_items) > 0
            message_parts = []

            if added_items:
                item_names = [item["name"] for item in added_items]
                message_parts.append(f"Successfully added {', '.join(item_names)} to bin {bin_id}")

            if failed_items:
                failed_names = [item["name"] for item in failed_items]
                message_parts.append(f"Failed to add {', '.join(failed_names)}")

            result_data = {
                "added_items": added_items,
                "failed_items": failed_items,
                "bin_id": bin_id,
                "success": success
            }

            return FunctionCallResult(
                success=success,
                data=result_data,
                function_name="add_items_to_bin",
                parameters=parameters
            )

        except Exception as e:
            logger.error(f"Error in add_items function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error adding items: {str(e)}",
                function_name="add_items_to_bin",
                parameters=parameters
            )
    
    async def _handle_remove_items(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle remove_items_from_bin function call"""
        items = parameters.get("items", [])
        bin_id = parameters.get("bin_id")

        if not items or not bin_id:
            return FunctionCallResult(
                success=False,
                error="Missing required parameters: items and bin_id",
                function_name="remove_items_from_bin",
                parameters=parameters
            )

        try:
            # Search for and remove items from the specified bin
            removed_items = []
            not_found_items = []

            for item in items:
                # Find matching items in the bin
                search_results = self.db_client.search_documents(
                    query=item,
                    limit=10,
                    min_relevance=0.6
                )

                # Filter by bin
                bin_matches = [
                    result for result in search_results.get('results', [])
                    if result.get('bin_id') == bin_id
                ]

                if bin_matches:
                    # Remove the best match
                    item_to_remove = bin_matches[0]
                    success = self.db_client.remove_document(item_to_remove['id'])

                    if success:
                        removed_items.append(item_to_remove['name'])

                        # Create audit log entry
                        audit_entry = {
                            "operation_id": str(uuid.uuid4()),
                            "operation_type": "remove",
                            "item_id": item_to_remove['id'],
                            "item_name": item_to_remove['name'],
                            "bin_id": bin_id,
                            "description": f"Removed '{item_to_remove['name']}' from bin {bin_id}",
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {
                                "original_query": item,
                                "relevance_score": item_to_remove.get("relevance_score", 0.0)
                            }
                        }
                        self.db_client.add_audit_log_entry(audit_entry)
                    else:
                        not_found_items.append(item)
                else:
                    not_found_items.append(item)

            # Prepare result
            if removed_items:
                if not_found_items:
                    message = f"Removed {', '.join(removed_items)} from bin {bin_id}. Could not find: {', '.join(not_found_items)}"
                else:
                    message = f"Successfully removed {', '.join(removed_items)} from bin {bin_id}"

                result_data = {
                    "removed_items": removed_items,
                    "not_found_items": not_found_items,
                    "bin_id": bin_id,
                    "success": True,
                    "message": message
                }

                return FunctionCallResult(
                    success=True,
                    data=result_data,
                    function_name="remove_items_from_bin",
                    parameters=parameters
                )
            else:
                return FunctionCallResult(
                    success=False,
                    error=f"Could not find any of the specified items ({', '.join(items)}) in bin {bin_id}",
                    function_name="remove_items_from_bin",
                    parameters=parameters
                )

        except Exception as e:
            logger.error(f"Error in remove_items function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error removing items: {str(e)}",
                function_name="remove_items_from_bin",
                parameters=parameters
            )
    
    async def _handle_move_items(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle move_items_between_bins function call"""
        items = parameters.get("items", [])
        source_bin_id = parameters.get("source_bin_id")
        target_bin_id = parameters.get("target_bin_id")

        if not items or not source_bin_id or not target_bin_id:
            return FunctionCallResult(
                success=False,
                error="Missing required parameters: items, source_bin_id, and target_bin_id",
                function_name="move_items_between_bins",
                parameters=parameters
            )

        try:
            # Move items from source bin to target bin
            moved_items = []
            not_found_items = []

            for item in items:
                # Find matching items in the source bin
                search_results = self.db_client.search_documents(
                    query=item,
                    limit=10,
                    min_relevance=0.6
                )

                # Filter by source bin
                bin_matches = [
                    result for result in search_results.get('results', [])
                    if result.get('bin_id') == source_bin_id
                ]

                if bin_matches:
                    # Move the best match
                    item_to_move = bin_matches[0]

                    # Update the item's bin_id and description using ChromaDB collection update
                    self.db_client.inventory_collection.update(
                        ids=[item_to_move['id']],
                        metadatas=[{
                            **item_to_move,
                            'bin_id': target_bin_id,
                            'description': f"{item_to_move['name']} in bin {target_bin_id}"
                        }]
                    )
                    success = True

                    if success:
                        moved_items.append(item_to_move['name'])

                        # Create audit log entry
                        audit_entry = {
                            "operation_id": str(uuid.uuid4()),
                            "operation_type": "move",
                            "item_id": item_to_move['id'],
                            "item_name": item_to_move['name'],
                            "source_bin_id": source_bin_id,
                            "target_bin_id": target_bin_id,
                            "description": f"Moved '{item_to_move['name']}' from bin {source_bin_id} to bin {target_bin_id}",
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {
                                "original_query": item,
                                "relevance_score": item_to_move.get("relevance_score", 0.0)
                            }
                        }
                        self.db_client.add_audit_log_entry(audit_entry)
                    else:
                        not_found_items.append(item)
                else:
                    not_found_items.append(item)

            # Prepare result
            if moved_items:
                if not_found_items:
                    message = f"Moved {', '.join(moved_items)} from bin {source_bin_id} to bin {target_bin_id}. Could not find: {', '.join(not_found_items)}"
                else:
                    message = f"Successfully moved {', '.join(moved_items)} from bin {source_bin_id} to bin {target_bin_id}"

                result_data = {
                    "moved_items": moved_items,
                    "not_found_items": not_found_items,
                    "source_bin_id": source_bin_id,
                    "target_bin_id": target_bin_id,
                    "success": True,
                    "message": message
                }

                return FunctionCallResult(
                    success=True,
                    data=result_data,
                    function_name="move_items_between_bins",
                    parameters=parameters
                )
            else:
                return FunctionCallResult(
                    success=False,
                    error=f"Could not find any of the specified items ({', '.join(items)}) in bin {source_bin_id}",
                    function_name="move_items_between_bins",
                    parameters=parameters
                )

        except Exception as e:
            logger.error(f"Error in move_items function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error moving items: {str(e)}",
                function_name="move_items_between_bins",
                parameters=parameters
            )
    
    async def _handle_search_items(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle search_for_items function call"""
        query = parameters.get("query")
        max_results = parameters.get("max_results", 10)

        if not query:
            return FunctionCallResult(
                success=False,
                error="Missing required parameter: query",
                function_name="search_for_items",
                parameters=parameters
            )

        try:
            results = self.db_client.search_documents(
                query=query,
                limit=max_results,
                min_relevance=0.6
            )

            result_data = {
                "query": query,
                "items": results.get('results', []),
                "success": True
            }

            return FunctionCallResult(
                success=True,
                data=result_data,
                function_name="search_for_items",
                parameters=parameters
            )

        except Exception as e:
            logger.error(f"Error in search_items function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error searching items: {str(e)}",
                function_name="search_for_items",
                parameters=parameters
            )
    
    async def _handle_list_bin(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle list_bin_contents function call"""
        bin_id = parameters.get("bin_id")

        if not bin_id:
            return FunctionCallResult(
                success=False,
                error="Missing required parameter: bin_id",
                function_name="list_bin_contents",
                parameters=parameters
            )

        try:
            # Search for all items in the specified bin
            all_results = self.db_client.inventory_collection.get(include=['metadatas'])

            bin_items = [
                metadata for metadata in all_results.get('metadatas', [])
                if metadata.get('bin_id') == bin_id
            ]

            result_data = {
                "bin_id": bin_id,
                "items": bin_items,
                "success": True
            }

            return FunctionCallResult(
                success=True,
                data=result_data,
                function_name="list_bin_contents",
                parameters=parameters
            )

        except Exception as e:
            logger.error(f"Error in list_bin function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error listing bin contents: {str(e)}",
                function_name="list_bin_contents",
                parameters=parameters
            )

    def format_function_result_for_user(self, result: FunctionCallResult) -> str:
        """
        Format a function call result into a user-friendly message.
        
        Args:
            result: The function call result to format
            
        Returns:
            User-friendly message string
        """
        if not result.success:
            return f"❌ Error: {result.error}"
        
        if not result.data:
            return "✅ Operation completed successfully"
        
        # Format based on function type
        if result.function_name == "add_items_to_bin":
            items = result.parameters.get("items", [])
            bin_id = result.parameters.get("bin_id")
            items_str = ", ".join(items)
            return f"✅ Added {items_str} to bin {bin_id}"
        
        elif result.function_name == "remove_items_from_bin":
            items = result.parameters.get("items", [])
            bin_id = result.parameters.get("bin_id")
            items_str = ", ".join(items)
            return f"✅ Removed {items_str} from bin {bin_id}"
        
        elif result.function_name == "move_items_between_bins":
            items = result.parameters.get("items", [])
            source_bin = result.parameters.get("source_bin_id")
            target_bin = result.parameters.get("target_bin_id")
            items_str = ", ".join(items)
            return f"✅ Moved {items_str} from bin {source_bin} to bin {target_bin}"
        
        elif result.function_name == "search_for_items":
            query = result.parameters.get("query")
            items = result.data.get("items", [])
            if not items:
                return f"🔍 No items found matching '{query}'"
            
            items_list = []
            for item in items[:10]:  # Limit to 10 results
                bin_info = f"bin {item.get('bin_id', 'unknown')}"
                items_list.append(f"• {item.get('name', 'Unknown')} (in {bin_info})")
            
            return f"🔍 Found {len(items)} items matching '{query}':\n" + "\n".join(items_list)
        
        elif result.function_name == "list_bin_contents":
            bin_id = result.parameters.get("bin_id")
            items = result.data.get("items", [])
            
            if not items:
                return f"📦 Bin {bin_id} is empty"
            
            items_list = [f"• {item.get('name', 'Unknown')}" for item in items]
            return f"📦 Bin {bin_id} contains {len(items)} items:\n" + "\n".join(items_list)
        
        return "✅ Operation completed successfully"
