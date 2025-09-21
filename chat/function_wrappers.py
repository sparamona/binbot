"""
Simple function wrappers for LLM function calling
"""

import logging
from typing import List, Dict, Any, Union

from api.inventory import (
    add_items_logic, remove_items_logic, move_items_logic,
    search_items_logic, get_bin_contents_logic
)
from api_schemas import ItemInput
from session.session_manager import get_session_manager

# Set up logger for function wrappers
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class InventoryFunctionWrappers:
    """Simple function wrappers for inventory operations"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_manager = get_session_manager()
    
    def add_items(self, bin_id: str, items: List[Dict[str, str]]) -> Dict[str, Any]:
        """Add items to a bin.

        Args:
            bin_id (str): ID of the bin to add items to (e.g. '3', 'A3', 'B5', 'TOOLS', '12')
            items (List[Dict[str, str]]): List of item dictionaries, each containing:
                - name (str): Name of the item (required)
                - description (str, optional): Optional description of the item
                - image_id (str, optional): Optional ID of associated image

        Returns:
            Dict[str, Any]: Response object containing:
                - success (bool): True if operation succeeded, False otherwise
                - message (str): Human-readable message describing the result

        Example:
            >>> add_items("3", [{"name": "screwdriver", "description": "Phillips head screwdriver"}])
            {"success": True, "message": "Successfully added 1 items to bin 3"}
        """
        logger.info(f"CALL add_items(bin_id='{bin_id}', items={items})")
        try:
            # Convert dict items to ItemInput objects
            item_inputs = []
            for item in items:
                item_input = ItemInput(
                    name=item['name'],
                    description=item.get('description', ''),
                    image_id=item.get('image_id', '')
                )
                item_inputs.append(item_input)

            # Use business logic function
            response = add_items_logic(bin_id, item_inputs)

            # Update session current bin
            self.session_manager.set_current_bin(self.session_id, bin_id)

            logger.info(f"RESULT add_items: {response.message}")
            return response.model_dump()

        except Exception as e:
            error_result = f"Error adding items: {str(e)}"
            logger.error(f"RESULT add_items: {error_result}")
            return {"success": False, "message": error_result}
    
    def search_items(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for items in inventory using semantic search.

        Args:
            query (str): Search query string to find matching items (e.g. "red tools", "electronics")
            limit (int, optional): Maximum number of results to return. Defaults to 10.

        Returns:
            Dict[str, Any]: Response object containing:
                - success (bool): True if search completed successfully
                - items (List[Dict]): List of matching items, each containing:
                    - id (str): Unique item identifier
                    - name (str): Item name
                    - description (str): Item description
                    - bin_id (str): ID of bin containing the item
                    - created_at (str): ISO timestamp when item was added
                    - image_id (str): Associated image ID if available
                    - confidence_score (float): Search relevance score (0.0-1.0)
                - current_bin (str): Empty string for search results

        Example:
            >>> search_items("screwdriver", 5)
            {"success": True, "items": [{"id": "123", "name": "Phillips screwdriver", "bin_id": "A3", ...}], "current_bin": ""}
        """
        logger.info(f"CALL search_items(query='{query}', limit={limit})")
        try:
            # Use business logic function
            response = search_items_logic(query, limit)

            logger.info(f"RESULT search_items: Found {len(response.items)} items")
            return response.model_dump()

        except Exception as e:
            error_result = f"Error searching items: {str(e)}"
            logger.error(f"RESULT search_items: {error_result}")
            return {"success": False, "items": [], "current_bin": ""}
    
    def get_bin_contents(self, bin_id: str) -> Dict[str, Any]:
        """Get all items in a specific storage bin.

        Args:
            bin_id (str): ID of the bin to retrieve contents from (e.g. '3', 'A3', 'B5', 'TOOLS', '12')

        Returns:
            Dict[str, Any]: Response object containing:
                - success (bool): True if operation completed successfully
                - bin_id (str): ID of the requested bin
                - items (List[Dict]): List of items in the bin, each containing:
                    - id (str): Unique item identifier
                    - name (str): Item name
                    - description (str): Item description
                    - bin_id (str): ID of bin containing the item
                    - created_at (str): ISO timestamp when item was added
                    - image_id (str): Associated image ID if available
                - total_count (int): Total number of items in the bin

        Example:
            >>> get_bin_contents("3")
            {"success": True, "bin_id": "3", "items": [{"id": "123", "name": "screwdriver", ...}], "total_count": 1}
        """
        logger.info(f"CALL get_bin_contents(bin_id='{bin_id}')")
        try:
            # Use business logic function
            response = get_bin_contents_logic(bin_id)

            # Update session current bin
            self.session_manager.set_current_bin(self.session_id, bin_id)

            item_names = [item.name for item in response.items]
            logger.info(f"RESULT get_bin_contents: Found {len(response.items)} items in bin {bin_id}: {item_names}")
            return response.model_dump()

        except Exception as e:
            error_result = f"Error getting bin contents: {str(e)}"
            logger.error(f"RESULT get_bin_contents: {error_result}")
            return {"success": False, "bin_id": bin_id, "items": [], "total_count": 0}
    
    def move_items(self, target_bin_id: str, item_ids: List[str]) -> Dict[str, Any]:
        """Move items from their current bins to a target bin.

        Args:
            target_bin_id (str): ID of the destination bin (e.g. '3', 'A3', 'B5', 'TOOLS', '12')
            item_ids (List[str]): List of item IDs to move

        Returns:
            Dict[str, Any]: Response object containing:
                - success (bool): True if operation succeeded, False otherwise
                - message (str): Human-readable message describing the result

        Example:
            >>> move_items("5", ["item-123", "item-456"])
            {"success": True, "message": "Successfully moved 2 items to bin 5"}
        """
        logger.info(f"CALL move_items(target_bin_id='{target_bin_id}', item_ids={item_ids})")
        try:
            # Use business logic function
            response = move_items_logic(item_ids, target_bin_id)

            # Update session current bin
            self.session_manager.set_current_bin(self.session_id, target_bin_id)

            logger.info(f"RESULT move_items: {response.message}")
            return response.model_dump()

        except Exception as e:
            error_result = f"Error moving items: {str(e)}"
            logger.error(f"RESULT move_items: {error_result}")
            return {"success": False, "message": error_result}
    
    def remove_items(self, item_ids: List[str]) -> Dict[str, Any]:
        """Remove items completely from the inventory system.

        Args:
            item_ids (List[str]): List of item IDs to remove from inventory

        Returns:
            Dict[str, Any]: Response object containing:
                - success (bool): True if operation succeeded, False otherwise
                - message (str): Human-readable message describing the result

        Example:
            >>> remove_items(["item-123", "item-456"])
            {"success": True, "message": "Successfully removed 2 items"}
        """
        logger.info(f"CALL remove_items(item_ids={item_ids})")
        try:
            # Use business logic function
            response = remove_items_logic(item_ids)

            logger.info(f"RESULT remove_items: {response.message}")
            return response.model_dump()

        except Exception as e:
            error_result = f"Error removing items: {str(e)}"
            logger.error(f"RESULT remove_items: {error_result}")
            return {"success": False, "message": error_result}


def get_function_wrappers(session_id: str) -> InventoryFunctionWrappers:
    """Get function wrappers for a session"""
    return InventoryFunctionWrappers(session_id)


def create_function_mapping(wrappers: InventoryFunctionWrappers) -> Dict[str, callable]:
    """Create mapping from function names to wrapper methods"""
    return {
        "add_items": wrappers.add_items,
        "search_items": wrappers.search_items,
        "get_bin_contents": wrappers.get_bin_contents,
        "move_items": wrappers.move_items,
        "remove_items": wrappers.remove_items
    }
