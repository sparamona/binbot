"""
Simple ChromaDB client test
"""

import sys
sys.path.append('.')

from database.chromadb_client import ChromaDBClient

def test_chromadb_initialization():
    """Test ChromaDB client initialization"""
    print("🧪 Testing ChromaDB initialization...")
    
    try:
        client = ChromaDBClient()
        print("✅ ChromaDB client initialized successfully")
        
        # Test that collections are created
        assert client.inventory_collection is not None
        print("✅ Inventory collection created")
        
        # Test empty search
        result = client.search_documents("test", limit=1, min_relevance=0.0)
        assert result['success']
        print(f"✅ Search works (found {len(result['items'])} items)")
        
        # Test empty bin contents
        bin_result = client.get_bin_contents('NONEXISTENT')
        assert bin_result['success']
        assert bin_result['total_count'] == 0
        print("✅ Bin contents query works")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing ChromaDB client (simple)...")
    print("=" * 50)
    
    success = test_chromadb_initialization()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ChromaDB client test passed!")
    else:
        print("❌ ChromaDB client test failed!")
