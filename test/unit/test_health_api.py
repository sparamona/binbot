"""
Tests for health API endpoint
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

import asyncio
from api.health import health_check


async def test_health_endpoint():
    """Test health check endpoint function directly"""
    print("🧪 Testing Health Endpoint")
    print("=" * 30)

    # Test health check function directly
    response = await health_check()

    print(f"📋 Response: {response}")
    print(f"📋 Status: {response.status}")

    # Verify response
    assert response.status == "ok"

    print("✅ Health endpoint working correctly")
    return True


if __name__ == "__main__":
    print("🏥 BinBot Health API Test")
    print("Tests health check endpoint")
    print()

    success = asyncio.run(test_health_endpoint())

    print("\n" + "=" * 40)
    if success:
        print("🎉 Health API test passed!")
    else:
        print("❌ Health API test failed!")
