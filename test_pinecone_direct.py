"""
测试 Pinecone 云服务直接连接
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "ui" / "backend"))

from pinecone_manager import PineconeManager, load_pinecone_config, get_pinecone_client

print("=" * 70)
print("Pinecone 云服务直接连接测试")
print("=" * 70)

# 加载配置
print("\n【步骤 1】加载配置文件")
config = load_pinecone_config()
api_key = config.get("api_key", "")
index_name = config.get("index_name", "legal-knowledge-base")
dimension = config.get("dimension", 768)

if not api_key:
    print("❌ API Key 未配置")
    print(f"   请检查 kb_config.json 中的 pinecone.api_key")
    sys.exit(1)

print(f"✅ API Key 已加载：{api_key[:10]}...{api_key[-5:]}")
print(f"✅ 索引名称：{index_name}")
print(f"✅ 向量维度：{dimension}")

# 初始化客户端
print("\n【步骤 2】初始化 Pinecone 客户端")
try:
    pc = PineconeManager(api_key=api_key)
    print("✅ Pinecone 客户端初始化成功")
except Exception as e:
    print(f"❌ 初始化失败：{e}")
    sys.exit(1)

# 列出所有索引
print("\n【步骤 3】获取索引列表")
try:
    indexes = pc.list_indexes()
    if indexes:
        print(f"✅ 找到 {len(indexes)} 个索引:")
        for idx in indexes:
            print(f"   - {idx}")
    else:
        print("ℹ️  暂无索引，将自动创建")
except Exception as e:
    print(f"❌ 获取索引失败：{e}")
    sys.exit(1)

# 测试查询（如果索引存在）
if index_name in indexes:
    print(f"\n【步骤 4】测试索引 '{index_name}' 连接")
    try:
        stats = pc.get_index_stats(index_name)
        print(f"✅ 索引统计信息:")
        print(f"   - 维度：{stats.get('dimension', 'N/A')}")
        print(f"   - 向量总数：{stats.get('total_vector_count', 0)}")
        print(f"   - 索引填充度：{stats.get('index_fullness', 0):.2%}")
        
        # 测试查询（使用随机向量）
        import random
        test_vector = [random.random() for _ in range(dimension)]
        result = pc.query(index_name, vector=test_vector, top_k=1)
        print(f"✅ 测试查询成功，返回 {len(result.get('matches', []))} 条结果")
        
    except Exception as e:
        print(f"❌ 索引测试失败：{e}")
else:
    print(f"\n【步骤 4】索引 '{index_name}' 不存在")
    print("ℹ️  该索引将在首次使用时自动创建")

print("\n" + "=" * 70)
print("✅ Pinecone 连接测试完成！")
print("=" * 70)
print("\n下一步操作:")
print("1. 重启 UI 服务：python -m ultrarag.client show ui")
print("2. 访问 http://127.0.0.1:5050")
print("3. 在知识库页面查看 Pinecone 连接状态")
