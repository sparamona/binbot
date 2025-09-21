#!/usr/bin/env python3
"""
Development server runner with auto-reload enabled
"""

import uvicorn
import os

def main():
    """Run the development server with auto-reload"""
    print("🚀 Starting BinBot Development Server")
    print("=" * 50)
    print("✨ Auto-reload: ENABLED")
    print("🔄 Watching directories: api, llm, chat, session, storage, config")
    print("🌐 Server: http://localhost:8001")
    print("📄 API Docs: http://localhost:8001/docs")
    print("🎯 Frontend: http://localhost:8001")
    print("=" * 50)
    print("💡 Press Ctrl+C to stop the server")
    print()
    
    # Set development environment
    os.environ["DEVELOPMENT"] = "true"
    
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            reload_dirs=[".", "api", "llm", "chat", "session", "storage", "config"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")

if __name__ == "__main__":
    main()
