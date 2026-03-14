"""
测试 Pinecone API 是否正常工作
"""
import sys
from pathlib import Path

# Add UltraRAG src to path
sys.path.insert(0, str(Path(__file__).parent / 'UltraRAG' / 'src'))

from ultrarag.ui.backend import pipeline_manager as pm

# 测试获取 Pinecone 客户端
print("Testing Pinecone client initialization...")
pc = pm._get_pinecone_client()

if pc:
    print("✓ Pinecone client initialized successfully")
    
    # 测试列出索引
    try:
        print("\nTesting list_indexes()...")
        indexes = pc.list_indexes()
        print(f"✓ Found {len(indexes)} indexes:")
        for idx in indexes:
            print(f"  - {idx.name}")
    except Exception as e:
        print(f"✗ Error listing indexes: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ Failed to initialize Pinecone client")
    print("  Possible reasons:")
    print("  1. Pinecone not configured in kb_config.json")
    print("  2. API key missing or invalid")
    print("  3. pinecone package not installed")