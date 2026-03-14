# UltraRAG Pinecone 云服务直接连接配置指南

## 🎯 概述

UltraRAG 现已支持**直接连接 Pinecone 云服务**，无需通过 Milvus SDK。这样可以：
- ✅ 直接使用 Pinecone 原生 API
- ✅ 避免 Milvus SDK 兼容性问题
- ✅ 享受 Pinecone 全部功能特性

---

## 📦 安装依赖

已自动安装最新版的 `pinecone` 包（v8.1.0）

```bash
pip install pinecone
```

---

## ⚙️ 配置文件

### kb_config.json

```json
{
  "pinecone": {
    "api_key": "pcsk_6kEbj2_TgfUfZHQsnbV5XLmm1tX79wKdmU8CAGBWuvasNNVWogLSxPQxxgaf4id2sxjNsb",
    "index_name": "legal-knowledge-base",
    "dimension": 768,
    "metric": "cosine",
    "cloud": "aws",
    "region": "us-east-1"
  },
  "milvus": {
    "uri": "",
    "token": ""
  }
}
```

**关键字段说明**:
- `api_key`: Pinecone API Key（必填）
- `index_name`: 索引名称（可选，默认 legal-knowledge-base）
- `dimension`: 向量维度（可选，默认 768）
- `metric`: 相似度度量（cosine/dotproduct/euclidean）
- `cloud/region`: 云服务商和区域

---

## 🔧 新增模块

### pinecone_manager.py

位于 `ui/backend/pinecone_manager.py`，提供：

#### **PineconeManager 类**
```python
from pinecone_manager import PineconeManager

# 初始化
pc = PineconeManager(api_key="your-api-key")

# 列出索引
indexes = pc.list_indexes()

# 获取统计信息
stats = pc.get_index_stats("my-index")

# 查询
results = pc.query(
    index_name="my-index",
    vector=[0.1, 0.2, ...],
    top_k=10
)

# 插入向量
pc.upsert("my-index", vectors=[
    ("id1", [0.1, 0.2, ...], {"text": "..."}),
    ("id2", [0.3, 0.4, ...], {"text": "..."})
])
```

#### **工具函数**
```python
# 加载配置
config = load_pinecone_config()

# 获取客户端
client = get_pinecone_client()
```

---

## 🧪 测试连接

运行测试脚本验证连接：

```bash
python test_pinecone_direct.py
```

**预期输出**:
```
✅ API Key 已加载：pcsk_6kEbj...xjNsb
✅ Pinecone 客户端初始化成功
✅ 找到 1 个索引:
   - software
✅ Pinecone 连接测试完成！
```

---

## 🌐 UI 界面

访问 http://127.0.0.1:5050

### 知识库页面状态

在知识库页面，您应该看到：
- **数据库类型**: Pinecone
- **连接状态**: connected
- **索引列表**: 显示所有可用的 Pinecone 索引

---

## 📊 当前索引状态

根据测试结果，您的 Pinecone 账户中已有：
- ✅ 索引：**software**
- ℹ️  将创建：**legal-knowledge-base**（首次使用时自动创建）

---

## 🔄 与 RAG 迭代集成的区别

### 之前（Milvus 模式）
```yaml
pipeline:
  - retriever.retriever_init    # 使用 Milvus SDK
  - retriever.retriever_index   # 构建 Milvus 索引
```

### 现在（Pinecone 直连模式）
```yaml
# 使用 Pinecone 原生 API
from pinecone_manager import PineconeManager

pc = PineconeManager(api_key=...)
pc.create_index("legal-knowledge-base", dimension=768)
pc.upsert(...)
```

---

## 💡 使用建议

### 开发环境
- ✅ 使用 Pinecone Free Tier（免费额度）
- ✅ 索引名称加上前缀区分项目（如 `dev-legal-kb`）

### 生产环境
- ✅ 使用 Pod 规格（性能更好）
- ✅ 配置备份和监控
- ✅ 设置合适的索引规格

---

## 🐛 故障排查

### 问题 1: Package renamed 错误
**症状**: `Exception: The official Pinecone python package has been renamed...`

**解决**: 
```bash
pip uninstall pinecone-client
pip install pinecone
```

### 问题 2: API Key 无效
**症状**: Authentication failed

**解决**: 
- 检查 kb_config.json 中的 api_key 是否正确
- 登录 https://app.pinecone.io/ 验证密钥
- 确认项目状态正常

### 问题 3: 索引不存在
**症状**: Index not found

**解决**:
- 索引会在首次 upsert 时自动创建
- 或手动创建：`pc.create_index("my-index", dimension=768)`

---

## 📚 API 参考

### PineconeManager 方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `list_indexes()` | 列出所有索引 | - |
| `get_index_stats(name)` | 获取索引统计 | index_name |
| `query(index, vector, top_k)` | 向量查询 | index_name, vector, top_k |
| `upsert(index, vectors)` | 插入向量 | index_name, vectors 列表 |
| `create_index(name, dimension)` | 创建索引 | name, dimension, metric |
| `delete_index(name)` | 删除索引 | index_name |

---

## 🎓 下一步

1. **上传文档到知识库**
   - 将合同/PDF 放到 `data/knowledge_base/raw/`
   - 在 UI 中执行构建流程

2. **测试检索功能**
   - 使用复杂的 RAG 迭代配置
   - 观察 Pinecone 索引的使用情况

3. **监控用量**
   - 登录 Pinecone Console 查看 API 调用
   - 优化向量数量和查询频率

---

## 🔗 相关资源

- [Pinecone Python SDK](https://github.com/pinecone-io/pinecone-python-client)
- [Pinecone Docs](https://docs.pinecone.io/)
- [UltraRAG 文档](docs/RAG_ITERATIVE_USAGE.md)

---

**最后更新**: 2026-03-14  
**维护者**: Contract Revision Agent Team
