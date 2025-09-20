"""
Tests for API schemas
"""

import sys
sys.path.append('.')

from api_schemas import (
    ItemInput, Item, AddItemsRequest, SearchRequest, 
    ChatRequest, ItemsResponse, ChatResponse, HealthResponse
)


def test_item_models():
    """Test item-related models"""
    print("🧪 Testing item models...")
    
    # Test ItemInput
    item_input = ItemInput(name="Screwdriver", description="Phillips head")
    assert item_input.name == "Screwdriver"
    assert item_input.description == "Phillips head"
    assert item_input.image_id == ""  # Default value
    print("✅ ItemInput model works")
    
    # Test Item
    item = Item(
        id="123",
        name="Screwdriver",
        description="Phillips head",
        bin_id="A3",
        created_at="2024-01-01T00:00:00",
        image_id="img-123"
    )
    assert item.id == "123"
    assert item.bin_id == "A3"
    print("✅ Item model works")
    
    return True


def test_request_models():
    """Test request models"""
    print("🧪 Testing request models...")
    
    # Test AddItemsRequest
    add_request = AddItemsRequest(
        bin_id="A3",
        items=[
            ItemInput(name="Screwdriver"),
            ItemInput(name="Wrench", description="10mm")
        ]
    )
    assert add_request.bin_id == "A3"
    assert len(add_request.items) == 2
    print("✅ AddItemsRequest model works")
    
    # Test SearchRequest
    search_request = SearchRequest(query="tools")
    assert search_request.query == "tools"
    assert search_request.limit == 10  # Default value
    print("✅ SearchRequest model works")
    
    # Test ChatRequest
    chat_request = ChatRequest(message="Hello", session_id="sess-123")
    assert chat_request.message == "Hello"
    assert chat_request.session_id == "sess-123"
    print("✅ ChatRequest model works")
    
    return True


def test_response_models():
    """Test response models"""
    print("🧪 Testing response models...")
    
    # Test ItemsResponse
    items_response = ItemsResponse(
        success=True,
        items=[
            Item(
                id="123",
                name="Test",
                description="",
                bin_id="A3",
                created_at="2024-01-01T00:00:00",
                image_id=""
            )
        ]
    )
    assert items_response.success is True
    assert len(items_response.items) == 1
    print("✅ ItemsResponse model works")
    
    # Test ChatResponse
    chat_response = ChatResponse(success=True, response="Hello there!")
    assert chat_response.success is True
    assert chat_response.response == "Hello there!"
    print("✅ ChatResponse model works")
    
    # Test HealthResponse
    health_response = HealthResponse(status="ok")
    assert health_response.status == "ok"
    print("✅ HealthResponse model works")
    
    return True


def test_json_serialization():
    """Test JSON serialization/deserialization"""
    print("🧪 Testing JSON serialization...")
    
    # Create a request
    request = AddItemsRequest(
        bin_id="A3",
        items=[ItemInput(name="Test Item")]
    )
    
    # Serialize to JSON
    json_data = request.model_dump()
    assert json_data['bin_id'] == "A3"
    assert len(json_data['items']) == 1
    print("✅ JSON serialization works")
    
    # Deserialize from JSON
    recreated = AddItemsRequest(**json_data)
    assert recreated.bin_id == "A3"
    assert recreated.items[0].name == "Test Item"
    print("✅ JSON deserialization works")
    
    return True


if __name__ == "__main__":
    print("🧪 Testing API schemas...")
    print("=" * 50)
    
    try:
        test_item_models()
        print()
        test_request_models()
        print()
        test_response_models()
        print()
        test_json_serialization()
        
        print("\n" + "=" * 50)
        print("🎉 All API schema tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
