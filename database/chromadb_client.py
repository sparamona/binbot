import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import chromadb
from chromadb.config import Settings


class ChromaDBClient:
    """ChromaDB client for BinBot inventory management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
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
                print(f"Found existing inventory collection: {collection_name}")

                # Check if collection has correct embedding dimension
                # Test with a dummy embedding to see if dimensions match
                try:
                    test_embedding = [0.0] * 1536  # OpenAI embedding size
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
                        print(f"Collection has wrong embedding dimension, recreating: {dim_error}")
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
                        print(f"Recreated inventory collection with correct dimensions: {collection_name}")
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
                print(f"Created new inventory collection: {collection_name}")

            # Get or create audit log collection
            audit_collection_name = "audit_log"
            try:
                self.audit_log_collection = self.client.get_collection(name=audit_collection_name)
                print(f"Found existing audit log collection: {audit_collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.audit_log_collection = self.client.create_collection(
                    name=audit_collection_name,
                    metadata={
                        "description": "BinBot audit log entries",
                        "created_at": datetime.now().isoformat()
                    }
                )
                print(f"Created new audit log collection: {audit_collection_name}")

            print("ChromaDB initialized successfully")
            return True

        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
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
            print(f"Database connection validation error: {e}")
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
            print(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def add_document(self, name: str, bin_id: str, description: str, embedding: List[float]) -> bool:
        """Add a document to the inventory collection"""
        try:
            if self.inventory_collection is None:
                print("Inventory collection not initialized")
                return False

            doc_id = str(uuid.uuid4())
            document_text = f"{name} - {description}"
            
            # Determine embedding model version
            embedding_model = "openai" if len(embedding) == 1536 else "hash-fallback-v1"
            
            metadata = {
                "name": name,
                "bin_id": bin_id,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "embedding_model": embedding_model
            }

            self.inventory_collection.add(
                documents=[document_text],
                metadatas=[metadata],
                embeddings=[embedding],
                ids=[doc_id]
            )
            
            print(f"Added document: {name} (ID: {doc_id})")
            return True

        except Exception as e:
            print(f"Error adding document: {e}")
            return False

    def add_audit_log_entry(self, audit_entry: Dict[str, Any]) -> bool:
        """Add an audit log entry"""
        try:
            if self.audit_log_collection is None:
                print("Audit log collection not initialized")
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

            print(f"Added audit log entry: {audit_entry.get('action', 'unknown')}")
            return True

        except Exception as e:
            print(f"Error adding audit log entry: {e}")
            return False
    
    def search_documents(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Search documents in the inventory collection"""
        try:
            if self.inventory_collection is None:
                raise Exception("Inventory collection not initialized")

            # Get all documents for simple text matching
            all_results = self.inventory_collection.get(
                include=['metadatas', 'documents']
            )

            matching_items = []
            query_lower = query.lower()

            for i in range(len(all_results['ids'])):
                metadata = all_results['metadatas'][i] if all_results['metadatas'] else {}
                document = all_results['documents'][i] if all_results['documents'] else ""

                # Check if query matches name, description, or document text
                name = metadata.get('name', '').lower()
                description = metadata.get('description', '').lower()
                document_lower = document.lower()

                if (query_lower in name or
                    query_lower in description or
                    query_lower in document_lower):

                    matching_items.append({
                        "id": all_results['ids'][i],
                        "name": metadata.get('name', ''),
                        "description": metadata.get('description', ''),
                        "bin_id": metadata.get('bin_id', ''),
                        "created_at": metadata.get('created_at', ''),
                        "relevance_score": 1.0  # Simple matching - all matches have same score
                    })

            # Apply pagination
            total_results = len(matching_items)
            paginated_results = matching_items[offset:offset + limit]
            has_more = offset + limit < total_results

            return {
                "total_results": total_results,
                "results": paginated_results,
                "has_more": has_more
            }

        except Exception as e:
            print(f"Error searching documents: {e}")
            raise e
