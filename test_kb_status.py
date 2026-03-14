"""Test KB status without Milvus"""
import sys
sys.path.insert(0, 'd:/华南理工大学/软件工程概论/contract_revision_agent/UltraRAG/ui/backend')

from pipeline_manager import list_kb_files, load_kb_config

print("Testing Knowledge Base status...")
print("=" * 60)

# Load config
config = load_kb_config()
print(f"\nConfiguration:")
print(f"  Use Vector DB: {config.get('use_vector_db', True)}")
print(f"  Milvus URI: {config.get('milvus', {}).get('uri', 'Not set')}")

# List files
try:
    result = list_kb_files()
    print(f"\n✅ Successfully loaded KB files!")
    print(f"  Raw files: {len(result['raw'])}")
    print(f"  Corpus files: {len(result['corpus'])}")
    print(f"  Chunk files: {len(result['chunks'])}")
    print(f"  Collections: {len(result['index'])}")
    print(f"  DB Status: {result['db_status']}")
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
