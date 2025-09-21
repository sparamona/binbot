"""
BinBot FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Import API routers
from api.health import router as health_router
from api.session import router as session_router
from api.inventory import router as inventory_router
from api.images import router as images_router
from api.chat import router as chat_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="BinBot API",
        description="AI-assisted inventory management system",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(health_router, tags=["Health"])
    app.include_router(session_router, tags=["Session"])
    app.include_router(inventory_router, tags=["Inventory"])
    app.include_router(images_router, tags=["Images"])
    app.include_router(chat_router, tags=["Chat"])
    
    # Serve static files (frontend)
    frontend_path = Path("frontend")
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    import os

    # Enable auto-reload in development
    reload = os.getenv("DEVELOPMENT", "true").lower() == "true"

    uvicorn.run(
        "app:app",  # Use string reference for reload to work
        host="0.0.0.0",
        port=8000,
        reload=reload,
        reload_dirs=[".", "api", "llm", "chat", "session", "storage", "config"]
    )
