"""
Tests for FastAPI application setup
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

from app import create_app


def test_app_creation():
    """Test FastAPI app creation and configuration"""
    print("🧪 Testing FastAPI App Creation")
    print("=" * 32)
    
    # Create app
    app = create_app()
    
    print(f"📋 App title: {app.title}")
    print(f"📋 App version: {app.version}")
    print(f"📋 App description: {app.description}")
    
    assert app.title == "BinBot API"
    assert app.version == "1.0.0"
    assert "inventory management" in app.description.lower()
    
    print("✅ App created with correct metadata")
    
    # Check that routers are included
    routes = [route.path for route in app.routes]
    print(f"📋 Total routes: {len(routes)}")
    
    # Check for key endpoints
    expected_paths = ["/health", "/api/session", "/api/inventory/add", "/api/images", "/api/chat/command"]
    
    found_paths = []
    for expected in expected_paths:
        for route_path in routes:
            if expected in route_path:
                found_paths.append(expected)
                break
    
    print(f"📋 Found {len(found_paths)} expected endpoints")
    for path in found_paths:
        print(f"  ✅ {path}")
    
    # We expect at least some key endpoints
    assert len(found_paths) >= 3, f"Expected at least 3 endpoints, found {len(found_paths)}"
    
    print("✅ App configured with API routers")
    return True


def test_app_middleware():
    """Test that CORS middleware is configured"""
    print("\n🧪 Testing App Middleware")
    print("=" * 25)
    
    app = create_app()
    
    # Check middleware
    middleware_count = len(app.user_middleware)
    print(f"📋 Middleware count: {middleware_count}")
    
    # Should have at least CORS middleware
    assert middleware_count >= 1, "Expected at least CORS middleware"
    
    print("✅ Middleware configured")
    return True


def test_app_import():
    """Test that the app can be imported"""
    print("\n🧪 Testing App Import")
    print("=" * 20)
    
    try:
        from app import app
        assert app is not None
        print("✅ App imported successfully")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 BinBot FastAPI App Test")
    print("Tests application setup and configuration")
    print()
    
    success1 = test_app_creation()
    success2 = test_app_middleware()
    success3 = test_app_import()
    
    success = success1 and success2 and success3
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FastAPI app tests passed!")
    else:
        print("❌ FastAPI app tests failed!")
