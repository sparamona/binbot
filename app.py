import os
import yaml
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import chromadb
from chromadb.config import Settings

from api_schemas import StandardResponse, HealthData, ErrorDetail

# Global variables for configuration, startup time, and database
config: Dict[str, Any] = {}
startup_time: float = 0
chroma_client: Optional[chromadb.ClientAPI] = None
inventory_collection: Optional[chromadb.Collection] = None
audit_log_collection: Optional[chromadb.Collection] = None

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml with environment variable substitution"""
    try:
        with open("config.yaml", "r") as file:
            config_content = file.read()
            
        # Replace environment variables
        import re
        def replace_env_var(match):
            env_var = match.group(1)
            return os.getenv(env_var, f"${{{env_var}}}")  # Keep original if not found
        
        config_content = re.sub(r'\$\{([^}]+)\}', replace_env_var, config_content)
        return yaml.safe_load(config_content)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def validate_llm_connection() -> bool:
    """Validate external LLM API connectivity"""
    try:
        provider = config.get("llm", {}).get("provider", "openai")
        
        if provider == "openai":
            api_key = config.get("llm", {}).get("openai", {}).get("api_key", "")
            if not api_key or api_key.startswith("${"):
                return False
            # For now, just check if API key is provided
            # Actual connection test will be implemented in Phase 4
            return True
            
        elif provider == "gemini":
            api_key = config.get("llm", {}).get("gemini", {}).get("api_key", "")
            if not api_key or api_key.startswith("${"):
                return False
            return True
            
        return False
    except Exception as e:
        print(f"LLM connection validation error: {e}")
        return False

def initialize_chromadb() -> bool:
    """Initialize ChromaDB client and collections"""
    global chroma_client, inventory_collection, audit_log_collection

    try:
        # Get database configuration
        db_config = config.get("database", {})
        persist_directory = db_config.get("persist_directory", "/app/data/chromadb")

        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB client with persistence
        chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create inventory collection
        collection_name = db_config.get("collection_name", "inventory")
        try:
            inventory_collection = chroma_client.get_collection(name=collection_name)
            print(f"Found existing inventory collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            inventory_collection = chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "description": "BinBot inventory items",
                    "embedding_model_version": config.get("llm", {}).get("openai", {}).get("embedding_model", "text-embedding-ada-002"),
                    "created_at": datetime.now().isoformat()
                }
            )
            print(f"Created new inventory collection: {collection_name}")

        # Get or create audit log collection
        audit_collection_name = "audit_log"
        try:
            audit_log_collection = chroma_client.get_collection(name=audit_collection_name)
            print(f"Found existing audit log collection: {audit_collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            audit_log_collection = chroma_client.create_collection(
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

def validate_database_connection() -> bool:
    """Validate ChromaDB connectivity"""
    try:
        if chroma_client is None:
            return False

        # Test connection by getting collection count
        collections = chroma_client.list_collections()
        return len(collections) >= 0  # Should always be true if connected

    except Exception as e:
        print(f"Database connection validation error: {e}")
        return False

def add_test_document(item_name: str, bin_id: str, description: str = "") -> bool:
    """Add a test document to the inventory collection"""
    try:
        if inventory_collection is None:
            return False

        # Generate a simple embedding (placeholder - will be replaced with LLM in Phase 4)
        # For now, use a simple hash-based approach for testing
        import hashlib
        text_to_embed = f"{item_name} {description}".strip()
        hash_obj = hashlib.md5(text_to_embed.encode())
        # Create a simple 384-dimensional embedding from hash
        hash_hex = hash_obj.hexdigest()
        embedding = []
        for i in range(0, len(hash_hex), 2):
            # Convert hex pairs to normalized floats
            val = int(hash_hex[i:i+2], 16) / 255.0 - 0.5  # Normalize to [-0.5, 0.5]
            embedding.append(val)

        # Pad or truncate to 384 dimensions (common embedding size)
        while len(embedding) < 384:
            embedding.extend(embedding[:min(len(embedding), 384 - len(embedding))])
        embedding = embedding[:384]

        # Generate unique ID
        item_id = str(uuid.uuid4())

        # Add document to collection (ChromaDB doesn't accept None values in metadata)
        inventory_collection.add(
            ids=[item_id],
            embeddings=[embedding],
            documents=[text_to_embed],
            metadatas=[{
                "item_id": item_id,
                "name": item_name,
                "description": description,
                "bin_id": bin_id,
                "embedding_model_version": "test-hash-v1",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }]
        )

        print(f"Added test document: {item_name} to bin {bin_id}")
        return True

    except Exception as e:
        print(f"Error adding test document: {e}")
        return False

def get_collection_stats() -> Dict[str, Any]:
    """Get basic statistics about the collections"""
    try:
        stats = {
            "inventory_count": 0,
            "audit_log_count": 0,
            "collections": []
        }

        if chroma_client:
            collections = chroma_client.list_collections()
            stats["collections"] = [col.name for col in collections]

            if inventory_collection:
                stats["inventory_count"] = inventory_collection.count()

            if audit_log_collection:
                stats["audit_log_count"] = audit_log_collection.count()

        return stats

    except Exception as e:
        print(f"Error getting collection stats: {e}")
        return {"error": str(e)}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global config, startup_time

    # Startup
    print("Starting BinBot application...")
    startup_time = time.time()
    config = load_config()

    if not config:
        print("Warning: Failed to load configuration")
    else:
        print("Configuration loaded successfully")

    # Initialize ChromaDB
    if not initialize_chromadb():
        print("Warning: ChromaDB initialization failed")

    yield

    # Shutdown
    print("Shutting down BinBot application...")

# Initialize FastAPI app
app = FastAPI(
    title="BinBot Inventory System",
    description="AI-powered basement inventory management system",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    """Serve the main frontend page"""
    return FileResponse("frontend/index.html")

@app.get("/health", response_model=StandardResponse)
async def health_check():
    """System health check endpoint"""
    try:
        # Check database connection
        db_connected = validate_database_connection()

        # Check LLM connection
        llm_connected = validate_llm_connection()

        # Calculate uptime
        uptime = time.time() - startup_time

        # Get collection statistics
        collection_stats = get_collection_stats()

        # Determine overall status
        status = "healthy" if db_connected and llm_connected else "degraded"

        # Create enhanced health data
        health_data = {
            "status": status,
            "database_connected": db_connected,
            "llm_connected": llm_connected,
            "version": "1.0.0",
            "uptime_seconds": uptime,
            "collections": collection_stats
        }

        return StandardResponse(
            success=True,
            data=health_data
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="HEALTH_CHECK_ERROR",
            message="Failed to perform health check",
            details={"error": str(e)}
        )

        return StandardResponse(
            success=False,
            error=error_detail
        )

@app.post("/test/add-sample-data", response_model=StandardResponse)
async def add_sample_data():
    """Add sample test data to the inventory (for Phase 2 testing)"""
    try:
        if inventory_collection is None:
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
                "total_items": sample_items
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="ADD_SAMPLE_DATA_ERROR",
            message="Failed to add sample data",
            details={"error": str(e)}
        )

        return StandardResponse(
            success=False,
            error=error_detail
        )

@app.get("/test/list-items", response_model=StandardResponse)
async def list_stored_items():
    """List all items currently stored in ChromaDB (for Phase 2 demonstration)"""
    try:
        if inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Get all documents from the collection
        results = inventory_collection.get()

        # Format the results for display
        items = []
        if results['ids']:
            for i in range(len(results['ids'])):
                item = {
                    "id": results['ids'][i],
                    "document": results['documents'][i] if results['documents'] else None,
                    "metadata": results['metadatas'][i] if results['metadatas'] else None,
                    "embedding_preview": results['embeddings'][i][:10] if results['embeddings'] and results['embeddings'][i] else None  # Show first 10 dimensions
                }
                items.append(item)

        return StandardResponse(
            success=True,
            data={
                "total_items": len(items),
                "items": items,
                "collection_info": {
                    "name": inventory_collection.name,
                    "count": inventory_collection.count()
                }
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="LIST_ITEMS_ERROR",
            message="Failed to list items",
            details={"error": str(e)}
        )
        print(f"Error listing items: {e}")
        return StandardResponse(
            success=False,
            error=error_detail
        )

@app.get("/search", response_model=StandardResponse)
async def search_inventory(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Search inventory items using simple text matching (Phase 3)"""
    try:
        if inventory_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Get all documents from the collection
        all_results = inventory_collection.get()

        if not all_results['ids']:
            return StandardResponse(
                success=True,
                data={
                    "query": q,
                    "total_results": 0,
                    "results": [],
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "has_more": False
                    }
                }
            )

        # Simple text matching - search in name, description, and document text
        matching_items = []
        query_lower = q.lower()

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

        return StandardResponse(
            success=True,
            data={
                "query": q,
                "total_results": total_results,
                "results": paginated_results,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": has_more
                }
            }
        )

    except Exception as e:
        error_detail = ErrorDetail(
            code="SEARCH_ERROR",
            message="Failed to search inventory",
            details={"error": str(e), "query": q}
        )
        print(f"Error searching inventory: {e}")
        return StandardResponse(
            success=False,
            error=error_detail
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    error_detail = ErrorDetail(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        details={"error": str(exc)}
    )
    
    return StandardResponse(
        success=False,
        error=error_detail
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get server config
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    debug = server_config.get("debug", False)
    
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=debug)
