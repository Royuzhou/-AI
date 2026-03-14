"""测试复杂 RAG 迭代配置加载"""
import sys
import yaml
sys.path.insert(0, 'd:/华南理工大学/软件工程概论/contract_revision_agent/UltraRAG/src')

print("=" * 60)
print("UltraRAG 复杂 RAG 迭代配置加载测试")
print("=" * 60)

# 测试 1：加载复杂配置
print("\n【测试 1】加载 complex_rag_iterative.yaml")
try:
    with open('examples/complex_rag_iterative.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print(f"✅ 成功加载配置文件")
    print(f"   - 服务器数量：{len(config.get('servers', {}))}")
    print(f"   - Pipeline 阶段数：{len(config.get('pipeline', []))}")
    print(f"   - 参数数量：{len(config.get('parameters', {}))}")
    print(f"   - 最大迭代次数：{config['parameters'].get('max_iterations', 'N/A')}")
except Exception as e:
    print(f"❌ 加载失败：{e}")

# 测试 2：加载简化配置
print("\n【测试 2】加载 simple_rag_iterative.yaml")
try:
    with open('examples/simple_rag_iterative.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print(f"✅ 成功加载配置文件")
    print(f"   - 服务器数量：{len(config.get('servers', {}))}")
    print(f"   - Pipeline 步骤数：{len(config.get('pipeline', []))}")
    print(f"   - 最大迭代次数：{config['parameters'].get('max_iterations', 'N/A')}")
except Exception as e:
    print(f"❌ 加载失败：{e}")

# 测试 3：验证服务器映射
print("\n【测试 3】验证服务器映射文件")
try:
    with open('examples/server/complex_rag_server.yaml', 'r', encoding='utf-8') as f:
        server_config = yaml.safe_load(f)
    print(f"✅ 成功加载服务器映射")
    print(f"   - 定义的服务器：{list(server_config.keys())}")
except Exception as e:
    print(f"❌ 加载失败：{e}")

# 测试 4：检查知识库配置
print("\n【测试 4】检查知识库配置")
try:
    import json
    with open('data/knowledge_base/kb_config.json', 'r', encoding='utf-8') as f:
        kb_config = json.load(f)
    print(f"✅ 知识库配置正常")
    print(f"   - Milvus URI: {kb_config['milvus'].get('uri', 'N/A')}")
    print(f"   - Token 配置：{'已设置' if kb_config['milvus'].get('token') else '未设置'}")
except Exception as e:
    print(f"❌ 配置检查失败：{e}")

print("\n" + "=" * 60)
print("配置加载测试完成！")
print("=" * 60)
print("\n下一步操作:")
print("1. 确保 kb_config.json 中的 API Key 已正确配置")
print("2. 运行：ultrarag run examples/complex_rag_iterative.yaml")
print("3. 或运行：ultrarag run examples/simple_rag_iterative.yaml")
