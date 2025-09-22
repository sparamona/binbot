#!/usr/bin/env python3
"""
Production server runner without auto-reload
"""

import uvicorn
import os

def main():
    """Run the production server"""
    print("🚀 Starting BinBot Production Server")
    print("=" * 50)
    print("🔒 Auto-reload: DISABLED")
    print("🌐 Server: http://localhost:8000")
    print("📄 API Docs: http://localhost:8000/docs")
    print("🎯 Frontend: http://localhost:8000")
    print("=" * 50)
    print("💡 Press Ctrl+C to stop the server")
    print()
    
    # Set production environment
    os.environ["DEVELOPMENT"] = "false"
    
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Production server stopped")

if __name__ == "__main__":
    main()
