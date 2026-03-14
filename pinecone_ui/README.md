# 🎯 Pinecone 向量数据库管理界面

这是一个**独立的** Pinecone 云服务管理界面，与现有的 UltraRAG UI 分离，提供完整的向量数据库管理功能。

---

## ✨ 特性

### 🚀 独立运行
- ✅ 不依赖现有 UltraRAG UI
- ✅ 独立端口（5051）运行
- ✅ 直接连接 Pinecone 云服务

### 📊 核心功能
- **连接状态监控**: 实时显示 Pinecone 连接状态
- **索引管理**: 创建、删除、查看索引统计信息
- **文件上传**: 支持 PDF、DOCX、TXT 等格式
- **向量查询**: 可视化向量相似度搜索
- **配置管理**: 在线修改 Pinecone 配置

### 🎨 现代化 UI
- 渐变色设计
- 响应式布局
- 实时反馈
- 直观的操作界面

---

## 🚀 快速开始

### 1. 安装依赖

```bash
conda activate ultrarag
pip install flask pinecone
```

### 2. 配置 API Key

确保 `UltraRAG/data/knowledge_base/kb_config.json` 中已配置 Pinecone：

```json
{
  "pinecone": {
    "api_key": "pcsk_xxx...",
    "index_name": "legal-knowledge-base",
    "dimension": 768,
    "metric": "cosine"
  }
}
```

### 3. 启动服务

```bash
python run_pinecone_ui.py
```

或使用命令行：

```bash
cd d:\华南理工大学\软件工程概论\contract_revision_agent
python run_pinecone_ui.py
```

### 4. 访问界面

打开浏览器访问：**http://localhost:5051**

---

## 📖 功能说明

### 连接状态监控

页面加载时自动检测 Pinecone 连接状态：
- 🟢 **已连接**: 显示绿色状态灯和索引列表
- 🔴 **未连接**: 显示红色状态灯和错误信息
- 🟡 **错误**: 显示黄色状态灯和详细错误

### 索引管理

#### 创建索引
1. 点击"➕ 创建新索引"按钮
2. 输入索引名称、维度、度量方式
3. 点击"创建"

#### 查看统计
每个索引卡片显示：
- 向量维度
- 向量总数
- 索引填充度

#### 删除索引
⚠️ **警告**: 删除操作不可恢复！

### 文件上传

支持拖拽或点击上传：
1. 点击上传区域
2. 选择文件（PDF/DOCX/TXT）
3. 等待上传完成

上传的文件保存在：`pinecone_ui/data/uploads/`

### 向量查询

1. 选择要查询的索引
2. 输入查询向量（JSON 数组格式）
   ```json
   [0.1, 0.2, 0.3, ..., 0.768]
   ```
3. 设置返回数量（top_k）
4. 点击"🔍 查询"

结果显示：
- 相似度分数
- 向量 ID
- 元数据信息

### 配置管理

在线修改 Pinecone 配置：
- **API Key**: Pinecone API 密钥
- **索引名称**: 默认索引名称
- **向量维度**: 通常为 768
- **度量方式**: cosine/dotproduct/euclidean

修改后点击"💾 保存配置"，系统会自动重新连接。

---

## 🔧 技术架构

### 后端（Flask）

```
pinecone_ui/
├── app.py                 # Flask 应用主文件
├── templates/
│   └── index.html        # 前端页面
├── static/               # 静态资源（可选）
└── data/
    └── uploads/          # 上传文件存储
```

### API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/connection/status` | GET | 获取连接状态 |
| `/api/indexes` | GET | 列出所有索引 |
| `/api/indexes/create` | POST | 创建索引 |
| `/api/indexes/<name>/delete` | DELETE | 删除索引 |
| `/api/indexes/<name>/stats` | GET | 获取索引统计 |
| `/api/upload` | POST | 上传文件 |
| `/api/query` | POST | 向量查询 |
| `/api/upsert` | POST | 插入/更新向量 |
| `/api/config` | GET/POST | 读取/保存配置 |

### 前端技术

- **纯 HTML/CSS/JavaScript**: 无需构建工具
- **原生 Fetch API**: 异步请求
- **CSS Grid/Flexbox**: 响应式布局
- **CSS Animation**: 动态效果

---

## 🔗 与 UltraRAG UI 的区别

| 特性 | Pinecone UI (新) | UltraRAG UI (原有) |
|------|------------------|-------------------|
| **用途** | 专门的向量数据库管理 | 完整的 RAG 流程管理 |
| **端口** | 5051 | 5050 |
| **依赖** | 仅需 Pinecone | Milvus + Pinecone |
| **功能** | 索引/查询/配置 | Pipeline/知识库/RAG |
| **复杂度** | 轻量级 | 重量级 |
| **适用场景** | 快速管理向量库 | 完整 RAG 工作流 |

---

## 💡 使用建议

### 开发环境
- 使用 Free Tier 额度
- 创建测试索引（如 `dev-test`）
- 定期清理无用索引

### 生产环境
- 使用 Pod 规格
- 启用备份和监控
- 设置合适的配额限制

---

## 🐛 故障排查

### 问题 1: 无法连接到 Pinecone

**症状**: 显示红色"未连接"状态

**解决**:
1. 检查 API Key 是否正确
2. 确认网络连接正常
3. 登录 Pinecone Console 验证账户状态

### 问题 2: 文件上传失败

**症状**: 上传后显示错误

**解决**:
1. 检查 `pinecone_ui/data/uploads/` 目录是否存在
2. 确认文件大小不超过限制
3. 查看 Flask 日志获取详细错误

### 问题 3: 查询无结果

**症状**: 返回空结果列表

**解决**:
1. 确认索引中有向量数据
2. 检查查询向量维度是否匹配
3. 尝试调整 top_k 值

---

## 📚 相关资源

- [Pinecone 官方文档](https://docs.pinecone.io/)
- [Pinecone Python SDK](https://github.com/pinecone-io/pinecone-python-client)
- [Flask 文档](https://flask.palletsprojects.com/)

---

## 🎯 下一步计划

- [ ] 批量向量导入功能
- [ ] 索引备份和恢复
- [ ] 可视化向量分布
- [ ] 支持更多文件格式
- [ ] 集成 OCR 文本提取
- [ ] WebSocket 实时更新

---

## 📄 许可证

与主项目保持一致

---

**最后更新**: 2026-03-14  
**维护者**: Contract Revision Agent Team
