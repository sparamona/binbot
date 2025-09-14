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

            items.append({
                "id": all_results['ids'][i],
                "name": metadata.get('name', ''),
                "description": metadata.get('description', ''),
                "bin_id": metadata.get('bin_id', ''),
                "created_at": metadata.get('created_at', ''),
                "embedding_model": metadata.get('embedding_model', 'unknown'),
                "document": document
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
        return db_client.add_document(name, bin_id, description, embedding)

    except Exception as e:
        print(f"Error adding test document: {e}")
        return False
