# UltraRAG 复杂 RAG 迭代配置使用指南

## 📋 概述

本配置实现了**复杂的 RAG（检索增强生成）迭代流程**，支持多轮检索、重排序、质量评估和查询优化。

## 🎯 核心特性

### 1. **多阶段处理流水线**
```
Phase 1: 知识库构建 → Phase 2: 迭代检索 → Phase 3: 答案生成
```

### 2. **迭代优化机制**
- 初始检索 → 质量评估 → 查询重写 → 再次检索
- 最多支持 3 轮迭代，自动收敛到最优结果

### 3. **智能重排序**
- 使用 Cross-Encoder 模型对检索结果精细排序
- 从 top-k=10 压缩到 top-k=5，提升质量

### 4. **多维度评估**
- 检索评估：precision, recall, f1, ndcg
- 答案评估：相关性、准确性、完整性

---

## 🚀 快速开始

### 方式 1：使用完整配置（推荐用于生产环境）

```bash
# 激活环境
conda activate ultrarag

# 运行复杂 RAG 迭代流程
ultrarag run examples/complex_rag_iterative.yaml
```

### 方式 2：使用简化配置（推荐用于开发测试）

```bash
# 运行简化版 RAG 迭代
ultrarag run examples/simple_rag_iterative.yaml
```

---

## 📁 配置文件说明

### 主要配置文件

| 文件 | 用途 | 复杂度 |
|------|------|--------|
| `complex_rag_iterative.yaml` | 完整 RAG 迭代流程 | ⭐⭐⭐⭐⭐ |
| `simple_rag_iterative.yaml` | 简化 RAG 迭代流程 | ⭐⭐⭐ |
| `server/complex_rag_server.yaml` | 服务器工具映射 | - |
| `server/simple_rag_server.yaml` | 服务器工具映射（简化） | - |

### 关键参数说明

#### 语料处理参数
```yaml
parse_file_path: data/knowledge_base/raw/xxx.docx  # 输入文件路径
chunk_backend: sentence                              # 基于句子分块
chunk_size: 512                                      # 每块 512 字符
chunk_overlap: 50                                    # 块间重叠 50 字符
```

#### 检索参数
```yaml
search_top_k: 10                    # 初始检索返回 10 条
search_score_threshold: 0.5         # 分数阈值 0.5
collection_name: legal_knowledge    # 集合名称
```

#### 重排序参数
```yaml
rerank_top_k: 5                              # 重排序后保留 5 条
rerank_model: "cross-encoder/ms-marco-..."   # 重排序模型
```

#### 迭代控制参数
```yaml
max_iterations: 3              # 最多迭代 3 次
convergence_threshold: 0.8     # 收敛阈值 0.8
query_rewrite_strategy: "expansion"  # 查询扩展策略
```

---

## 🔄 迭代流程详解

### 第 1 轮：初始检索
```python
用户查询 → 向量检索 → 返回 top-10 → 重排序 → top-5
       ↓
   质量评估 (F1=0.65 < 0.8)
       ↓
   未收敛，继续迭代
```

### 第 2 轮：查询优化
```python
原始查询 + 反馈 → 查询扩展 → 新查询
       ↓
向量检索 (使用新查询) → 返回 top-10 → 重排序 → top-5
       ↓
   质量评估 (F1=0.78 < 0.8)
       ↓
   仍未收敛，继续迭代
```

### 第 3 轮：最终优化
```python
扩展查询 + 上下文增强 → 最终查询
       ↓
向量检索 → 返回 top-10 → 重排序 → top-5
       ↓
   质量评估 (F1=0.85 ≥ 0.8)
       ↓
   收敛！生成最终答案
```

---

## 🛠️ 自定义配置

### 修改迭代次数
```yaml
parameters:
  max_iterations: 5  # 改为 5 次迭代
```

### 更换生成模型
```yaml
parameters:
  generator_model: "Qwen/Qwen2.5-14B-Instruct"  # 更强的模型
```

### 调整收敛阈值
```yaml
iteration_control:
  convergence:
    threshold: 0.9  # 更严格的收敛标准
```

### 禁用重排序（加速流程）
```yaml
pipeline:
  - name: "iterative_retrieval"
    steps:
      - retriever.retriever_search
      # - reranker.rerank_documents  # 注释掉
      - evaluation.evaluate_retrieval
```

---

## 📊 输出结果

### 目录结构
```
output/rag_iterations/
├── iteration_1/
│   ├── retrieval_results.json    # 检索结果
│   ├── reranked_docs.json        # 重排序结果
│   └── evaluation_metrics.json   # 评估指标
├── iteration_2/
│   └── ...
├── iteration_3/
│   └── ...
└── final_answer.json             # 最终答案
```

### 日志查看
```bash
# 实时查看日志
tail -f output/rag_iterations/log.txt

# 可视化评估结果
python script/visualize_results.py output/rag_iterations
```

---

## ⚙️ 高级功能

### 1. 缓存策略
```yaml
cache:
  enabled: true           # 启用缓存
  cache_dir: .cache/ultrarag
  ttl_hours: 24          # 缓存 24 小时
```

### 2. 并行检索
```yaml
retriever:
  concurrency: 4         # 4 个并发检索任务
```

### 3. 自定义评估指标
```yaml
evaluation:
  metrics: 
    - "precision@5"
    - "recall@10"
    - "ndcg@5"
    - "mrr"  # 平均倒数排名
```

---

## 🔧 故障排查

### 问题 1：迭代不收敛
**症状**: 一直迭代，超过 max_iterations
**解决**: 
```yaml
# 降低收敛阈值
convergence_threshold: 0.7  # 从 0.8 降到 0.7
```

### 问题 2：检索质量低
**症状**: 评估分数始终低于阈值
**解决**:
```yaml
# 增加检索数量
search_top_k: 20  # 从 10 增加到 20

# 更换更强的嵌入模型
model_name_or_path: "BAAI/bge-large-zh-v1.5"
```

### 问题 3：内存不足
**症状**: OOM 错误
**解决**:
```yaml
# 减小分块大小
chunk_size: 256  # 从 512 降到 256

# 减少迭代次数
max_iterations: 2  # 从 3 降到 2
```

---

## 📈 性能优化建议

### 速度优先
```yaml
parameters:
  max_iterations: 1          # 只迭代 1 次
  search_top_k: 5            # 减少检索数量
  rerank_top_k: 3            # 减少重排序数量
  
pipeline:
  # 跳过重排序
  - retriever.retriever_search
  - generation.generate_response
```

### 质量优先
```yaml
parameters:
  max_iterations: 5          # 多次迭代
  search_top_k: 20           # 广泛检索
  rerank_top_k: 10           # 精细排序
  convergence_threshold: 0.9 # 严格收敛
  
pipeline:
  - retriever.retriever_search
  - reranker.rerank_documents
  - evaluation.evaluate_retrieval
  - generation.generate_query_rewrite
```

---

## 🎓 最佳实践

### 1. 开发阶段
- 使用 `simple_rag_iterative.yaml` 快速验证
- 关闭评估和重排序以加速调试
- 使用小样本数据测试

### 2. 测试阶段
- 启用所有评估指标
- 调整超参数（top_k, threshold 等）
- 记录每次实验的配置和结果

### 3. 生产部署
- 使用 `complex_rag_iterative.yaml`
- 启用缓存减少重复计算
- 监控迭代次数和收敛情况

---

## 📚 相关资源

- [UltraRAG 官方文档](https://github.com/OpenBMB/UltraRAG)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [RAG 技术综述](https://arxiv.org/abs/2312.10997)

---

## 💡 常见问题

**Q: 为什么需要迭代检索？**
A: 单次检索可能无法捕捉用户真实意图，通过多轮迭代可以逐步优化查询，提升检索质量。

**Q: 如何判断迭代是否应该停止？**
A: 当评估分数达到收敛阈值（如 F1≥0.8）或达到最大迭代次数时自动停止。

**Q: 可以自定义评估函数吗？**
A: 可以，在 `servers/evaluation/src/evaluation.py` 中实现自定义评估逻辑。

**Q: 支持中文吗？**
A: 完全支持，配置中已针对中文法律文档优化。

---

## 📞 技术支持

如有问题，请提交 Issue 或联系开发团队。
