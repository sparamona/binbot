"""
Simple function wrappers for LLM function calling
"""

from typing import List, Dict, Any
from datetime import datetime

from database.chromadb_client import get_chromadb_client
from llm.embeddings import get_embedding_service
from session.session_manager import get_session_manager


class InventoryFunctionWrappers:
    """Simple function wrappers for inventory operations"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db_client = get_chromadb_client()
        self.embedding_service = get_embedding_service()
        self.session_manager = get_session_manager()
    
    def add_items(self, bin_id: str, items: List[Dict[str, str]]) -> str:
        """Add items to a bin"""
        try:
            # Generate embeddings for items
            item_texts = []
            for item in items:
                text = f"{item['name']} {item.get('description', '')}"
                item_texts.append(text)

            embeddings = self.embedding_service.batch_generate_embeddings(item_texts)

            # Prepare documents for ChromaDB (with id and embedding fields)
            documents = []
            for i, item in enumerate(items):
                doc = {
                    'id': str(__import__('uuid').uuid4()),  # Generate unique ID
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'bin_id': bin_id,
                    'created_at': datetime.now().isoformat(),
                    'image_id': '',
                    'embedding': embeddings[i]  # Include embedding in document
                }
                documents.append(doc)

            # Add to database
            self.db_client.add_documents_bulk(documents)

            # Update session current bin
            self.session_manager.set_current_bin(self.session_id, bin_id)

            return f"Successfully added {len(items)} items to bin {bin_id}"

        except Exception as e:
            return f"Error adding items: {str(e)}"
    
    def search_items(self, query: str, limit: int = 10) -> str:
        """Search for items in inventory"""
        try:
            results = self.db_client.search_documents(query, limit)
            
            if not results:
                return f"No items found matching '{query}'"
            
            response = f"Found {len(results)} items matching '{query}':\n"
            for item in results:
                response += f"- {item['name']} in bin {item['bin_id']}"
                if item.get('description'):
                    response += f": {item['description']}"
                response += "\n"
            
            return response
            
        except Exception as e:
            return f"Error searching items: {str(e)}"
    
    def get_bin_contents(self, bin_id: str) -> str:
        """Get contents of a specific bin"""
        try:
            items = self.db_client.get_bin_contents(bin_id)
            
            if not items:
                return f"Bin {bin_id} is empty"
            
            # Update session current bin
            self.session_manager.set_current_bin(self.session_id, bin_id)
            
            response = f"Bin {bin_id} contains {len(items)} items:\n"
            for item in items:
                response += f"- {item['name']}"
                if item.get('description'):
                    response += f": {item['description']}"
                response += "\n"
            
            return response
            
        except Exception as e:
            return f"Error getting bin contents: {str(e)}"
    
    def move_items(self, target_bin_id: str, item_ids: List[str]) -> str:
        """Move items to a different bin"""
        try:
            moved_count = 0
            failed_items = []
            
            for item_id in item_ids:
                success = self.db_client.update_item_bin(item_id, target_bin_id)
                if success:
                    moved_count += 1
                else:
                    failed_items.append(item_id)
            
            # Update session current bin
            self.session_manager.set_current_bin(self.session_id, target_bin_id)
            
            response = f"Moved {moved_count} items to bin {target_bin_id}"
            if failed_items:
                response += f". Failed to move {len(failed_items)} items"
            
            return response
            
        except Exception as e:
            return f"Error moving items: {str(e)}"
    
    def remove_items(self, item_ids: List[str]) -> str:
        """Remove items from inventory"""
        try:
            removed_count = 0
            failed_items = []
            
            for item_id in item_ids:
                success = self.db_client.remove_document(item_id)
                if success:
                    removed_count += 1
                else:
                    failed_items.append(item_id)
            
            response = f"Removed {removed_count} items from inventory"
            if failed_items:
                response += f". Failed to remove {len(failed_items)} items"
            
            return response
            
        except Exception as e:
            return f"Error removing items: {str(e)}"


def get_function_wrappers(session_id: str) -> InventoryFunctionWrappers:
    """Get function wrappers for a session"""
    return InventoryFunctionWrappers(session_id)
