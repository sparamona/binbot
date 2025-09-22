"""
Simple semantic search distance analysis for BinBot
Tests distance values to determine optimal cutoff thresholds
"""

import sys
import os
sys.path.append('.')

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

from session.session_manager import get_session_manager
from chat.function_wrappers import get_function_wrappers
from database.chromadb_client import get_chromadb_client


def test_search_distances():
    """Test search distances with known items to determine cutoffs"""
    
    print("🎯 Semantic Search Distance Analysis")
    print("=" * 50)
    
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
    
    # Test queries with different expected relevance levels
    test_queries = [
        {"query": "screwdriver", "expected": "Exact match", "relevant_items": ["Phillips screwdriver", "Flathead screwdriver"]},
        {"query": "phillips head tool", "expected": "Close semantic", "relevant_items": ["Phillips screwdriver"]},
        {"query": "writing tool", "expected": "Semantic match", "relevant_items": ["Pencil", "Pen"]},
        {"query": "cutting tool", "expected": "Semantic match", "relevant_items": ["Kitchen knife"]},
        {"query": "fruit", "expected": "Different category", "relevant_items": ["Banana"]},
        {"query": "computer equipment", "expected": "Different category", "relevant_items": ["Computer mouse"]},
        {"query": "elephant", "expected": "Unrelated", "relevant_items": []},
    ]
    
    print("\n🔍 Testing search distances...")
    print()
    
    # Get direct database access for distance analysis
    db_client = get_chromadb_client()
    from llm.embeddings import get_embedding_service
    embedding_service = get_embedding_service()
    
    distance_data = []
    
    for test in test_queries:
        query = test["query"]
        expected = test["expected"]
        relevant_items = test["relevant_items"]
        
        print(f"Query: '{query}' ({expected})")
        print("-" * 30)
        
        # Generate embedding and search
        query_embedding = embedding_service.generate_embedding(query)
        results = db_client._collection.query(
            query_embeddings=[query_embedding],
            n_results=len(test_items)  # Get all items to see full distance range
        )
        
        if results['distances'] and results['distances'][0]:
            for i, (item_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i]
                item_name = metadata['name']
                
                # Determine if this item is relevant
                is_relevant = any(rel in item_name for rel in relevant_items)
                relevance_marker = "🎯" if is_relevant else "  "
                
                print(f"  {relevance_marker} {item_name:20} → {distance:.4f}")
                
                # Collect data for analysis
                distance_data.append({
                    "query": query,
                    "query_type": expected,
                    "item": item_name,
                    "distance": distance,
                    "is_relevant": is_relevant
                })
        
        print()
    
    # Analyze distance patterns
    print("=" * 50)
    print("📊 DISTANCE ANALYSIS")
    print("=" * 50)
    
    # Group by relevance
    relevant_distances = [d["distance"] for d in distance_data if d["is_relevant"]]
    irrelevant_distances = [d["distance"] for d in distance_data if not d["is_relevant"]]
    
    if relevant_distances:
        print(f"Relevant items:")
        print(f"  Min distance:  {min(relevant_distances):.4f}")
        print(f"  Max distance:  {max(relevant_distances):.4f}")
        print(f"  Avg distance:  {sum(relevant_distances)/len(relevant_distances):.4f}")
    
    if irrelevant_distances:
        print(f"\nIrrelevant items:")
        print(f"  Min distance:  {min(irrelevant_distances):.4f}")
        print(f"  Max distance:  {max(irrelevant_distances):.4f}")
        print(f"  Avg distance:  {sum(irrelevant_distances)/len(irrelevant_distances):.4f}")
    
    # Find optimal cutoff
    all_distances = [d["distance"] for d in distance_data]
    if all_distances:
        print(f"\nOverall distance range: {min(all_distances):.4f} to {max(all_distances):.4f}")
    
    # Suggest cutoffs
    print("\n💡 CUTOFF RECOMMENDATIONS:")
    
    if relevant_distances and irrelevant_distances:
        max_relevant = max(relevant_distances)
        min_irrelevant = min(irrelevant_distances)
        
        if max_relevant < min_irrelevant:
            suggested_cutoff = (max_relevant + min_irrelevant) / 2
            print(f"  Perfect separation possible at: {suggested_cutoff:.4f}")
        else:
            print(f"  Overlap detected:")
            print(f"    Conservative cutoff (high precision): {max_relevant:.4f}")
            print(f"    Liberal cutoff (high recall): {min_irrelevant:.4f}")
    
    # General recommendations
    print(f"\n  General guidelines:")
    print(f"    < 0.5: Exact/very close matches")
    print(f"    0.5-1.0: Good semantic matches")
    print(f"    1.0-1.5: Weak semantic matches")
    print(f"    > 1.5: Likely irrelevant")
    
    print(f"\n  Recommended cutoffs:")
    print(f"    Strict (high precision): 0.8")
    print(f"    Balanced: 1.0")
    print(f"    Loose (high recall): 1.2")
    
    return distance_data


if __name__ == "__main__":
    print("🔍 BinBot Search Distance Analysis")
    print("Analyzing semantic search distances to determine optimal cutoff thresholds.")
    print()
    
    try:
        distance_data = test_search_distances()
        print("\n🎉 Analysis complete!")
        print("Use the cutoff recommendations to filter search results in your application.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
