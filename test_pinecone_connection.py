"""Test Pinecone connection using the actual backend code"""
import sys
sys.path.insert(0, 'd:/华南理工大学/软件工程概论/contract_revision_agent/UltraRAG/ui/backend')

from pipeline_manager import load_kb_config, _get_milvus_client

# Load configuration
config = load_kb_config()
print("Current Configuration:")
print(f"URI: {config['milvus'].get('uri', 'Not set')}")
print(f"Token: {config['milvus'].get('token', 'Not set')[:10]}..." if config['milvus'].get('token') else "No token")
print()

# Test connection
try:
    client = _get_milvus_client()
    print("✅ Connection successful!")
    
    # Try to list collections
    collections = client.list_collections()
    print(f"Collections: {collections}")
    
    client.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
