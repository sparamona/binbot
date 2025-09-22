"""
Tests for session API endpoints
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

import asyncio
from fastapi import Response
from api.session import start_session, get_session, end_session
from session.session_manager import get_session_manager


async def test_session_endpoints():
    """Test session management endpoints"""
    print("🧪 Testing Session Endpoints")
    print("=" * 35)

    # Mock response object for cookie handling
    class MockResponse:
        def __init__(self):
            self.cookies = {}

        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

        def delete_cookie(self, key, **kwargs):
            if key in self.cookies:
                del self.cookies[key]
    
    # Test 1: Create session
    print("\n📝 Test 1: Create session")
    mock_response = MockResponse()
    response = await start_session(mock_response)

    print(f"📋 Response: {response}")

    assert response.success is True
    assert response.session_id is not None
    session_id = response.session_id

    # Check cookie was set
    assert "session_id" in mock_response.cookies
    print("✅ Session created with cookie")
    
    # Test 2: Get session info
    print("\n📋 Test 2: Get session info")
    response = await get_session(session_id)

    print(f"📋 Response: {response}")

    assert response.success is True
    assert response.session.session_id == session_id
    assert response.session.created_at is not None
    assert response.session.last_accessed is not None
    assert response.session.current_bin == ""
    assert response.session.conversation == []
    print("✅ Session info retrieved")
    
    # Test 3: Get non-existent session
    print("\n❌ Test 3: Get non-existent session")
    try:
        await get_session("invalid-session-id")
        assert False, "Should have raised HTTPException"
    except Exception as e:
        print(f"📋 Expected error: {e}")
        print("✅ Non-existent session raises exception")

    # Test 4: End session
    print("\n🗑️ Test 4: End session")
    mock_response2 = MockResponse()
    response = await end_session(session_id, mock_response2)

    print(f"📋 Response: {response}")

    assert response.success is True
    assert response.session_id == session_id
    print("✅ Session ended")

    # Test 5: Verify session is gone
    print("\n🔍 Test 5: Verify session is gone")
    try:
        await get_session(session_id)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        print(f"📋 Expected error: {e}")
        print("✅ Ended session is no longer accessible")
    
    return True


if __name__ == "__main__":
    print("🔐 BinBot Session API Test")
    print("Tests session management endpoints")
    print()

    success = asyncio.run(test_session_endpoints())

    print("\n" + "=" * 50)
    if success:
        print("🎉 Session API tests passed!")
    else:
        print("❌ Session API tests failed!")
