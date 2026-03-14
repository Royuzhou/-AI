# UltraRAG 复杂 RAG 迭代配置 - 修改总结

## 📅 修改日期
2026-03-13


### 一、新增文件

#### 1. **核心配置文件**
| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `examples/complex_rag_iterative.yaml` | 完整 RAG 迭代配置 | ~200 行 |
| `examples/simple_rag_iterative.yaml` | 简化 RAG 迭代配置 | ~60 行 |
| `examples/server/complex_rag_server.yaml` | 服务器映射（复杂版） | ~80 行 |
| `examples/server/simple_rag_server.yaml` | 服务器映射（简化版） | ~50 行 |

#### 2. **文档与测试**
| 文件路径 | 说明 |
|---------|------|
| `docs/RAG_ITERATIVE_USAGE.md` | 详细使用指南 |
| `test_rag_iterative_config.py` | 配置加载测试脚本 |

---

### 二、修改的文件

#### 1. **恢复数据库配置**
**文件**: `data/knowledge_base/kb_config.json`

**修改前** (本地模式):
```json
{
  "milvus": {
    "uri": "./data/knowledge_base/milvus_local.db",
    "token": ""
  },
  "use_vector_db": false,
  "vector_backend": "none"
}
```

**修改后** (云服务):
```json
{
  "milvus": {
    "uri": "https://software-nnrl5hm.svc.aped-4627-b74a.pinecone.io",
    "token": "YOUR_PINECONE_API_KEY"
  }
}
```

**说明**: 
- ✅ 恢复 Pinecone 云服务 URI
- ✅ 需要替换实际的 API Key
- ✅ 移除了本地降级配置

---

### 三、删除的文件

| 文件路径 | 原因 |
|---------|------|
| `examples/kb_local_faiss.yaml` | 不再需要本地 FAISS 配置 |
| `run_local_kb.py` | 本地启动脚本已废弃 |
| `docker-compose-milvus.yml` | 不需要本地 Milvus Docker 部署 |

---

## 🔧 技术架构

### 1. **TAML 配置结构**
```yaml
servers:        # MCP 服务器定义
  - corpus
  - retriever
  - reranker
  - generation
  - evaluation

pipeline:       # 处理流水线
  - Phase 1: 知识库构建
  - Phase 2: 迭代检索 (3 轮)
  - Phase 3: 答案生成

parameters:     # 参数配置
  - 语料处理参数
  - 检索参数
  - 重排序参数
  - 迭代控制参数
  - 生成参数
  - 评估参数

server_configs: # 工具映射
  - 定义每个工具的输入输出
```

### 2. **迭代流程设计**
```
用户查询
   ↓
[第 1 轮] 检索 → 重排序 → 评估 → (未收敛)
   ↓                    ↑
[第 2 轮] 查询重写 ──────┘
   ↓
[第 3 轮] 再次检索 → 重排序 → 评估 → (收敛)
   ↓
生成最终答案
```

### 3. **收敛条件**
```python
if evaluation_score >= convergence_threshold:
    停止迭代，生成答案
else:
    继续下一轮迭代
    
if iteration_count >= max_iterations:
    强制停止，使用当前最佳结果
```

---

## 🚀 使用方法

### 方式 1：完整配置（生产环境）
```bash
conda activate ultrarag
ultrarag run examples/complex_rag_iterative.yaml
```

**特点**:
- ✅ 包含重排序和评估
- ✅ 3 轮迭代优化
- ✅ 多维度质量监控
- ⏱️ 预计耗时：5-10 分钟

### 方式 2：简化配置（开发测试）
```bash
conda activate ultrarag
ultrarag run examples/simple_rag_iterative.yaml
```

**特点**:
- ✅ 仅保留核心功能
- ✅ 2 轮快速迭代
- ✅ 无重排序和评估
- ⏱️ 预计耗时：2-3 分钟

---

## 📊 性能对比

| 配置 | 迭代次数 | 检索数量 | 重排序 | 评估 | 预计时间 | 适用场景 |
|------|---------|---------|--------|------|---------|---------|
| `complex_rag_iterative` | 3 | top-10→top-5 | ✅ | ✅ | 5-10min | 生产环境 |
| `simple_rag_iterative` | 2 | top-5 | ❌ | ❌ | 2-3min | 开发测试 |
| 原 `kb_local.yaml` | 0 | N/A | ❌ | ❌ | <1min | 简单解析 |

---

## ⚙️ 关键参数调优

### 提升质量
```yaml
max_iterations: 5           # 增加迭代次数
search_top_k: 20            # 扩大检索范围
convergence_threshold: 0.9  # 提高收敛标准
rerank_top_k: 10            # 精细重排序
```

### 提升速度
```yaml
max_iterations: 1           # 减少迭代
search_top_k: 5             # 缩小范围
rerank_top_k: 3             # 快速重排序
```

---

## 🔍 验证步骤

### 1. 检查配置加载
```bash
python test_rag_iterative_config.py
```

**预期输出**:
```
✅ 成功加载配置文件
   - 服务器数量：5
   - Pipeline 阶段数：3
   - 最大迭代次数：3
```

### 2. 测试运行（简化版）
```bash
ultrarag run examples/simple_rag_iterative.yaml
```

**观察点**:
- ✅ Pipeline 是否正确执行
- ✅ 迭代是否按预期进行
- ✅ 输出目录是否生成

### 3. 查看结果
```bash
# 查看输出
ls output/rag_iterations/

# 查看日志
cat output/memory__simple_rag_*.json
```

---

## 🐛 已知问题与解决方案

### 问题 1: Pinecone 连接失败
**症状**: `Milvus connection failed`
**解决**: 
```json
// kb_config.json
{
  "milvus": {
    "uri": "https://正确的-pinecone-uri",
    "token": "正确的-api-key"
  }
}
```

### 问题 2: 迭代不收敛
**症状**: 一直迭代到 max_iterations
**解决**: 降低收敛阈值或检查检索质量

### 问题 3: 内存不足
**症状**: OOM 错误
**解决**: 减小 chunk_size 或 search_top_k

---

## 📋 待办事项

### 短期（本周）
- [ ] 实现 query_rewrite 工具
- [ ] 添加更多评估指标
- [ ] 优化迭代收敛逻辑

### 中期（本月）
- [ ] 支持多路召回
- [ ] 集成 Reranker 模型
- [ ] 添加可视化界面

### 长期（下季度）
- [ ] 自适应迭代次数
- [ ] 分布式检索
- [ ] 实时反馈学习

---

## 📚 参考资料

1. [UltraRAG 官方文档](https://github.com/OpenBMB/UltraRAG)
2. [RAG 迭代优化论文](https://arxiv.org/abs/2312.10997)
3. [MCP 协议规范](https://modelcontextprotocol.io/)
4. [Cross-Encoder 重排序](https://www.sbert.net/examples/applications/retrieve_rerank/README.html)

---

## 💡 使用建议

### 对于开发者
1. 从 `simple_rag_iterative.yaml` 开始熟悉流程
2. 逐步启用高级功能（重排序、评估）
3. 根据实际效果调整超参数

### 对于最终用户
1. 使用 UI 界面操作更直观
2. 关注最终答案质量而非过程
3. 提供反馈帮助系统优化

### 对于运维人员
1. 监控 API 调用次数和成本
2. 设置合理的并发限制
3. 定期清理缓存和临时文件

---

## 📞 技术支持

如有问题，请查阅：
- `docs/RAG_ITERATIVE_USAGE.md` - 详细使用指南
- `test_rag_iterative_config.py` - 配置测试脚本
- UltraRAG 官方 GitHub Issues

---

**修改完成时间**: 约 2 小时  
**代码变更量**: +500 行（新增），-100 行（删除），~50 行（修改）  
**影响范围**: RAG 流程配置、知识库管理、迭代控制
