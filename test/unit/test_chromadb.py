"""
Tests for ChromaDB client functionality
"""

import sys
import uuid
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.chromadb_client import ChromaDBClient


def test_chromadb_basic_operations():
    """Test basic ChromaDB operations"""
    print("🧪 Testing ChromaDB basic operations...")
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override config for testing
        import config.settings
        original_path = config.settings.get_config().database_path
        config.settings.get_config()._config['database']['chromadb']['persist_directory'] = temp_dir
        
        try:
            # Initialize client
            client = ChromaDBClient()
            
            # Test data
            test_items = [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Phillips Screwdriver',
                    'description': 'Medium size Phillips head screwdriver',
                    'bin_id': 'A3',
                    'embedding': [0.1] * 384,  # Mock embedding
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'embedding_model': 'test-model',
                    'images': []
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Flathead Screwdriver',
                    'description': 'Small flathead screwdriver for electronics',
                    'bin_id': 'A3',
                    'embedding': [0.2] * 384,  # Mock embedding
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'embedding_model': 'test-model',
                    'images': []
                }
            ]
            
            # Test bulk add
            result = client.add_documents_bulk(test_items)
            assert result['success'], f"Add failed: {result.get('error')}"
            assert result['added_count'] == 2
            print("✅ Bulk add successful")
            
            # Test search
            search_result = client.search_documents("screwdriver", limit=5, min_relevance=0.0)
            assert search_result['success'], f"Search failed: {search_result.get('error')}"
            assert len(search_result['items']) >= 1
            print(f"✅ Search found {len(search_result['items'])} items")
            
            # Test bin contents
            bin_result = client.get_bin_contents('A3')
            assert bin_result['success'], f"Bin contents failed: {bin_result.get('error')}"
            assert bin_result['total_count'] == 2
            print(f"✅ Bin A3 contains {bin_result['total_count']} items")
            
            # Test item update
            item_id = test_items[0]['id']
            update_result = client.update_item_bin(item_id, 'B5')
            assert update_result['success'], f"Update failed: {update_result.get('error')}"
            print("✅ Item bin update successful")
            
            # Verify update
            bin_result_after = client.get_bin_contents('B5')
            assert bin_result_after['success']
            assert bin_result_after['total_count'] == 1
            print("✅ Item moved to new bin successfully")
            
            # Test item removal
            remove_result = client.remove_document(item_id)
            assert remove_result['success'], f"Remove failed: {remove_result.get('error')}"
            print("✅ Item removal successful")
            
            # Test audit log
            audit_entry = {
                'operation_id': str(uuid.uuid4()),
                'type': 'add',
                'item_ids': [item['id'] for item in test_items],
                'bin_ids': ['A3'],
                'description': 'Added test items to bin A3',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'test': True}
            }
            
            audit_result = client.add_audit_log_entry(audit_entry)
            assert audit_result['success'], f"Audit log failed: {audit_result.get('error')}"
            print("✅ Audit log entry successful")
            
        finally:
            # Restore original config
            config.settings.get_config()._config['database']['chromadb']['persist_directory'] = original_path


def test_chromadb_image_associations():
    """Test image association functionality"""
    print("🧪 Testing image associations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override config for testing
        import config.settings
        original_path = config.settings.get_config().database_path
        config.settings.get_config()._config['database']['chromadb']['persist_directory'] = temp_dir
        
        try:
            client = ChromaDBClient()
            
            # Add test item
            item_id = str(uuid.uuid4())
            test_item = {
                'id': item_id,
                'name': 'Test Item',
                'description': 'Item for image testing',
                'bin_id': 'TEST',
                'embedding': [0.1] * 384,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'embedding_model': 'test-model',
                'images': []
            }
            
            add_result = client.add_documents_bulk([test_item])
            assert add_result['success']
            
            # Add image association
            image_id = str(uuid.uuid4())
            image_result = client.add_image_to_item(item_id, image_id, set_as_primary=True)
            assert image_result['success'], f"Image association failed: {image_result.get('error')}"
            print("✅ Image association successful")
            
            # Verify image association
            bin_contents = client.get_bin_contents('TEST')
            assert bin_contents['success']
            item = bin_contents['items'][0]
            assert image_id in item['images']
            assert item['primary_image'] == image_id
            print("✅ Image association verified")
            
        finally:
            config.settings.get_config()._config['database']['chromadb']['persist_directory'] = original_path


if __name__ == "__main__":
    print("🧪 Testing ChromaDB client...")
    print("=" * 50)
    
    try:
        test_chromadb_basic_operations()
        print()
        test_chromadb_image_associations()
        
        print("\n" + "=" * 50)
        print("🎉 All ChromaDB tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
