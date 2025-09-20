"""
ChromaDB Client for BinBot

Simple vector storage and search for inventory items.
"""

from typing import List, Dict, Any
from pathlib import Path

import chromadb
from config.settings import DATABASE_PATH, STORAGE_MODE
from config.embeddings import EMBEDDING_DIMENSION


class ChromaDBClient:
    """Simple ChromaDB client for inventory management"""

    def __init__(self):
        self._client = None
        self._collection = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        if STORAGE_MODE == 'memory':
            # In-memory client for testing
            self._client = chromadb.Client()
        else:
            # Persistent client for production
            db_path = Path(DATABASE_PATH)
            db_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(db_path))

        self._collection = self._client.get_or_create_collection(
            name="inventory",
            metadata={"hnsw:space": "cosine", "dimension": EMBEDDING_DIMENSION}
        )

    @property
    def inventory_collection(self):
        """Access to inventory collection"""
        return self._collection
    
    def add_documents_bulk(self, items: List[Dict[str, Any]]):
        """Add multiple items to the inventory with embeddings"""
        if not items:
            return

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for item in items:
            ids.append(item['id'])
            embeddings.append(item['embedding'])

            # Create searchable document text
            doc_text = item['name']
            if item.get('description'):
                doc_text += f" {item['description']}"
            documents.append(doc_text)

            # Simple metadata
            metadata = {
                'name': item['name'],
                'description': item.get('description', ''),
                'bin_id': item['bin_id'],
                'created_at': item['created_at'],
                'image_id': item.get('image_id', '')  # Single image per item
            }
            metadatas.append(metadata)

        # Add to ChromaDB
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
    
    def search_documents(self, query: str, limit: int = 10, max_distance: float = 0.7):
        """Search for items using vector similarity with distance filtering"""
        # Generate embedding for query using our embedding service
        from llm.embeddings import get_embedding_service
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_embedding(query)

        # Get more results than needed to allow for distance filtering
        search_limit = min(limit * 3, 50)  # Search more, filter down
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=search_limit
        )

        items = []
        if results['ids'] and results['ids'][0]:
            for i, item_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]

                # Filter by distance threshold
                if distance > max_distance:
                    continue

                item = {
                    'id': item_id,
                    'name': metadata['name'],
                    'description': metadata.get('description', ''),
                    'bin_id': metadata['bin_id'],
                    'created_at': metadata['created_at'],
                    'image_id': metadata.get('image_id', ''),
                    'confidence_score': round(1.0 - distance, 3),
                    'distance': distance
                }
                items.append(item)

                # Stop when we have enough results
                if len(items) >= limit:
                    break

        return items
    
    def remove_document(self, item_id: str):
        """Remove an item by ID"""
        self._collection.delete(ids=[item_id])
    
    def update_item_bin(self, item_id: str, new_bin_id: str):
        """Update an item's bin location"""
        existing = self._collection.get(ids=[item_id])
        if existing['ids']:
            metadata = existing['metadatas'][0]
            metadata['bin_id'] = new_bin_id
            self._collection.update(ids=[item_id], metadatas=[metadata])
    
    def get_bin_contents(self, bin_id: str):
        """Get all items in a specific bin"""
        results = self._collection.get(where={"bin_id": bin_id})

        items = []
        if results['ids']:
            for i, item_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                item = {
                    'id': item_id,
                    'name': metadata['name'],
                    'description': metadata.get('description', ''),
                    'bin_id': metadata['bin_id'],
                    'created_at': metadata['created_at'],
                    'image_id': metadata.get('image_id', '')
                }
                items.append(item)

        return items

    def add_image_to_item(self, item_id: str, image_id: str):
        """Associate an image with an item"""
        existing = self._collection.get(ids=[item_id])
        if existing['ids']:
            metadata = existing['metadatas'][0]
            metadata['image_id'] = image_id
            self._collection.update(ids=[item_id], metadatas=[metadata])

    def add_audit_log_entry(self, entry: Dict[str, Any]):
        """Add an audit log entry (simplified - just pass for now)"""
        # TODO: Implement audit logging if needed
        pass


# Global client instance
_chromadb_client = None


def get_chromadb_client() -> ChromaDBClient:
    """Get the global ChromaDB client"""
    global _chromadb_client
    if _chromadb_client is None:
        _chromadb_client = ChromaDBClient()
    return _chromadb_client
