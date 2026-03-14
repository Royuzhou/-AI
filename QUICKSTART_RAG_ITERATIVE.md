# UltraRAG 复杂 RAG 迭代配置 - 快速开始指南

## 🎯 一句话概述
本配置实现了**智能多轮迭代的 RAG 系统**，通过自动检索→评估→优化循环，持续提升答案质量。

---

## ⚡ 30 秒快速开始

### 步骤 1：配置 API Key（首次使用）
打开 `data/knowledge_base/kb_config.json`，替换 Pinecone API Key：
```json
{
  "milvus": {
    "uri": "https://software-nnrl5hm.svc.aped-4627-b74a.pinecone.io",
    "token": "你的实际-API-Key"
  }
}
```

### 步骤 2：运行交互式启动器
```bash
conda activate ultrarag
python launch_rag_iterative.py
```

### 步骤 3：选择模式
- 输入 `1` → 完整配置（生产环境，5-10 分钟）
- 输入 `2` → 简化配置（开发测试，2-3 分钟）

---

## 📁 核心文件清单

| 文件 | 作用 | 必改 |
|------|------|------|
| `examples/complex_rag_iterative.yaml` | 完整 RAG 流程配置 | ❌ |
| `examples/simple_rag_iterative.yaml` | 简化 RAG 流程配置 | ❌ |
| `data/knowledge_base/kb_config.json` | 数据库连接配置 | ✅ |
| `launch_rag_iterative.py` | 交互式启动脚本 | ❌ |
| `docs/RAG_ITERATIVE_USAGE.md` | 详细使用文档 | ❌ |

---

## 🔧 关键参数速查

### 控制迭代次数
```yaml
parameters:
  max_iterations: 3  # 最多迭代 3 次
```

### 控制收敛标准
```yaml
iteration_control:
  convergence:
    threshold: 0.8  # 评估分数≥0.8 时停止
```

### 调整检索范围
```yaml
parameters:
  search_top_k: 10   # 每次检索返回 10 条
  rerank_top_k: 5    # 重排序后保留 5 条
```

---

## 🐛 常见问题速查

### Q1: API Key 在哪里获取？
A: 登录 [Pinecone Console](https://app.pinecone.io/) → API Keys → 复制

### Q2: 如何查看迭代过程？
A: 查看 `output/rag_iterations/` 目录下的日志文件

### Q3: 迭代一直不收敛怎么办？
A: 降低阈值：`convergence_threshold: 0.7`

### Q4: 如何加速流程？
A: 使用简化配置或减少迭代次数

---

## 📊 输出结果位置

```
output/
├── memory__complex_rag_时间戳.json    # 完整执行记录
└── rag_iterations/
    ├── iteration_1/
    │   ├── retrieval_results.json     # 第 1 轮检索结果
    │   └── evaluation_metrics.json    # 第 1 轮评估指标
    ├── iteration_2/
    │   └── ...
    ├── iteration_3/
    │   └── ...
    └── final_answer.json              # 最终答案
```

---

## 🚨 重要提示

1. **首次运行会下载模型**（约 5-10 分钟），请耐心等待
2. **确保网络连接稳定**（需要访问 Pinecone 云服务）
3. **API 调用会产生费用**，请注意用量监控
4. **中文文档已优化**，支持《民法典》等法律文件

---

## 💡 下一步建议

✅ **已完成**:
- [x] 复杂 RAG 迭代配置
- [x] 服务器映射定义
- [x] 启动脚本编写
- [x] 使用文档创建

🔄 **待完成**:
- [ ] 实现 `generate_query_rewrite` 工具
- [ ] 实现 `evaluate_retrieval` 工具
- [ ] 测试真实数据效果
- [ ] 调优超参数

---

## 📞 获取帮助

1. 查看详细文档：`docs/RAG_ITERATIVE_USAGE.md`
2. 运行测试脚本：`python test_rag_iterative_config.py`
3. 查看修改记录：`CHANGELOG_RAG_ITERATIVE.md`

---

**最后更新**: 2026-03-13  
**维护者**: Contract Revision Agent Team
