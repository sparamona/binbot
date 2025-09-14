import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config.settings import Settings
from database.chromadb_client import ChromaDBClient
from llm.client import LLMClient
from llm.embeddings import EmbeddingService
from api import health, search, test, add, remove, move, session, context
from api_schemas import StandardResponse, ErrorDetail

# Global instances
settings = Settings()
llm_client = LLMClient(settings.config)
db_client = ChromaDBClient(settings.config, llm_client)
embedding_service = EmbeddingService(llm_client)
startup_time: float = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global startup_time

    # Startup
    print("Starting BinBot application...")
    startup_time = time.time()

    # Initialize database
    if not db_client.initialize():
        print("Warning: Database initialization failed")
    else:
        print("Database initialized successfully")

    # Initialize LLM clients
    llm_client.initialize()

    # Set dependencies for API routers
    health.set_dependencies(db_client, llm_client, startup_time)
    search.set_dependencies(db_client)
    test.set_dependencies(db_client, embedding_service)
    add.set_dependencies(db_client, embedding_service)
    remove.set_dependencies(db_client, embedding_service)
    move.set_dependencies(db_client, embedding_service)

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

# Include API routers
app.include_router(health.router)
app.include_router(search.router)
app.include_router(test.router)
app.include_router(add.router)
app.include_router(remove.router)
app.include_router(move.router)
app.include_router(session.router, prefix="/session", tags=["session"])
app.include_router(context.router, prefix="/context", tags=["context"])

# Set dependencies for API routers
health.set_dependencies(db_client, llm_client, startup_time)
add.set_dependencies(db_client, embedding_service)
remove.set_dependencies(db_client, embedding_service)
move.set_dependencies(db_client, embedding_service)
context.set_dependencies(db_client, embedding_service)

@app.get("/test")
async def test_page():
    """Serve the test page"""
    return FileResponse("frontend/index.html")

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

    # Get server config from settings
    server_config = settings.config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    debug = server_config.get("debug", False)

    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=debug)
