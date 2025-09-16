import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import chromadb
from chromadb.config import Settings
from config.embeddings import DEFAULT_EMBEDDING_DIMENSION, get_model_info

logger = logging.getLogger(__name__)



class ChromaDBClient:
    """ChromaDB client for BinBot inventory management"""

    def __init__(self, config: Dict[str, Any], llm_client=None):
        self.config = config
        self.llm_client = llm_client
        self.client: Optional[chromadb.ClientAPI] = None
        self.inventory_collection: Optional[chromadb.Collection] = None
        self.audit_log_collection: Optional[chromadb.Collection] = None
    
    def initialize(self) -> bool:
        """Initialize ChromaDB client and collections"""
        try:
            # Get database configuration
            db_config = self.config.get("database", {})
            persist_directory = db_config.get("persist_directory", "/app/data/chromadb")

            # Ensure directory exists
            os.makedirs(persist_directory, exist_ok=True)

            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create inventory collection
            collection_name = db_config.get("collection_name", "inventory")
            try:
                self.inventory_collection = self.client.get_collection(name=collection_name)
                logger.debug(f"Found existing inventory collection: {collection_name}")

                # Check if collection has correct embedding dimension
                # Test with a dummy embedding to see if dimensions match
                try:
                    test_embedding = [0.0] * DEFAULT_EMBEDDING_DIMENSION
                    # Try to add a test document to check dimensions
                    self.inventory_collection.add(
                        documents=["dimension_test"],
                        embeddings=[test_embedding],
                        ids=["test_dimension_check"]
                    )
                    # If successful, remove the test document
                    self.inventory_collection.delete(ids=["test_dimension_check"])
                except Exception as dim_error:
                    if "dimension" in str(dim_error).lower():
                        logger.debug(f"Collection has wrong embedding dimension, recreating: {dim_error}")
                        # Delete and recreate collection with correct dimensions
                        self.client.delete_collection(collection_name)
                        self.inventory_collection = self.client.create_collection(
                            name=collection_name,
                            metadata={
                                "description": "BinBot inventory items",
                                "embedding_model_version": self.config.get("llm", {}).get("openai", {}).get("embedding_model", "text-embedding-ada-002"),
                                "created_at": datetime.now().isoformat()
                            }
                        )
                        logger.debug(f"Recreated inventory collection with correct dimensions: {collection_name}")
                    else:
                        raise dim_error

            except Exception:
                # Collection doesn't exist, create it
                self.inventory_collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": "BinBot inventory items",
                        "embedding_model_version": self.config.get("llm", {}).get("openai", {}).get("embedding_model", "text-embedding-ada-002"),
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.debug(f"Created new inventory collection: {collection_name}")

            # Get or create audit log collection
            audit_collection_name = "audit_log"
            try:
                self.audit_log_collection = self.client.get_collection(name=audit_collection_name)
                logger.debug(f"Found existing audit log collection: {audit_collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.audit_log_collection = self.client.create_collection(
                    name=audit_collection_name,
                    metadata={
                        "description": "BinBot audit log entries",
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.debug(f"Created new audit log collection: {audit_collection_name}")

            logger.debug("ChromaDB initialized successfully")
            return True

        except Exception as e:
            logger.debug(f"Failed to initialize ChromaDB: {e}")
            return False
    
    def validate_connection(self) -> bool:
        """Validate database connection"""
        try:
            if self.client is None:
                return False
            
            # Try to list collections to test connection
            collections = self.client.list_collections()
            return len(collections) >= 0  # Should always be true if connection works
        except Exception as e:
            logger.debug(f"Database connection validation error: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = {
                "inventory_count": 0,
                "audit_log_count": 0,
                "collections": []
            }
            
            if self.client:
                collections = self.client.list_collections()
                stats["collections"] = [col.name for col in collections]
                
                if self.inventory_collection:
                    stats["inventory_count"] = self.inventory_collection.count()
                
                if self.audit_log_collection:
                    stats["audit_log_count"] = self.audit_log_collection.count()
            
            return stats
        except Exception as e:
            logger.debug(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def add_document(self, name: str, bin_id: str, description: str, embedding: List[float]) -> str:
        """Add a document to the inventory collection and return the document ID"""
        try:
            if self.inventory_collection is None:
                logger.debug("Inventory collection not initialized")
                return None

            doc_id = str(uuid.uuid4())
            document_text = f"{name} - {description}"

            # Determine embedding model version using centralized config
            model_info = get_model_info(len(embedding))
            embedding_model = model_info["name"]

            metadata = {
                "name": name,
                "bin_id": bin_id,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "embedding_model": embedding_model,
                "images_count": 0,  # Store count instead of list
                "images_json": "",  # Store as comma-separated string
                "primary_image": ""  # Store empty string instead of None
            }

            self.inventory_collection.add(
                documents=[document_text],
                metadatas=[metadata],
                embeddings=[embedding],
                ids=[doc_id]
            )

            logger.debug(f"Added document: {name} (ID: {doc_id})")
            return doc_id

        except Exception as e:
            logger.debug(f"Error adding document: {e}")
            return None

    def add_documents_bulk(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple documents in a single transaction with rollback capability"""
        try:
            if self.inventory_collection is None:
                return {"success": False, "error": "Inventory collection not initialized"}

            # Prepare all data first
            doc_ids = []
            documents = []
            metadatas = []
            embeddings = []
            added_items = []

            for item in items:
                doc_id = str(uuid.uuid4())
                document_text = f"{item['name']} - {item['description']}"

                # Determine embedding model version using centralized config
                model_info = get_model_info(len(item['embedding']))
                embedding_model = model_info["name"]

                # Convert image data to ChromaDB-compatible format
                images_list = item.get('images', [])
                primary_image = item.get('primary_image', None)

                metadata = {
                    "name": item['name'],
                    "bin_id": item['bin_id'],
                    "description": item['description'],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "embedding_model": embedding_model,
                    "images_count": len(images_list),  # Store count instead of list
                    "images_json": ",".join(images_list) if images_list else "",  # Store as comma-separated string
                    "primary_image": primary_image if primary_image else ""  # Store empty string instead of None
                }

                doc_ids.append(doc_id)
                documents.append(document_text)
                metadatas.append(metadata)
                embeddings.append(item['embedding'])
                added_items.append({
                    "id": doc_id,
                    "name": item['name'],
                    "bin_id": item['bin_id'],
                    "description": item['description']
                })

            # Atomic operation - add all documents at once using upsert for better reliability
            self.inventory_collection.upsert(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=doc_ids
            )

            # Force a count operation to ensure data is committed/flushed
            try:
                count = self.inventory_collection.count()
                logger.debug(f"Bulk added {len(doc_ids)} documents (collection now has {count} total items)")
                logger.debug(f"Added document IDs: {doc_ids}")

                # Verify the documents were actually added by trying to retrieve them
                verification_result = self.inventory_collection.get(ids=doc_ids, include=['metadatas'])
                logger.debug(f"Verification: Found {len(verification_result['ids'])} out of {len(doc_ids)} documents")
                if len(verification_result['ids']) != len(doc_ids):
                    logger.debug(f"Missing IDs: {set(doc_ids) - set(verification_result['ids'])}")

            except Exception as e:
                logger.debug(f"Bulk added {len(doc_ids)} documents (count check failed: {e})")
            return {
                "success": True,
                "added_items": added_items,
                "doc_ids": doc_ids
            }

        except Exception as e:
            logger.debug(f"Error in bulk add operation: {e}")
            return {"success": False, "error": str(e)}

    def rollback_bulk_add(self, doc_ids: List[str]) -> bool:
        """Rollback a bulk add operation by removing the specified document IDs"""
        try:
            if self.inventory_collection is None:
                logger.debug("Inventory collection not initialized")
                return False

            if not doc_ids:
                return True  # Nothing to rollback

            # Remove all documents that were added
            self.inventory_collection.delete(ids=doc_ids)
            logger.debug(f"Rolled back {len(doc_ids)} documents")
            return True

        except Exception as e:
            logger.debug(f"Error rolling back bulk add: {e}")
            return False

    def add_audit_log_entry(self, audit_entry: Dict[str, Any]) -> bool:
        """Add an audit log entry"""
        try:
            if self.audit_log_collection is None:
                logger.debug("Audit log collection not initialized")
                return False

            doc_id = audit_entry.get("operation_id", str(uuid.uuid4()))
            document_text = audit_entry.get("description", "Audit log entry")

            # Create a simple embedding for audit log (just zeros)
            embedding = [0.0] * 1536  # Standard OpenAI embedding size

            self.audit_log_collection.add(
                documents=[document_text],
                metadatas=[audit_entry],
                embeddings=[embedding],
                ids=[doc_id]
            )

            logger.debug(f"Added audit log entry: {audit_entry.get('action', 'unknown')}")
            return True

        except Exception as e:
            logger.debug(f"Error adding audit log entry: {e}")
            return False
    
    def search_documents(self, query: str, limit: int = 10, offset: int = 0, min_relevance: float = 0.6, embedding_service=None) -> Dict[str, Any]:
        """Search documents in the inventory collection using semantic similarity"""
        try:
            if self.inventory_collection is None:
                raise Exception("Inventory collection not initialized")

            # Try semantic search first if we have an embedding service
            if embedding_service:
                try:
                    # Generate embedding for the search query
                    query_embedding = embedding_service.generate_embedding(query)

                    if query_embedding:
                        # Perform vector similarity search
                        search_results = self.inventory_collection.query(
                            query_embeddings=[query_embedding],
                            n_results=limit + offset,  # Get more results to handle pagination
                            include=['metadatas', 'documents', 'distances']
                        )

                        if search_results['ids'] and len(search_results['ids'][0]) > 0:
                            matching_items = []

                            # Process results starting from offset
                            ids = search_results['ids'][0]
                            metadatas = search_results['metadatas'][0] if search_results['metadatas'] else []
                            distances = search_results['distances'][0] if search_results['distances'] else []

                            for i in range(len(ids)):
                                if i < offset:
                                    continue  # Skip items before offset
                                if len(matching_items) >= limit:
                                    break  # Stop when we have enough results

                                metadata = metadatas[i] if i < len(metadatas) else {}
                                distance = distances[i] if i < len(distances) else 1.0

                                # Convert distance to relevance score (lower distance = higher relevance)
                                relevance_score = max(0.0, 1.0 - distance)

                                # Filter by minimum relevance score
                                if relevance_score >= min_relevance:
                                    # Parse images from ChromaDB format
                                    images_json = metadata.get('images_json', '')
                                    images = images_json.split(',') if images_json else []
                                    images = [img.strip() for img in images if img.strip()]  # Clean up

                                    matching_items.append({
                                        "id": ids[i],
                                        "name": metadata.get('name', ''),
                                        "description": metadata.get('description', ''),
                                        "bin_id": metadata.get('bin_id', ''),
                                        "created_at": metadata.get('created_at', ''),
                                        "relevance_score": relevance_score,
                                        "images": images,
                                        "primary_image": metadata.get('primary_image', ''),
                                        "images_count": len(images)
                                    })

                            total_results = len(ids)
                            has_more = offset + limit < total_results

                            return {
                                "total_results": total_results,
                                "results": matching_items,
                                "has_more": has_more
                            }

                except Exception as e:
                    logger.debug(f"Semantic search failed: {e}")
                    raise e
            else:
                raise Exception("Embedding service is required for search functionality")

        except Exception as e:
            logger.debug(f"Error searching documents: {e}")
            raise e

    def remove_document(self, document_id: str) -> bool:
        """Remove a document from the inventory collection"""
        try:
            if self.inventory_collection is None:
                logger.debug("Inventory collection not initialized")
                return False

            # Remove the document by ID
            self.inventory_collection.delete(ids=[document_id])
            logger.debug(f"Successfully removed document: {document_id}")
            return True

        except Exception as e:
            logger.debug(f"Error removing document {document_id}: {e}")
            return False

    def update_document_metadata(self, document_id: str, metadata_updates: dict) -> bool:
        """Update metadata for a specific document"""
        try:
            if self.inventory_collection is None:
                logger.debug("Inventory collection not initialized")
                return False

            # Get the current document with embeddings
            result = self.inventory_collection.get(ids=[document_id], include=["metadatas", "documents", "embeddings"])

            if not result["ids"] or len(result["ids"]) == 0:
                logger.debug(f"Document {document_id} not found")
                return False

            # Get current metadata, document, and embedding
            current_metadata = result["metadatas"][0] if result["metadatas"] else {}
            current_document = result["documents"][0] if result["documents"] else ""
            current_embedding = result["embeddings"][0] if result["embeddings"] else None

            # Update metadata with new values
            updated_metadata = {**current_metadata, **metadata_updates}

            # Update the document (ChromaDB requires re-adding with same ID to update)
            # Must include the original embedding to avoid dimension mismatch
            self.inventory_collection.upsert(
                ids=[document_id],
                documents=[current_document],
                metadatas=[updated_metadata],
                embeddings=[current_embedding] if current_embedding else None
            )

            logger.debug(f"Successfully updated metadata for document: {document_id}")
            return True

        except Exception as e:
            logger.debug(f"Error updating document metadata {document_id}: {e}")
            return False

    def add_image_to_item(self, item_id: str, image_id: str, set_as_primary: bool = False) -> bool:
        """Add an image ID to an item's image list"""
        try:
            # Get current item data
            result = self.inventory_collection.get(
                ids=[item_id],
                include=['metadatas']
            )

            if not result['ids'] or len(result['ids']) == 0:
                logger.debug(f"Item {item_id} not found")
                return False

            current_metadata = result['metadatas'][0]

            # Parse current images from ChromaDB format
            images_json = current_metadata.get('images_json', '')
            images = images_json.split(',') if images_json else []
            images = [img.strip() for img in images if img.strip()]  # Clean up

            # Add image ID if not already present
            if image_id not in images:
                images.append(image_id)

            # Set as primary image if requested or if it's the first image
            primary_image = current_metadata.get('primary_image', '')
            if set_as_primary or not primary_image:
                primary_image = image_id

            # Update metadata in ChromaDB-compatible format
            updates = {
                'images_count': len(images),
                'images_json': ','.join(images),
                'primary_image': primary_image,
                'updated_at': datetime.now().isoformat()
            }

            logger.debug(f"chromadb_client: Adding image {image_id} to item {item_id}")

            return self.update_document_metadata(item_id, updates)

        except Exception as e:
            logger.debug(f"Error adding image {image_id} to item {item_id}: {e}")
            return False

    def remove_image_from_item(self, item_id: str, image_id: str) -> bool:
        """Remove an image ID from an item's image list"""
        try:
            # Get current item data
            result = self.inventory_collection.get(
                ids=[item_id],
                include=['metadatas']
            )

            if not result['ids'] or len(result['ids']) == 0:
                logger.debug(f"Item {item_id} not found")
                return False

            current_metadata = result['metadatas'][0]

            # Parse current images from ChromaDB format
            images_json = current_metadata.get('images_json', '')
            images = images_json.split(',') if images_json else []
            images = [img.strip() for img in images if img.strip()]  # Clean up

            primary_image = current_metadata.get('primary_image', '')

            # Remove image ID if present
            if image_id in images:
                images.remove(image_id)

            # Update primary image if it was the removed image
            if primary_image == image_id:
                primary_image = images[0] if images else ""

            # Update metadata in ChromaDB-compatible format
            updates = {
                'images_count': len(images),
                'images_json': ','.join(images),
                'primary_image': primary_image,
                'updated_at': datetime.now().isoformat()
            }

            return self.update_document_metadata(item_id, updates)

        except Exception as e:
            logger.debug(f"Error removing image {image_id} from item {item_id}: {e}")
            return False

    def get_items_with_images(self) -> List[Dict[str, Any]]:
        """Get all items that have associated images"""
        try:
            if self.inventory_collection is None:
                return []

            # Get all items
            all_results = self.inventory_collection.get(
                include=['metadatas']
            )

            items_with_images = []
            for i, item_id in enumerate(all_results['ids']):
                metadata = all_results['metadatas'][i]

                # Parse images from ChromaDB format
                images_json = metadata.get('images_json', '')
                images = images_json.split(',') if images_json else []
                images = [img.strip() for img in images if img.strip()]  # Clean up

                if images:  # Item has images
                    items_with_images.append({
                        'item_id': item_id,
                        'name': metadata.get('name', ''),
                        'bin_id': metadata.get('bin_id', ''),
                        'images': images,
                        'primary_image': metadata.get('primary_image', '')
                    })

            return items_with_images

        except Exception as e:
            logger.debug(f"Error getting items with images: {e}")
            return []
