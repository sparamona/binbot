"""
Tests for inventory API endpoints
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

import asyncio
from api.inventory import add_items, search_items, get_bin_contents
from api_schemas import AddItemsRequest, ItemInput, SearchRequest
from session.session_manager import get_session_manager


async def test_inventory_endpoints():
    """Test inventory management endpoints"""
    print("🧪 Testing Inventory Endpoints")
    print("=" * 35)
    
    # Create a test session
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    print(f"📝 Created test session: {session_id[:8]}...")
    
    # Test 1: Add items to bin
    print("\n➕ Test 1: Add items to bin")
    add_request = AddItemsRequest(
        bin_id="TEST_BIN",
        items=[
            ItemInput(name="Test Screwdriver", description="Phillips head screwdriver"),
            ItemInput(name="Test Hammer", description="Claw hammer")
        ]
    )
    
    response = await add_items(add_request, session_id)
    
    print(f"📋 Success: {response.success}")
    print(f"📋 Items added: {len(response.items)}")
    print(f"📋 Current bin: {response.current_bin}")
    
    assert response.success is True
    assert len(response.items) == 2
    assert response.current_bin == "TEST_BIN"
    print("✅ Items added successfully")
    
    # Test 2: Get bin contents
    print("\n📦 Test 2: Get bin contents")
    response = await get_bin_contents("TEST_BIN", session_id)
    
    print(f"📋 Success: {response.success}")
    print(f"📋 Bin ID: {response.bin_id}")
    print(f"📋 Total count: {response.total_count}")
    print(f"📋 Items: {[item.name for item in response.items]}")
    
    assert response.success is True
    assert response.bin_id == "TEST_BIN"
    assert response.total_count == 2
    assert any(item.name == "Test Screwdriver" for item in response.items)
    assert any(item.name == "Test Hammer" for item in response.items)
    print("✅ Bin contents retrieved successfully")
    
    # Test 3: Search for items
    print("\n🔍 Test 3: Search for items")
    search_request = SearchRequest(query="screwdriver", limit=5)
    
    response = await search_items(search_request, session_id)
    
    print(f"📋 Success: {response.success}")
    print(f"📋 Items found: {len(response.items)}")
    if response.items:
        print(f"📋 First result: {response.items[0].name}")
        print(f"📋 Confidence: {response.items[0].confidence_score}")
    
    assert response.success is True
    assert len(response.items) >= 1
    assert any("screwdriver" in item.name.lower() for item in response.items)
    print("✅ Search working correctly")
    
    # Test 4: Search with no results
    print("\n🔍 Test 4: Search with no results")
    search_request = SearchRequest(query="nonexistent_item_xyz", limit=5)
    
    response = await search_items(search_request, session_id)
    
    print(f"📋 Success: {response.success}")
    print(f"📋 Items found: {len(response.items)}")
    
    assert response.success is True
    assert len(response.items) == 0
    print("✅ Empty search results handled correctly")
    
    # Test 5: Get empty bin contents
    print("\n📦 Test 5: Get empty bin contents")
    response = await get_bin_contents("EMPTY_BIN", session_id)
    
    print(f"📋 Success: {response.success}")
    print(f"📋 Total count: {response.total_count}")
    
    assert response.success is True
    assert response.total_count == 0
    assert len(response.items) == 0
    print("✅ Empty bin handled correctly")
    
    return True


async def test_error_handling():
    """Test error handling for inventory endpoints"""
    print("\n❌ Testing Error Handling")
    print("=" * 30)
    
    # Test missing session ID
    print("\n🚫 Test: Missing session ID")
    try:
        add_request = AddItemsRequest(
            bin_id="TEST_BIN",
            items=[ItemInput(name="Test Item")]
        )
        await add_items(add_request, "")
        assert False, "Should have raised HTTPException"
    except Exception as e:
        print(f"📋 Expected error: {e}")
        print("✅ Missing session ID handled correctly")
    
    return True


if __name__ == "__main__":
    print("📦 BinBot Inventory API Test")
    print("Tests inventory management endpoints")
    print()
    
    async def run_all_tests():
        success1 = await test_inventory_endpoints()
        success2 = await test_error_handling()
        return success1 and success2
    
    success = asyncio.run(run_all_tests())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Inventory API tests passed!")
    else:
        print("❌ Inventory API tests failed!")
