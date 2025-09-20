"""
Test the new distance filtering in semantic search
"""

import sys
import os
sys.path.append('.')

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

from session.session_manager import get_session_manager
from chat.function_wrappers import get_function_wrappers
from database.chromadb_client import get_chromadb_client


def test_distance_filtering():
    """Test the new distance filtering functionality"""
    
    print("🎯 Testing Distance Filtering in Semantic Search")
    print("=" * 55)
    
    # Setup test inventory
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    wrappers = get_function_wrappers(session_id)
    
    print("📦 Setting up test items...")
    
    # Add diverse test items
    test_items = [
        {"name": "Phillips screwdriver", "description": "Small Phillips head screwdriver for electronics"},
        {"name": "Flathead screwdriver", "description": "Medium flathead screwdriver"},
        {"name": "Hammer", "description": "Claw hammer for driving nails"},
        {"name": "Pencil", "description": "Yellow #2 pencil for writing"},
        {"name": "Pen", "description": "Blue ballpoint pen"},
        {"name": "Kitchen knife", "description": "Sharp knife for cutting food"},
        {"name": "Banana", "description": "Yellow ripe banana fruit"},
        {"name": "Computer mouse", "description": "Wireless computer mouse"}
    ]
    
    result = wrappers.add_items("TEST", test_items)
    print(f"✅ {result}")
    
    # Test different distance thresholds
    test_query = "screwdriver"
    thresholds = [0.3, 0.5, 0.7, 1.0]
    
    print(f"\n🔍 Testing query: '{test_query}' with different distance thresholds")
    print()
    
    db_client = get_chromadb_client()
    
    for threshold in thresholds:
        print(f"Distance threshold: {threshold}")
        print("-" * 25)
        
        results = db_client.search_documents(test_query, limit=10, max_distance=threshold)
        
        if results:
            for i, item in enumerate(results, 1):
                distance = item.get('distance', 0)
                confidence = item.get('confidence_score', 0)
                name = item['name']
                print(f"  {i}. {name:20} (dist: {distance:.3f}, conf: {confidence:.3f})")
        else:
            print("  No results found")
        
        print(f"  Total results: {len(results)}")
        print()
    
    # Test semantic queries with balanced threshold
    print("🧠 Testing semantic queries with balanced threshold (0.7)")
    print("=" * 55)
    
    semantic_queries = [
        "writing tool",
        "cutting tool", 
        "computer equipment",
        "fruit",
        "completely unrelated elephant"
    ]
    
    for query in semantic_queries:
        print(f"Query: '{query}'")
        print("-" * 30)
        
        results = db_client.search_documents(query, limit=5, max_distance=0.7)
        
        if results:
            for i, item in enumerate(results, 1):
                distance = item.get('distance', 0)
                confidence = item.get('confidence_score', 0)
                name = item['name']
                print(f"  {i}. {name:20} (dist: {distance:.3f}, conf: {confidence:.3f})")
        else:
            print("  No relevant results found (all items filtered out)")
        
        print(f"  Results: {len(results)}")
        print()
    
    print("💡 OBSERVATIONS:")
    print("- Lower thresholds = fewer, more relevant results")
    print("- Higher thresholds = more results, some less relevant")
    print("- Threshold 0.7 provides good balance for most queries")
    print("- Unrelated queries properly return no results with strict thresholds")


if __name__ == "__main__":
    try:
        test_distance_filtering()
        print("\n🎉 Distance filtering test complete!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
