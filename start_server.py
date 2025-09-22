#!/usr/bin/env python3
"""
Simple server startup script for testing
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("🚀 Starting BinBot Server...")
    print("Loading modules...")
    
    from app import app
    print("✅ App loaded successfully")
    
    import uvicorn
    print("✅ Uvicorn loaded successfully")
    
    print("🌐 Starting server on http://localhost:8000")
    print("📄 API docs will be available at http://localhost:8000/docs")
    print("💡 Press Ctrl+C to stop")
    print("-" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
    
except KeyboardInterrupt:
    print("\n👋 Server stopped by user")
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
