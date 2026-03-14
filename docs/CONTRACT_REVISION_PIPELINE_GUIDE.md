# 合同修订 Pipeline 使用指南

## 📋 概述

本指南介绍如何在 UltraRAG UI 中配置和使用合同修订 pipeline，实现智能化的合同法律条款识别与修订功能。

---

## 🎯 Pipeline 架构

合同修订流程包含 4 个核心步骤:

```
合同文档 → 文档提取 → 法律条款识别 → 法律条文检索 → 合同修订生成
               ↓              ↓              ↓              ↓
           (PDF/Word+OCR)  (Qwen3-Max)   (Pinecone)    (Qwen3-Max)
```

---

## 📁 文件结构

```
UltraRAG/
├── examples/
│   ├── contract_revision_pipeline.yaml       # 完整 pipeline 配置
│   ├── contract_revision_demo.yaml           # 简化演示配置
│   └── server/
│       └── contract_revision_server.yaml     # 服务定义
└── servers/
    ├── doc_extractor/                        # 文档提取服务
    │   ├── src/doc_extractor.py
    │   └── parameter.yaml
    ├── legal_identifier/                     # 法律条款识别服务
    │   ├── src/legal_identifier.py
    │   └── parameter.yaml
    ├── legal_retriever/                      # 法律条文检索服务
    │   ├── src/legal_retriever.py
    │   └── parameter.yaml
    └── contract_revision/                    # 合同修订服务
        ├── src/contract_revision.py
        └── parameter.yaml
```

---

## 🚀 快速开始

### 方式一：使用简化演示版 (推荐初次使用)

1. **启动 UltraRAG UI (Admin 模式)**
   ```bash
   python -m ultrarag.client show ui --admin
   ```

2. **访问 UI**
   - 打开浏览器：http://localhost:5050

3. **选择 Pipeline**
   - 在 Pipeline 下拉框中选择 `contract_revision_demo`

4. **运行测试**
   - 点击 Run 按钮执行
   - 查看输出结果

---

### 方式二：使用完整版 Pipeline

#### 步骤 1: 安装依赖

```bash
pip install openai pinecone sentence-transformers PyPDF2 python-docx paddlepaddle paddleocr
```

#### 步骤 2: 配置 API 密钥

编辑各服务的参数文件:

**servers/legal_identifier/parameter.yaml**
```yaml
model: qwen3-max
api_key: 你的 DashScope API Key
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

**servers/legal_retriever/parameter.yaml**
```yaml
pinecone_api_key: 你的 Pinecone API Key
pinecone_index: software
top_k: 3
similarity_threshold: 0.6
```

**servers/contract_revision/parameter.yaml**
```yaml
model: qwen3-max
api_key: 你的 DashScope API Key
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 步骤 3: 准备合同文档

将合同文件放入 `data/contracts/` 目录。

#### 步骤 4: 在 UI 中运行

1. 选择 `contract_revision_pipeline`
2. 配置输入参数:
   - `file_path`: 合同文件路径
   - `use_ocr`: 是否对 PDF 使用 OCR
3. 点击 Run 执行

---

## 🔧 详细配置说明

### 1. 文档提取服务 (`doc_extractor`)

**功能**: 从 PDF/Word 文档提取文本，支持 OCR

**参数**:
- `ocr_lang`: OCR 识别语言 (默认：ch)
- `use_textline_orientation`: 文本行方向识别 (默认：true)
- `pdf_text_threshold`: PDF 文本提取阈值 (默认：50)

**工具**:
- `extract_text(file_path, use_ocr)`: 提取文档文本

---

### 2. 法律条款识别服务 (`legal_identifier`)

**功能**: 使用 Qwen3-Max 识别合同中的法律条款

**参数**:
- `model`: Qwen 模型 (默认：qwen3-max)
- `api_key`: DashScope API 密钥
- `base_url`: API 基础 URL

**分类标签**:
- 责任条款
- 监管条款
- 合规条款
- 争议解决
- 其他法律条款

**工具**:
- `identify_clauses(contract_text)`: 识别法律条款

---

### 3. 法律条文检索服务 (`legal_retriever`)

**功能**: 使用 Pinecone 向量数据库检索相似法律条文

**参数**:
- `pinecone_api_key`: Pinecone API 密钥
- `pinecone_index`: 索引名称 (默认：software)
- `top_k`: 返回最相似的 K 个结果 (默认：3)
- `similarity_threshold`: 相似度阈值 (默认：0.6)
- `embedding_model`: 嵌入模型 (默认：all-MiniLM-L6-v2)

**工具**:
- `search_references(clauses)`: 检索法律参考

---

### 4. 合同修订服务 (`contract_revision`)

**功能**: 使用 Qwen3-Max 生成修订后的合同

**参数**:
- `model`: Qwen 模型 (默认：qwen3-max)
- `api_key`: DashScope API 密钥
- `base_url`: API 基础 URL
- `include_suggestions`: 是否包含修改建议 (默认：true)

**工具**:
- `revise_contract(contract_text, legal_clauses, legal_references)`: 生成修订合同

---

## 💡 使用示例

### 示例 1: 处理 Word 合同

```yaml
# 输入参数
doc_extractor:
  file_path: data/contracts/销售合同.docx
  use_ocr: false

legal_identifier:
  model: qwen3-max

legal_retriever:
  top_k: 3

contract_revision:
  include_suggestions: true
```

### 示例 2: 处理 PDF 扫描件

```yaml
# 输入参数
doc_extractor:
  file_path: data/contracts/租赁合同.pdf
  use_ocr: true  # 启用 OCR 处理扫描件

legal_retriever:
  similarity_threshold: 0.7  # 提高相似度阈值
```

---

## 📊 输出格式

### 成功响应

```json
{
  "extracted_text": "合同全文...",
  "identified_clauses": ["条款 1", "条款 2", ...],
  "legal_references": [
    {
      "clause": "识别的条款",
      "reference": "相关法律条文",
      "score": 0.85
    }
  ],
  "revised_contract": "修订后的完整合同",
  "suggestions": [
    "1. 修改位置：第三条\n   原文：...\n   修改为：...\n   修改原因：..."
  ]
}
```

### 错误处理

如果某一步骤失败，会返回错误信息但不中断整个流程:

```json
{
  "error": "具体错误信息",
  "partial_results": {...}
}
```

---

## 🔍 故障排查

### 问题 1: 文档提取失败

**可能原因**:
- 文件路径不正确
- PDF 文件损坏
- OCR 引擎未安装

**解决方案**:
```bash
# 检查文件是否存在
ls data/contracts/

# 验证 OCR 安装
python -c "from paddleocr import PaddleOCR; print('OK')"
```

---

### 问题 2: API 调用失败

**可能原因**:
- API Key 配置错误
- 网络连接问题
- 配额不足

**解决方案**:
```bash
# 测试 API 连接
python test_api_connection.py
```

---

### 问题 3: Pinecone 检索无结果

**可能原因**:
- 索引为空
- 相似度阈值过高
- 向量维度不匹配

**解决方案**:
1. 降低 `similarity_threshold` 参数
2. 检查 Pinecone 索引中是否有数据
3. 确认 embedding 模型正确

---

## 📝 最佳实践

1. **性能优化**
   - 对于长文档，先分段再处理
   - 使用缓存避免重复计算
   - 批量处理多个合同

2. **质量控制**
   - 设置合理的相似度阈值 (0.6-0.8)
   - 人工审核重要合同的修订结果
   - 定期更新法律条文数据库

3. **成本节约**
   - 本地开发使用简化版 pipeline
   - 生产环境再启用完整的 4 步流程
   - 监控 API 调用次数

---

## 🆚 版本对比

| 特性 | 简化版 (demo) | 完整版 (pipeline) |
|------|-------------|-----------------|
| 依赖服务 | sayhello | 4 个专用服务 |
| 处理步骤 | 1 步 | 4 步 |
| 适用场景 | UI 演示/测试 | 生产环境 |
| 处理速度 | 快 | 较慢 |
| 结果质量 | 基础 | 高质量 |

---

## 📚 参考资料

- [UltraRAG 官方文档](https://ultrarag.openbmb.cn/)
- [Qwen3-Max API 文档](https://help.aliyun.com/zh/dashscope/)
- [Pinecone 文档](https://docs.pinecone.io/)
- [原合同修订系统代码](../src/agent.py)

---

## ❓ 常见问题

**Q: 能否只使用部分步骤？**  
A: 可以！你可以自定义 pipeline，只包含需要的服务。

**Q: 如何添加自定义的法律条款分类？**  
A: 修改 `legal_identifier.py` 中的 `LEGAL_CATEGORIES` 字典。

**Q: 支持哪些文件格式？**  
A: 支持 .docx、.pdf 和纯文本文件。扫描件 PDF 需要启用 OCR。

**Q: 如何处理批量合同？**  
A: 创建循环处理的 pipeline 或使用脚本批量执行。

---

## 🎉 下一步

完成配置后，你可以:
1. 在 UI 中测试 pipeline
2. 根据实际需求调整参数
3. 集成到现有工作流中
4. 扩展更多功能 (如多语言支持、自定义模板等)

祝你使用愉快！🚀
