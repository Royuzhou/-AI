# 合同修订智能体 (Contract Revision Agent)

基于 **LangGraph + DeepSeek + RAG** 的 AI 合同法律审查与修订系统。

## 功能

- 💬 **AI 对话** — 支持法律咨询、条款解释、合同分析，SSE 流式输出
- 📄 **合同修订** — 上传合同文件，Agent 自动完成法律审查并输出结构化修订结果
- 📚 **知识库管理** — 拖拽上传法律法规文件，自动分块、向量化、写入 Pinecone
- ⚖️ **RAG 检索** — Agent 实时从 Pinecone 知识库检索相关法条，确保修订有法可依
- 🔍 **Reflection 自省** — 双模型审查机制，裁判 LLM 独立评分，不通过自动重改
- ⚙️ **密钥管理** — Web 页面配置 DeepSeek / Pinecone API Key，本地 JSON 持久化

## 技术栈

| 层 | 技术 |
|----|------|
| Agent 框架 | LangGraph (StateGraph + ToolNode + Reflection) |
| LLM | DeepSeek-Chat (主模型 + 裁判模型双实例) |
| 工具调用 | LangChain @tool 装饰器 (Function Calling) |
| 向量检索 | Pinecone + SentenceTransformer (all-MiniLM-L6-v2) |
| 文档处理 | PaddleOCR + PyMuPDF + python-docx + PyPDF2 |
| 后端 | Flask + SSE 流式 |
| 前端 | Vue 3 + Element Plus + Pinia + Vite |
| 协议 | 内部 Function Calling，外部保留 MCP/stdio 接口 |

## 项目结构

```
contract_revision_agent/
├── start.py                     # 一键启动
├── requirements.txt             # Python 依赖
├── backend/
│   ├── run.py                   # Flask 入口
│   ├── cli.py                   # CLI 运维
│   ├── config.py                # 全局配置
│   └── src/
│       ├── agent.py             # LangGraph Agent (LLM + ToolNode + Reflection)
│       ├── mcp/                 # 自研 MCP 协议 (Server/Client/Host)
│       ├── tools/               # Tool 函数 + MCP Server
│       ├── rag/                 # RAG 管线 (7 节点)
│       ├── document/            # 文档提取 (OCR + PDF/Word)
│       ├── legal/               # 法律检索 (Pinecone)
│       ├── hooks/               # 格式校验 (think/answer 标签)
│       ├── memory/              # 记忆层
│       └── api/                 # Flask API (chat/contract/knowledge/config)
├── frontend/                    # Vue 3 前端
│   └── src/
│       ├── pages/               # ChatPage / RevisionPage / KnowledgePage / HistoryPage / SettingsPage
│       ├── components/          # Sidebar / ChatMessage / ChatInput / DiffView / SuggestionList
│       ├── stores/              # Pinia (chat / config / kb)
│       └── api/                 # 前端 API 封装
└── data/                        # 运行时数据
    ├── uploads/
    └── outputs/
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```

### 2. 配置 API Key

启动后在设置页面（⚙️）输入你的 DeepSeek 和 Pinecone API Key：

- DeepSeek: `sk-...` + Base URL + Model
- Pinecone: `pcsk_...` + Index Name

密钥保存在 `data/web_config.json`，不会提交到 Git。

### 3. 启动

```bash
python start.py
# → http://localhost:8080
```

### 4. 使用

1. **对话** — 直接输入法律问题，AI 流式回复
2. **合同修订** — 上传合同文件 + 输入"帮我修订"，右侧面板显示结构化结果
3. **知识库** — 上传法律法规文件（PDF/Word/TXT），自动入库
4. **历史** — 查看和管理过往对话

## CLI 运维

```bash
cd backend

# 合同修订
python cli.py revise 合同文件.docx

# RAG 知识库更新
python cli.py kb-update --file 民法典全文.pdf --name 民法典
python cli.py kb-update --url https://... --name 公司法

# 查看知识库状态
python cli.py kb-status

# 单独调用工具
python cli.py tool extract 合同.docx
python cli.py tool search 违约金
```

## Agent 架构

```
用户上传合同
    │
    ▼
┌──────────────────────┐
│  LLM Node (DeepSeek) │ ← System Prompt: 六阶段框架
│  STRUCTURE → CLASSIFY│    + 内嵌 7 条法律原则
│  → RETRIEVE → REVISE │    + think/answer 标签
│  → REFLECT → OUTPUT  │
└──────┬───────┬───────┘
       │       │
   tool_call  end
       │
       ▼
┌──────────────┐
│  ToolNode     │  extract_document / retrieve_legal_references / finalize_revision
└──────┬───────┘
       │
   finalize? → ┌────────────────┐
               │ Reflection Node │  裁判 LLM (独立审查)
               │ 5 维评分 1-5    │  不通过 → 反馈 → LLM 重改
               └────────────────┘
```

## RAG 管线

```
输入: URL / 本地文件 / 纯文本
  ↓
[1] 获取文本 (下载 / 提取 / 直传)
  ↓
[2] 分块 (500字/块, 50 overlap)
  ↓
[3] 向量化 (SentenceTransformer 384-dim)
  ↓
[4] 入库 (Pinecone upsert)
  ↓
[5] 验证
```

## 修订输出格式

每条修改按 5 个标签输出：

```
§CHANGE
§ORIGINAL
(合同原文)
§LAW
(RAG 检索的法律条文)
§SUGGESTION
修改建议 + 修改理由 + 法条依据
§REVISED
(修改后文本)
§END
```

## License

MIT
