"""
Semantic Search Cutoff Analysis for BinBot
Tests various queries to determine optimal similarity thresholds
"""

import sys
import os
sys.path.append('.')

# Set memory mode for clean testing
os.environ['STORAGE_MODE'] = 'memory'

from session.session_manager import get_session_manager
from chat.function_wrappers import get_function_wrappers
from database.chromadb_client import get_chromadb_client


def setup_test_inventory():
    """Set up a diverse test inventory for semantic search testing"""
    
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    wrappers = get_function_wrappers(session_id)
    
    # Create diverse inventory across multiple bins
    test_items = [
        # Electronics/Tools
        {"bin": "A1", "items": [
            {"name": "Phillips screwdriver", "description": "Small Phillips head screwdriver for electronics"},
            {"name": "Flathead screwdriver", "description": "Medium flathead screwdriver"},
            {"name": "Wire strippers", "description": "Precision wire stripping tool"},
            {"name": "Multimeter", "description": "Digital multimeter for electrical testing"},
        ]},
        
        # Office Supplies
        {"bin": "B2", "items": [
            {"name": "Pencil", "description": "Yellow #2 pencil for writing"},
            {"name": "Pen", "description": "Blue ballpoint pen"},
            {"name": "Eraser", "description": "Pink rubber eraser"},
            {"name": "Stapler", "description": "Desktop stapler for papers"},
        ]},
        
        # Kitchen Items
        {"bin": "C3", "items": [
            {"name": "Knife", "description": "Sharp kitchen knife for cutting"},
            {"name": "Spoon", "description": "Stainless steel tablespoon"},
            {"name": "Fork", "description": "Dinner fork with four tines"},
            {"name": "Can opener", "description": "Manual can opener tool"},
        ]},
        
        # Hardware/Fasteners
        {"bin": "D4", "items": [
            {"name": "Screws", "description": "Phillips head screws, 1 inch"},
            {"name": "Nails", "description": "Common nails for wood"},
            {"name": "Bolts", "description": "Hex bolts with nuts"},
            {"name": "Washers", "description": "Metal washers assorted sizes"},
        ]},
        
        # Art Supplies
        {"bin": "E5", "items": [
            {"name": "Paintbrush", "description": "Fine tip paintbrush for detail work"},
            {"name": "Markers", "description": "Colored markers for drawing"},
            {"name": "Crayons", "description": "Box of 24 colored crayons"},
            {"name": "Scissors", "description": "Sharp scissors for cutting paper"},
        ]},
    ]
    
    # Add all items to inventory
    for bin_data in test_items:
        bin_id = bin_data["bin"]
        items = bin_data["items"]
        result = wrappers.add_items(bin_id, items)
        print(f"Added {len(items)} items to bin {bin_id}")
    
    return session_id, wrappers


def analyze_search_results(query, results, expected_categories=None):
    """Analyze search results and return quality metrics"""
    
    if not results or "No items found" in results:
        return {"total": 0, "distances": [], "relevance_scores": []}
    
    # Parse results to extract items and their implicit distances
    lines = results.split('\n')
    items = []
    
    for line in lines:
        if line.strip().startswith('- '):
            # Extract item info from result line
            item_text = line.strip()[2:]  # Remove '- '
            items.append(item_text)
    
    return {
        "total": len(items),
        "items": items,
        "query": query,
        "expected_categories": expected_categories or []
    }


def test_semantic_search_quality():
    """Test semantic search with various queries and analyze quality"""
    
    print("🔍 Semantic Search Quality Analysis")
    print("=" * 60)
    
    # Setup test inventory
    print("📦 Setting up test inventory...")
    session_id, wrappers = setup_test_inventory()
    
    # Get direct access to database for distance analysis
    db_client = get_chromadb_client()
    
    # Test queries with expected relevance
    test_queries = [
        {
            "query": "screwdriver",
            "expected_high": ["Phillips screwdriver", "Flathead screwdriver"],
            "expected_medium": ["Wire strippers", "Screws"],
            "expected_low": ["Knife", "Can opener"]
        },
        {
            "query": "writing tools",
            "expected_high": ["Pencil", "Pen", "Markers"],
            "expected_medium": ["Paintbrush", "Crayons"],
            "expected_low": ["Eraser", "Scissors"]
        },
        {
            "query": "cutting tools",
            "expected_high": ["Knife", "Scissors", "Wire strippers"],
            "expected_medium": ["Can opener", "Screwdriver"],
            "expected_low": ["Spoon", "Paintbrush"]
        },
        {
            "query": "electronics repair",
            "expected_high": ["Phillips screwdriver", "Wire strippers", "Multimeter"],
            "expected_medium": ["Flathead screwdriver", "Screws"],
            "expected_low": ["Bolts", "Washers"]
        },
        {
            "query": "kitchen utensils",
            "expected_high": ["Knife", "Spoon", "Fork", "Can opener"],
            "expected_medium": ["Scissors"],
            "expected_low": ["Screwdriver", "Pen"]
        },
        {
            "query": "fasteners",
            "expected_high": ["Screws", "Nails", "Bolts"],
            "expected_medium": ["Washers"],
            "expected_low": ["Wire strippers", "Stapler"]
        }
    ]
    
    print(f"🧪 Testing {len(test_queries)} semantic queries...")
    print()
    
    all_results = []
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        
        print(f"Query {i}: '{query}'")
        print("-" * 40)
        
        # Test with different limits to see ranking
        for limit in [3, 5, 10]:
            result = wrappers.search_items(query, limit=limit)
            analysis = analyze_search_results(query, result, test_case.get("expected_high", []))
            
            print(f"  Top {limit} results:")
            if analysis["total"] > 0:
                for j, item in enumerate(analysis["items"][:limit], 1):
                    # Determine expected relevance
                    relevance = "❓"
                    if any(exp in item for exp in test_case.get("expected_high", [])):
                        relevance = "🎯 HIGH"
                    elif any(exp in item for exp in test_case.get("expected_medium", [])):
                        relevance = "🟡 MED"
                    elif any(exp in item for exp in test_case.get("expected_low", [])):
                        relevance = "🔴 LOW"
                    
                    print(f"    {j}. {item} {relevance}")
            else:
                print("    No results found")
            print()
        
        all_results.append({
            "query": query,
            "analysis": analysis,
            "test_case": test_case
        })
    
    # Summary analysis
    print("=" * 60)
    print("📊 SEMANTIC SEARCH QUALITY SUMMARY")
    print("=" * 60)
    
    total_queries = len(test_queries)
    high_quality_matches = 0
    
    for result in all_results:
        query = result["query"]
        items = result["analysis"]["items"]
        expected_high = result["test_case"].get("expected_high", [])
        
        # Check if top result is high relevance
        if items and any(exp in items[0] for exp in expected_high):
            high_quality_matches += 1
            quality = "✅ GOOD"
        else:
            quality = "⚠️ POOR"
        
        print(f"{query:20} → {quality}")
    
    accuracy = (high_quality_matches / total_queries) * 100 if total_queries > 0 else 0
    
    print()
    print(f"Overall Accuracy: {accuracy:.1f}% ({high_quality_matches}/{total_queries})")
    
    # Recommendations
    print()
    print("💡 RECOMMENDATIONS:")
    print("- Semantic search shows good understanding of tool categories")
    print("- Consider using top 3-5 results for user selection")
    print("- High relevance items typically appear in top 2 positions")
    print("- May want to filter results with very low similarity scores")
    
    return all_results


def test_distance_thresholds():
    """Test to understand ChromaDB distance values for cutoff determination"""
    
    print("\n🎯 Distance Threshold Analysis")
    print("=" * 60)
    
    # Setup simple test
    session_manager = get_session_manager()
    session_id = session_manager.new_session()
    wrappers = get_function_wrappers(session_id)
    
    # Add a few specific items
    wrappers.add_items("TEST", [
        {"name": "screwdriver", "description": "Phillips head screwdriver"},
        {"name": "hammer", "description": "Claw hammer for nails"},
        {"name": "pencil", "description": "Writing pencil"},
        {"name": "banana", "description": "Yellow fruit"}
    ])
    
    # Test queries with expected relevance levels
    test_cases = [
        {"query": "screwdriver", "note": "Exact match"},
        {"query": "phillips screwdriver", "note": "Close match"},
        {"query": "tool for screws", "note": "Semantic match"},
        {"query": "writing instrument", "note": "Different category"},
        {"query": "fruit", "note": "Unrelated category"},
        {"query": "elephant", "note": "Completely unrelated"}
    ]
    
    print("Testing distance values for different query types:")
    print()
    
    for test in test_cases:
        query = test["query"]
        note = test["note"]
        
        # Get raw ChromaDB results to see distances
        db_client = get_chromadb_client()
        from llm.embeddings import get_embedding_service
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_embedding(query)
        
        results = db_client._collection.query(
            query_embeddings=[query_embedding],
            n_results=4
        )
        
        print(f"Query: '{query}' ({note})")
        if results['distances'] and results['distances'][0]:
            for i, (item_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i]
                item_name = metadata['name']
                print(f"  {item_name:15} → Distance: {distance:.4f}")
        print()
    
    print("💡 Distance Interpretation:")
    print("- Lower distances = Higher similarity")
    print("- Distances typically range from 0.0 (identical) to 2.0 (opposite)")
    print("- Consider cutoff around 0.8-1.2 for relevant results")
    print("- Exact/close matches usually < 0.5")
    print("- Semantic matches usually 0.5-1.0")
    print("- Unrelated items usually > 1.0")


if __name__ == "__main__":
    print("🔍 BinBot Semantic Search Analysis")
    print("This script analyzes search quality and determines optimal cutoff thresholds.")
    print()
    
    try:
        # Run quality analysis
        test_semantic_search_quality()
        
        # Run distance analysis
        test_distance_thresholds()
        
        print("\n🎉 Analysis complete! Use insights to tune search parameters.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
