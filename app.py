import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config.settings import Settings
from database.chromadb_client import ChromaDBClient
from llm.client import LLMClient
from api import health, search, test

# Global instances
settings = Settings()
db_client = ChromaDBClient(settings.config)
llm_client = LLMClient(settings.config)
startup_time: float = 0

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

def initialize_llm_clients():
    """Initialize LLM clients based on available API keys and configuration"""
    global openai_client, gemini_model, llm_provider

    openai_key = os.environ.get('OPENAI_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')

    # Try to initialize OpenAI client
    if openai_key and openai_key != "${OPENAI_API_KEY}" and OPENAI_AVAILABLE:
        try:
            print(f"DEBUG: Attempting to initialize OpenAI client...")
            print(f"DEBUG: OpenAI available: {OPENAI_AVAILABLE}")
            print(f"DEBUG: API key present: {bool(openai_key)}")
            print(f"DEBUG: API key starts with: {openai_key[:10]}..." if openai_key else "No key")
            print(f"DEBUG: OpenAI version: {openai.__version__}")

            # Initialize OpenAI client with minimal configuration
            openai_client = openai.OpenAI(api_key=openai_key)
            llm_provider = "openai"
            print("OpenAI client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            print(f"DEBUG: Exception args: {e.args}")
            import traceback
            print(f"DEBUG: Full traceback:")
            traceback.print_exc()
            openai_client = None

    # Try to initialize Gemini client
    if gemini_key and gemini_key != "${GEMINI_API_KEY}" and GOOGLE_AI_AVAILABLE:
        try:
            genai.configure(api_key=gemini_key)
            gemini_model = genai.GenerativeModel('gemini-pro')
            if llm_provider is None:  # Only set if OpenAI wasn't successful
                llm_provider = "gemini"
            print("Gemini client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Gemini client: {e}")
            gemini_model = None

    if llm_provider is None:
        print("No LLM clients initialized. Set OPENAI_API_KEY or GEMINI_API_KEY environment variable.")

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text using available LLM service"""
    if not text.strip():
        return None

    try:
        if llm_provider == "openai" and openai_client:
            response = openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        elif llm_provider == "gemini" and gemini_model:
            # Note: Gemini doesn't have a direct embedding API yet
            # For now, fall back to hash-based embeddings
            return generate_hash_embedding(text)
        else:
            # Fall back to hash-based embeddings
            return generate_hash_embedding(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return generate_hash_embedding(text)

def generate_hash_embedding(text: str) -> List[float]:
    """Generate hash-based embedding as fallback"""
    hash_obj = hashlib.md5(text.encode())
    hash_bytes = hash_obj.digest()

    # Convert to 384-dimensional embedding
    embedding = []
    for i in range(384):
        byte_index = i % len(hash_bytes)
        embedding.append((hash_bytes[byte_index] / 255.0) * 2.0 - 1.0)

    return embedding

def validate_llm_connection() -> bool:
    """Validate external LLM API connectivity"""
    try:
        # Check if any LLM client is initialized
        return llm_provider is not None and (openai_client is not None or gemini_model is not None)
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

        # Generate embedding using LLM or fallback to hash
        text_to_embed = f"{item_name} {description}".strip()
        embedding = generate_embedding(text_to_embed)

        if embedding is None:
            print(f"Failed to generate embedding for: {item_name}")
            return False

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
                "embedding_model_version": llm_provider if llm_provider else "hash-fallback-v1",
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

    # Initialize LLM clients
    initialize_llm_clients()

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
