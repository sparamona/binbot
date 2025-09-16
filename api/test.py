from fastapi import APIRouter, HTTPException
from api_schemas import StandardResponse, ErrorDetail
from database.chromadb_client import ChromaDBClient
from llm.embeddings import EmbeddingService

router = APIRouter(prefix="/test", tags=["test"])

# These will be injected by the main app
db_client: ChromaDBClient = None
embedding_service: EmbeddingService = None


def set_dependencies(db: ChromaDBClient, embeddings: EmbeddingService):
    """Set dependencies for the test router"""
    global db_client, embedding_service
    db_client = db
    embedding_service = embeddings


@router.post("/add-sample-data", response_model=StandardResponse)
async def add_sample_data():
    """Add sample test data to the inventory (for Phase 2 testing)"""
    try:
        if db_client.inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Sample items to add
        sample_items = [
            {"name": "Phillips head screwdriver", "bin_id": "1", "description": "Medium size Phillips head screwdriver with red handle"},
            {"name": "Electrical wire nuts", "bin_id": "1", "description": "Pack of yellow wire nuts for electrical connections"},
            {"name": "LED light bulbs", "bin_id": "2", "description": "60W equivalent LED bulbs, warm white"},
            {"name": "Duct tape", "bin_id": "2", "description": "Silver duct tape roll, heavy duty"},
            {"name": "Arduino Uno", "bin_id": "3", "description": "Arduino Uno R3 microcontroller board"},
            {"name": "Breadboard jumper wires", "bin_id": "3", "description": "Assorted male-to-male breadboard jumper wires"},
        ]

        added_count = 0
        for item in sample_items:
            if add_test_document(item["name"], item["bin_id"], item["description"]):
                added_count += 1

        return StandardResponse(
            success=True,
            data={
                "message": f"Added {added_count} sample items to inventory",
                "items_added": added_count,
                "total_items_attempted": len(sample_items)
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="SAMPLE_DATA_ERROR",
            message="Failed to add sample data",
            details={"error": str(e)}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.get("/list-items", response_model=StandardResponse)
async def list_test_items():
    """List all items in the inventory (for testing)"""
    try:
        if db_client.inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Get all items
        all_results = db_client.inventory_collection.get(
            include=['metadatas', 'documents']
        )

        items = []
        for i in range(len(all_results['ids'])):
            metadata = all_results['metadatas'][i] if all_results['metadatas'] else {}
            document = all_results['documents'][i] if all_results['documents'] else ""

            # Parse image information from ChromaDB metadata
            images_json = metadata.get('images_json', '')
            images = images_json.split(',') if images_json else []
            images = [img.strip() for img in images if img.strip()]  # Clean up empty strings

            items.append({
                "id": all_results['ids'][i],
                "name": metadata.get('name', ''),
                "description": metadata.get('description', ''),
                "bin_id": metadata.get('bin_id', ''),
                "created_at": metadata.get('created_at', ''),
                "embedding_model": metadata.get('embedding_model', 'unknown'),
                "document": document,
                "images": images,
                "images_count": metadata.get('images_count', 0),
                "primary_image": metadata.get('primary_image', '')
            })

        return StandardResponse(
            success=True,
            data={
                "total_items": len(items),
                "items": items
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="LIST_ITEMS_ERROR",
            message="Failed to list items",
            details={"error": str(e)}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.get("/stats", response_model=StandardResponse)
async def get_collection_stats():
    """Get ChromaDB collection statistics"""
    try:
        if db_client is None:
            raise HTTPException(status_code=500, detail="Database client not initialized")

        stats = db_client.get_collection_stats()

        return StandardResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="STATS_ERROR",
            message="Failed to get collection stats",
            details={"error": str(e)}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.get("/debug-search", response_model=StandardResponse)
async def debug_search(q: str = "mouse"):
    """Debug search functionality by showing raw ChromaDB query results"""
    try:
        if db_client is None or db_client.inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Generate embedding for the search query using global embedding service
        if embedding_service is None:
            raise HTTPException(status_code=500, detail="Embedding service not initialized")

        query_embedding = embedding_service.generate_embedding(q)

        if not query_embedding:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="EMBEDDING_ERROR",
                    message="Failed to generate embedding for query",
                    details={"query": q}
                )
            )

        # Perform raw ChromaDB query
        search_results = db_client.inventory_collection.query(
            query_embeddings=[query_embedding],
            n_results=50,  # Get many results for debugging
            include=['metadatas', 'documents', 'distances']
        )

        # Format results for debugging
        debug_results = []
        if search_results['ids'] and len(search_results['ids'][0]) > 0:
            ids = search_results['ids'][0]
            metadatas = search_results['metadatas'][0] if search_results['metadatas'] else []
            distances = search_results['distances'][0] if search_results['distances'] else []
            documents = search_results['documents'][0] if search_results['documents'] else []

            for i in range(len(ids)):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 1.0
                document = documents[i] if i < len(documents) else ""
                relevance_score = max(0.0, 1.0 - distance)

                debug_results.append({
                    "id": ids[i],
                    "name": metadata.get('name', ''),
                    "description": metadata.get('description', ''),
                    "bin_id": metadata.get('bin_id', ''),
                    "created_at": metadata.get('created_at', ''),
                    "embedding_model": metadata.get('embedding_model', ''),
                    "document": document,
                    "distance": distance,
                    "relevance_score": relevance_score
                })

        return StandardResponse(
            success=True,
            data={
                "query": q,
                "query_embedding_length": len(query_embedding),
                "total_results": len(debug_results),
                "results": debug_results[:20]  # Limit to first 20 for readability
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="DEBUG_SEARCH_ERROR",
            message="Failed to debug search",
            details={"error": str(e), "query": q}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.get("/debug-embedding", response_model=StandardResponse)
async def debug_embedding(text: str = "test mouse"):
    """Debug embedding generation to compare old vs new methods"""
    try:
        if embedding_service is None:
            raise HTTPException(status_code=500, detail="Embedding service not initialized")

        # Generate embedding using the service
        embedding = embedding_service.generate_embedding(text)

        if not embedding:
            return StandardResponse(
                success=False,
                error=ErrorDetail(
                    code="EMBEDDING_ERROR",
                    message="Failed to generate embedding",
                    details={"text": text}
                )
            )

        # Get some statistics about the embedding
        embedding_stats = {
            "length": len(embedding),
            "min_value": min(embedding),
            "max_value": max(embedding),
            "mean_value": sum(embedding) / len(embedding),
            "first_10_values": embedding[:10],
            "data_type": str(type(embedding[0])),
            "sum_of_squares": sum(x*x for x in embedding)
        }

        return StandardResponse(
            success=True,
            data={
                "text": text,
                "embedding_stats": embedding_stats
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="DEBUG_EMBEDDING_ERROR",
            message="Failed to debug embedding",
            details={"error": str(e), "text": text}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.get("/debug-chromadb", response_model=StandardResponse)
async def debug_chromadb():
    """Debug ChromaDB collection to see what's actually stored"""
    try:
        if db_client is None or db_client.inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Get all items from ChromaDB directly
        all_results = db_client.inventory_collection.get(
            include=['metadatas', 'documents', 'embeddings']
        )

        debug_items = []
        if all_results['ids']:
            for i in range(len(all_results['ids'])):
                item_id = all_results['ids'][i]
                metadata = all_results['metadatas'][i] if i < len(all_results['metadatas']) else {}
                document = all_results['documents'][i] if i < len(all_results['documents']) else ""
                embedding = all_results['embeddings'][i] if i < len(all_results['embeddings']) else []

                # Get embedding statistics
                embedding_stats = {}
                if embedding:
                    embedding_stats = {
                        "length": len(embedding),
                        "min_value": min(embedding),
                        "max_value": max(embedding),
                        "mean_value": sum(embedding) / len(embedding),
                        "sum_of_squares": sum(x*x for x in embedding),
                        "first_5_values": embedding[:5]
                    }

                debug_items.append({
                    "id": item_id,
                    "name": metadata.get('name', ''),
                    "bin_id": metadata.get('bin_id', ''),
                    "created_at": metadata.get('created_at', ''),
                    "embedding_model": metadata.get('embedding_model', ''),
                    "document": document,
                    "embedding_stats": embedding_stats
                })

        # Sort by created_at to see newest items first
        debug_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return StandardResponse(
            success=True,
            data={
                "total_items": len(debug_items),
                "items": debug_items[:10]  # Show first 10 items
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="DEBUG_CHROMADB_ERROR",
            message="Failed to debug ChromaDB",
            details={"error": str(e)}
        )
        return StandardResponse(
            success=False,
            error=error_detail
        )


@router.post("/test-image-upload-process", response_model=StandardResponse)
async def test_image_upload_process():
    """Test the exact same process as image upload to debug embedding issues"""
    try:
        # Simulate the exact same process as image upload
        item_name = "Test Coaster Item"
        description = "Round, light brown cardboard with a spiral cut pattern. Test item for debugging."
        bin_id = "99"

        # Generate embedding exactly like image upload does
        embedding_text = f"{item_name} {description}"
        embedding = embedding_service.generate_embedding(embedding_text)

        if embedding is None:
            return StandardResponse(
                success=False,
                error="Failed to generate embedding"
            )

        # Store using individual add_document method exactly like image upload does
        created_item_id = db_client.add_document(
            name=item_name,
            bin_id=bin_id,
            description=description,
            embedding=embedding
        )

        if not created_item_id:
            return StandardResponse(
                success=False,
                error="Failed to add document"
            )

        # Test search immediately
        search_response = db_client.search_documents("coaster", limit=5)
        search_results = search_response.get("results", []) if search_response else []

        return StandardResponse(
            success=True,
            data={
                "message": "Test item added successfully",
                "embedding_length": len(embedding),
                "embedding_type": str(type(embedding)),
                "embedding_sample": embedding[:5],
                "search_results_count": len(search_results),
                "search_sample": [{"name": r.get("name", ""), "relevance": r.get("relevance_score", 0)} for r in search_results[:2]]
            }
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=str(e)
        )


def add_test_document(name: str, bin_id: str, description: str) -> bool:
    """Add a test document to the inventory collection"""
    try:
        document_text = f"{name} - {description}"

        # Generate embedding using the embedding service
        embedding = embedding_service.generate_embedding(document_text)
        if embedding is None:
            print(f"Failed to generate embedding for: {name}")
            return False

        # Add document to database
        created_item_id = db_client.add_document(name, bin_id, description, embedding)
        return created_item_id is not None

    except Exception as e:
        print(f"Error adding test document: {e}")
        return False


@router.post("/clear-database", response_model=StandardResponse)
async def clear_database():
    """Clear all data from the database - DESTRUCTIVE OPERATION"""
    try:
        if db_client is None or db_client.inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Get current item count before clearing
        try:
            current_items = db_client.inventory_collection.get()
            items_count = len(current_items['ids']) if current_items['ids'] else 0
        except Exception:
            items_count = 0

        # Clear the inventory collection by deleting and recreating it
        collection_name = db_client.config.get("database", {}).get("collection_name", "inventory")

        # Delete the collection
        try:
            db_client.client.delete_collection(collection_name)
            print(f"Deleted collection: {collection_name}")
        except Exception as e:
            print(f"Warning: Could not delete collection {collection_name}: {e}")

        # Recreate the collection
        try:
            from datetime import datetime
            db_client.inventory_collection = db_client.client.create_collection(
                name=collection_name,
                metadata={
                    "description": "BinBot inventory items",
                    "embedding_model_version": db_client.config.get("llm", {}).get("openai", {}).get("embedding_model", "text-embedding-ada-002"),
                    "created_at": datetime.now().isoformat()
                }
            )
            print(f"Recreated collection: {collection_name}")
        except Exception as e:
            print(f"Error recreating collection: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to recreate collection: {e}")

        # TODO: Clear image files from storage (if needed)
        # This would require integration with the image storage system
        images_deleted = 0  # Placeholder for now

        return StandardResponse(
            success=True,
            data={
                "message": "Database cleared successfully",
                "items_deleted": items_count,
                "images_deleted": images_deleted,
                "collection_recreated": True
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error clearing database: {e}")
        return StandardResponse(
            success=False,
            error=ErrorDetail(
                code="CLEAR_DATABASE_ERROR",
                message="Failed to clear database",
                details={"error": str(e)}
            )
        )
