import os
import yaml
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from api_schemas import StandardResponse, HealthData, ErrorDetail

# Global variables for configuration and startup time
config: Dict[str, Any] = {}
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

def validate_database_connection() -> bool:
    """Validate ChromaDB connectivity (placeholder for Phase 2)"""
    # For Phase 1, we'll just return True
    # Actual ChromaDB connection will be implemented in Phase 2
    return True

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
        
        # Determine overall status
        status = "healthy" if db_connected and llm_connected else "degraded"
        
        health_data = HealthData(
            status=status,
            database_connected=db_connected,
            llm_connected=llm_connected,
            version="1.0.0",
            uptime_seconds=uptime
        )
        
        return StandardResponse(
            success=True,
            data=health_data.model_dump()
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
