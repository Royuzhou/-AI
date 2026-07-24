"""
合同修订智能体配置文件

协议:
  外部通信: HTTP REST (ChatOpenAI → DeepSeek API)
  内部工具: MCP/stdio (Agent → MCP Servers)
"""

# ==================== 主模型配置 (DeepSeek v4) ====================
# 负责合同修订推理，使用 think/answer 标签
MAIN_LLM_CONFIG = {
    "api_key": "YOUR_DEEPSEEK_API_KEY",  # 在设置页面输入或设环境变量
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "temperature": 0,
    "max_tokens": 8192,
}

# ==================== 裁判模型配置 ====================
# 独立审查修订质量，不同参数确保差异化思维路径
JUDGE_LLM_CONFIG = {
    "api_key": "YOUR_DEEPSEEK_API_KEY",  # 在设置页面输入或设环境变量
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 4096,
}

# ==================== Pinecone 向量检索配置 ====================
PINECONE_CONFIG = {
    "api_key": "YOUR_PINECONE_API_KEY",  # 在设置页面输入或设环境变量
    "index_name": "software",
    "top_k": 3,
}

# ==================== Embedding 模型配置 ====================
MODEL_CONFIG = {
    "sentence_transformer": "sentence-transformers/all-MiniLM-L6-v2",
    "hf_endpoint": "https://hf-mirror.com",
}

# ==================== PaddleOCR 配置 ====================
OCR_CONFIG = {
    "use_textline_orientation": True,
    "lang": "ch",
}

# ==================== 文本处理配置 ====================
TEXT_CONFIG = {
    "pdf_text_threshold": 50,
    "dpi": 2,
}

# ==================== 法律条款分类标签 ====================
LEGAL_CATEGORIES = {
    "责任条款": "涉及责任划分、赔偿、违约等",
    "监管条款": "涉及政府监管、审批、备案等",
    "合规条款": "涉及法律法规遵循、行业标准等",
    "争议解决": "涉及仲裁、诉讼、管辖等",
    "其他法律条款": "其他涉及法律的内容",
}

# ==================== Reflection 配置 ====================
REFLECTION_CONFIG = {
    "max_retries": 2,  # 裁判不通过时最多重试次数
    "pass_threshold": 3,  # 1-5 分，>= 此分算通过
}

# ==================== MCP Server 配置 ====================
# 3 个 MCP Server 的启动命令，Agent 通过 MCP/stdio 连接
MCP_SERVERS = {
    "document-extractor": {
        "command": "python",
        "args": ["-m", "src.tools.document_server"],
    },
    "legal-retriever": {
        "command": "python",
        "args": ["-m", "src.tools.retrieval_server"],
    },
    "revision-finalizer": {
        "command": "python",
        "args": ["-m", "src.tools.finalize_server"],
    },
    "rag-updater": {
        "command": "python",
        "args": ["-m", "src.tools.rag_updater_server"],
    },
}

# ==================== 合并配置 ====================
CONFIG = {
    "main_llm": MAIN_LLM_CONFIG,
    "judge_llm": JUDGE_LLM_CONFIG,
    "pinecone": PINECONE_CONFIG,
    "model": MODEL_CONFIG,
    "ocr": OCR_CONFIG,
    "text": TEXT_CONFIG,
    "legal_categories": LEGAL_CATEGORIES,
    "memory": {},  # 保留键以兼容旧引用
    "reflection": REFLECTION_CONFIG,
    "mcp_servers": MCP_SERVERS,
    "output_dir": "data/outputs",
}
