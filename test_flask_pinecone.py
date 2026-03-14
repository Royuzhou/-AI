"""
直接测试 Flask 应用的 Pinecone 路由
"""
import sys
from pathlib import Path

# Add both UltraRAG/src and UltraRAG to path
ultrarag_src = Path(__file__).parent / 'UltraRAG' / 'src'
ultrarag_root = Path(__file__).parent / 'UltraRAG'
sys.path.insert(0, str(ultrarag_src))
sys.path.insert(0, str(ultrarag_root))

# Import and create app
from ultrarag.ui.backend.app import create_app

app = create_app(admin_mode=True)

# Check if pinecone routes are registered
print("Checking Pinecone routes...")
pinecone_routes = [rule for rule in app.url_map.iter_rules() if 'pinecone' in str(rule)]

if pinecone_routes:
    print(f"✓ Found {len(pinecone_routes)} Pinecone routes:")
    for route in pinecone_routes:
        print(f"  {route.methods} {route.rule}")
else:
    print("✗ No Pinecone routes found!")
    
# Test the route directly with Flask test client
print("\nTesting /api/kb/pinecone/indexes endpoint...")
with app.test_client() as client:
    response = client.get('/api/kb/pinecone/indexes')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")