"""
合同修订智能体配置文件
"""

# Qwen3-Max API配置
QWEN_CONFIG = {
    "api_key": "sk-a852d5808e084025aae207a99545b776",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3-max"
}

# Pinecone配置
PINECONE_CONFIG = {
    "api_key": "pcsk_6f3yXX_CK5s2GTwXKPQVectvkzKqdQvBArp4Q6FnHhxYV5UDGiVBaFTEBN9AiErWv58Kd2",
    "index_name": "software",
    "top_k": 3
}

# 模型配置
MODEL_CONFIG = {
    "sentence_transformer": "sentence-transformers/all-MiniLM-L6-v2",
    "hf_endpoint": "https://hf-mirror.com"
}

# PaddleOCR配置
OCR_CONFIG = {
    "use_textline_orientation": True,
    "lang": "ch"
}

# 文本处理配置
TEXT_CONFIG = {
    "pdf_text_threshold": 50,
    "dpi": 2
}

# 法律条款分类标签
LEGAL_CATEGORIES = {
    "责任条款": "涉及责任划分、赔偿、违约等",
    "监管条款": "涉及政府监管、审批、备案等",
    "合规条款": "涉及法律法规遵循、行业标准等",
    "争议解决": "涉及仲裁、诉讼、管辖等",
    "其他法律条款": "其他涉及法律的内容"
}

# 合并所有配置
CONFIG = {
    "qwen_config": QWEN_CONFIG,
    "pinecone_config": PINECONE_CONFIG,
    "model_config": MODEL_CONFIG,
    "ocr_config": OCR_CONFIG,
    "text_config": TEXT_CONFIG,
    "legal_categories": LEGAL_CATEGORIES,
    "output_dir": "data/outputs"
}

# UltraRAG 相关配置，可选启用
# 如果你希望在项目中启用 UltraRAG 作为检索/生成后端，
# 将 use 设为 True 并指定 server_root 等参数。
ULTRARAG_CONFIG = {
    # 是否启用 UltraRAG；默认关闭以保证向后兼容
    "use": False,
    # 本地 UltraRAG 仓库中 servers 目录的绝对路径或相对路径
    # 例如: "../UltraRAG/servers" 或 "D:/.../UltraRAG/servers"
    "server_root": "",
    # 检索器使用的 embedding 模型名称
    "retriever_model": "Qwen/Qwen3-Embedding-0.6B",
}

# 将其加入主配置，方便在代码中统一访问
CONFIG["ultrarag_config"] = ULTRARAG_CONFIG