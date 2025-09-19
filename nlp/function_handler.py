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
    from_image_context: bool = False

class FunctionCallHandler:
    """Handles execution of OpenAI function calls for inventory operations"""

    def __init__(self, db_client, embedding_service, vision_service=None, image_storage=None):
        self.db_client = db_client
        self.embedding_service = embedding_service
        self.vision_service = vision_service
        self.image_storage = image_storage
        self.supported_functions = set(get_all_function_names())
    
    async def execute_function_call(self, function_name: str, parameters: Dict[str, Any], session_id: Optional[str] = None) -> FunctionCallResult:
        """
        Execute a function call with the given parameters.

        Args:
            function_name: Name of the function to execute
            parameters: Parameters for the function call
            session_id: Optional session ID for accessing conversation context

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
                return await self._handle_add_items(parameters, session_id)
            elif function_name == "remove_items_from_bin":
                return await self._handle_remove_items(parameters)
            elif function_name == "move_items_between_bins":
                return await self._handle_move_items(parameters)
            elif function_name == "search_for_items":
                return await self._handle_search_items(parameters)

            elif function_name == "list_bin_contents":
                return await self._handle_list_bin(parameters)
            elif function_name == "add_items_from_image":
                return await self._handle_add_items_from_image(parameters, session_id)
            elif function_name == "analyze_image":
                return await self._handle_analyze_image(parameters)
            elif function_name == "search_by_image":
                return await self._handle_search_by_image(parameters)
            elif function_name == "describe_image":
                return await self._handle_describe_image(parameters)
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
    
    async def _handle_add_items(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> FunctionCallResult:
        """Handle add_items_to_bin function call"""
        items = parameters.get("items", [])
        bin_id = parameters.get("bin_id")
        image_id = parameters.get("image_id")

        if not items or not bin_id:
            return FunctionCallResult(
                success=False,
                error="Missing required parameters: items and bin_id",
                function_name="add_items_to_bin",
                parameters=parameters
            )

        try:
            # Get vision analysis data from conversation context if image_id is provided
            vision_items_map = {}
            if image_id and session_id:
                vision_items_map = self._get_vision_items_from_conversation(session_id, image_id)
                logger.info(f"Retrieved vision analysis for {len(vision_items_map)} items from conversation context")

            # Prepare items with embeddings (like the real add API does)
            prepared_items = []
            failed_items = []
            added_items = []

            # First pass: validate and prepare all items with embeddings
            for item_name in items:
                item_name = item_name.strip()
                if not item_name:
                    failed_items.append({
                        "name": item_name,
                        "error": "Empty item name"
                    })
                    continue

                # Use vision analysis description if available, otherwise create generic description
                if item_name in vision_items_map:
                    description = vision_items_map[item_name]["description"]
                    logger.info(f"Using vision analysis description for '{item_name}': {description[:100]}...")
                else:
                    description = f"{item_name} in bin {bin_id}"
                    logger.info(f"Using generic description for '{item_name}': {description}")

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
                        added_items = bulk_result["added_items"]  # Use items with actual database IDs
                        for item in added_items:
                            logger.info(f"Added item '{item['name']}' to bin {bin_id}")

                        # Associate image with created items if image_id parameter is provided
                        image_id_to_use = parameters.get('image_id')

                        if image_id_to_use and self.image_storage:
                            await self._associate_image_with_items(image_id_to_use, added_items, bin_id)
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

            # Add current_bin to result data
            result_data["current_bin"] = bin_id

            return FunctionCallResult(
                success=success,
                data=result_data,
                function_name="add_items_to_bin",
                parameters=parameters,
                from_image_context=bool(parameters.get('image_id'))
            )

        except Exception as e:
            logger.error(f"Error in add_items function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error adding items: {str(e)}",
                function_name="add_items_to_bin",
                parameters=parameters,
                from_image_context=bool(parameters.get('image_id'))
            )

    async def _associate_image_with_items(self, image_id: str, added_items: List[Dict], bin_id: str):
        """Associate an image with newly created items"""
        try:
            logger.info(f"Attempting to associate image {image_id} with {len(added_items)} items")

            # For each created item, associate the image and set as primary
            for item in added_items:
                item_id = item['id']
                logger.info(f"Processing item {item_id} for image association")

                # Update image metadata to associate with this item
                # For the first item, update the image metadata to point to it
                if item == added_items[0]:  # Use first item as the primary association
                    logger.info(f"Updating image metadata for primary item {item_id}")
                    self.image_storage.update_image_metadata(image_id, {
                        'item_id': item_id,
                        'bin_id': bin_id
                    })

                # Associate image with item in database (includes retry mechanism)
                logger.info(f"Calling add_image_to_item for item {item_id}")
                success = self.db_client.add_image_to_item(
                    item_id=item_id,
                    image_id=image_id,
                    set_as_primary=True
                )

                if success:
                    logger.info(f"Successfully associated image {image_id} with item {item_id}")
                else:
                    logger.warning(f"Failed to associate image {image_id} with item {item_id}")

        except Exception as e:
            logger.error(f"Error associating image {image_id} with items: {e}")

    def _get_vision_items_from_conversation(self, session_id: str, image_id: str) -> Dict[str, Dict[str, str]]:
        """Extract vision analysis items from conversation context for a specific image"""
        try:
            # Import here to avoid circular imports
            from nlp.conversation_manager import conversation_manager
            import json

            # Get conversation history
            conversation = conversation_manager.get_conversation(session_id)

            # Look for system messages containing vision analysis data for this image_id
            vision_items = {}
            for message in conversation.messages:
                if (message.role == "system" and
                    message.content.startswith("VISION_ANALYSIS:")):

                    try:
                        # Parse the JSON data from the vision analysis message
                        json_data = message.content[len("VISION_ANALYSIS:"):]
                        vision_data = json.loads(json_data)

                        # Check if this is for the correct image
                        if vision_data.get("image_id") == image_id:
                            logger.info(f"Found vision analysis data for image {image_id}")

                            # Create a map of item names to their detailed descriptions
                            for item in vision_data.get("items", []):
                                item_name = item.get("name", "")
                                item_description = item.get("description", "")
                                if item_name and item_description:
                                    vision_items[item_name] = {
                                        "description": item_description,
                                        "confidence": item.get("confidence", 0.0)
                                    }

                            logger.info(f"Extracted {len(vision_items)} vision items: {list(vision_items.keys())}")
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse vision analysis JSON: {e}")
                        continue

            return vision_items

        except Exception as e:
            logger.error(f"Error extracting vision items from conversation: {e}")
            return {}

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
                    min_relevance=0.6,
                    embedding_service=self.embedding_service
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

                # Add current_bin to result data
                result_data["current_bin"] = bin_id

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
                    min_relevance=0.6,
                    embedding_service=self.embedding_service
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
                    # Only include simple metadata types (str, int, float, bool)
                    metadata = {
                        'name': item_to_move['name'],
                        'description': f"{item_to_move['name']} in bin {target_bin_id}",
                        'bin_id': target_bin_id,
                        'created_at': item_to_move.get('created_at', ''),
                        'embedding_model': item_to_move.get('embedding_model', 'openai')
                    }

                    self.db_client.inventory_collection.update(
                        ids=[item_to_move['id']],
                        metadatas=[metadata]
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

                # Add current_bin to result data (target bin for move operations)
                result_data["current_bin"] = target_bin_id

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
                min_relevance=0.6,
                embedding_service=self.embedding_service
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

            # Add current_bin to result data
            result_data["current_bin"] = bin_id

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

    async def _handle_add_items_from_image(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> FunctionCallResult:
        """Handle adding items from image analysis using current image context"""
        # This function is deprecated - image context now flows through conversation
        # The LLM should use add_items_to_bin directly with image_id when appropriate
        return FunctionCallResult(
            success=False,
            error="This function is deprecated. Use add_items_to_bin with image_id parameter instead.",
            function_name="add_items_from_image",
            parameters=parameters
        )

    async def _handle_analyze_image(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle image analysis using Vision API"""
        try:
            if not self.vision_service:
                return FunctionCallResult(
                    success=False,
                    error="Vision service not available",
                    function_name="analyze_image",
                    parameters=parameters
                )

            image_id = parameters.get("image_id")
            context = parameters.get("context")

            if not image_id:
                return FunctionCallResult(
                    success=False,
                    error="Image ID is required",
                    function_name="analyze_image",
                    parameters=parameters
                )

            # Get image path from storage
            from storage.image_storage import ImageStorage
            image_storage = ImageStorage()
            image_path = image_storage.get_image_path(image_id, "full")

            if not image_path:
                return FunctionCallResult(
                    success=False,
                    error=f"Image {image_id} not found",
                    function_name="analyze_image",
                    parameters=parameters
                )

            # Analyze image
            analysis_result = await self.vision_service.identify_item(image_path, context)

            if not analysis_result.get("success", False):
                return FunctionCallResult(
                    success=False,
                    error=analysis_result.get("error", "Analysis failed"),
                    function_name="analyze_image",
                    parameters=parameters
                )

            return FunctionCallResult(
                success=True,
                data=analysis_result,
                function_name="analyze_image",
                parameters=parameters
            )

        except Exception as e:
            logger.error(f"Error in analyze_image function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error analyzing image: {str(e)}",
                function_name="analyze_image",
                parameters=parameters
            )

    async def _handle_search_by_image(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle search by image using Vision API"""
        try:
            if not self.vision_service:
                return FunctionCallResult(
                    success=False,
                    error="Vision service not available",
                    function_name="search_by_image",
                    parameters=parameters
                )

            image_id = parameters.get("image_id")
            additional_query = parameters.get("additional_query")

            if not image_id:
                return FunctionCallResult(
                    success=False,
                    error="Image ID is required",
                    function_name="search_by_image",
                    parameters=parameters
                )

            # Get image path from storage
            from storage.image_storage import ImageStorage
            image_storage = ImageStorage()
            image_path = image_storage.get_image_path(image_id, "full")

            if not image_path:
                return FunctionCallResult(
                    success=False,
                    error=f"Image {image_id} not found",
                    function_name="search_by_image",
                    parameters=parameters
                )

            # Generate search terms
            search_result = await self.vision_service.search_by_image(image_path, additional_query)

            if not search_result.get("success", False):
                return FunctionCallResult(
                    success=False,
                    error=search_result.get("error", "Search term generation failed"),
                    function_name="search_by_image",
                    parameters=parameters
                )

            # Use the suggested query to search inventory
            suggested_query = search_result.get("suggested_query", "")
            if suggested_query:
                search_params = {"query": suggested_query, "limit": 10}
                inventory_search = await self._handle_search_items(search_params)

                # Combine vision results with inventory search
                result_data = {
                    "vision_analysis": search_result,
                    "inventory_search": inventory_search.data if inventory_search.success else None,
                    "suggested_query": suggested_query
                }
            else:
                result_data = {"vision_analysis": search_result}

            return FunctionCallResult(
                success=True,
                data=result_data,
                function_name="search_by_image",
                parameters=parameters
            )

        except Exception as e:
            logger.error(f"Error in search_by_image function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error searching by image: {str(e)}",
                function_name="search_by_image",
                parameters=parameters
            )

    async def _handle_describe_image(self, parameters: Dict[str, Any]) -> FunctionCallResult:
        """Handle image description for accessibility"""
        try:
            if not self.vision_service:
                return FunctionCallResult(
                    success=False,
                    error="Vision service not available",
                    function_name="describe_image",
                    parameters=parameters
                )

            image_id = parameters.get("image_id")

            if not image_id:
                return FunctionCallResult(
                    success=False,
                    error="Image ID is required",
                    function_name="describe_image",
                    parameters=parameters
                )

            # Get image path from storage
            from storage.image_storage import ImageStorage
            image_storage = ImageStorage()
            image_path = image_storage.get_image_path(image_id, "full")

            if not image_path:
                return FunctionCallResult(
                    success=False,
                    error=f"Image {image_id} not found",
                    function_name="describe_image",
                    parameters=parameters
                )

            # Generate description
            description_result = await self.vision_service.describe_for_accessibility(image_path)

            if not description_result.get("success", False):
                return FunctionCallResult(
                    success=False,
                    error=description_result.get("error", "Description generation failed"),
                    function_name="describe_image",
                    parameters=parameters
                )

            return FunctionCallResult(
                success=True,
                data=description_result,
                function_name="describe_image",
                parameters=parameters
            )

        except Exception as e:
            logger.error(f"Error in describe_image function: {e}")
            return FunctionCallResult(
                success=False,
                error=f"Error describing image: {str(e)}",
                function_name="describe_image",
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
            if result.from_image_context:
                return f"📸 Added items from uploaded image to bin {bin_id}: {items_str}"
            else:
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

        elif result.function_name == "add_items_from_image":
            bin_id = result.parameters.get("bin_id")
            description = result.parameters.get("image_description", "")

            response = f"📷 **Add Items from Image to Bin {bin_id}**\n\n"
            response += result.data.get("message", "")

            if result.data.get("instructions"):
                response += "\n\n**Steps:**\n"
                for instruction in result.data["instructions"]:
                    response += f"{instruction}\n"

            return response

        elif result.function_name == "analyze_image":
            image_id = result.parameters.get("image_id")
            analysis = result.data

            item_name = analysis.get("item_name", "Unknown item")
            description = analysis.get("description", "No description available")
            confidence = analysis.get("confidence", 0)
            category = analysis.get("category", "Unknown")

            response = f"🔍 **Image Analysis Results:**\n"
            response += f"**Item:** {item_name}\n"
            response += f"**Description:** {description}\n"
            response += f"**Category:** {category}\n"
            response += f"**Confidence:** {confidence}/10"

            if analysis.get("characteristics"):
                features = ", ".join(analysis["characteristics"])
                response += f"\n**Features:** {features}"

            return response

        elif result.function_name == "search_by_image":
            image_id = result.parameters.get("image_id")
            vision_analysis = result.data.get("vision_analysis", {})
            inventory_search = result.data.get("inventory_search")
            suggested_query = result.data.get("suggested_query", "")

            response = f"🔍 **Image Search Results:**\n"

            if suggested_query:
                response += f"**Generated search terms:** {suggested_query}\n\n"

            if inventory_search and inventory_search.get("items"):
                items = inventory_search["items"]
                response += f"**Found {len(items)} matching items:**\n"
                for item in items[:5]:  # Show top 5 results
                    response += f"• {item.get('name', 'Unknown')} (Bin {item.get('bin_id', '?')})\n"
                if len(items) > 5:
                    response += f"... and {len(items) - 5} more items\n"
            else:
                response += "**No matching items found in inventory**\n"

            # Add vision analysis details
            if vision_analysis.get("primary_terms"):
                terms = ", ".join(vision_analysis["primary_terms"])
                response += f"\n**AI identified terms:** {terms}"

            return response

        elif result.function_name == "describe_image":
            image_id = result.parameters.get("image_id")
            description = result.data.get("description", "No description available")

            return f"📷 **Image Description:**\n{description}"

        return "✅ Operation completed successfully"
