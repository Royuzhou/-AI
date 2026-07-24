"""
配置管理器 — DeepSeek / Pinecone 配置持久化 (本地 JSON)

密钥不硬编码。用户通过 Web 界面输入后保存到 data/web_config.json。
非敏感字段（base_url / model / index_name）从 config.py 获取默认值。
"""

import json
import os

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "web_config.json")

# 非敏感默认值（从 config.py 导入，避免循环引用）
def _defaults():
    from config import MAIN_LLM_CONFIG, PINECONE_CONFIG
    return {
        "deepseek": {
            "api_key": "",
            "base_url": MAIN_LLM_CONFIG["base_url"],
            "model": MAIN_LLM_CONFIG["model"],
        },
        "pinecone": {
            "api_key": "",
            "index_name": PINECONE_CONFIG.get("index_name", "software"),
            "top_k": PINECONE_CONFIG.get("top_k", 3),
        },
    }


def load_config() -> dict:
    """加载完整配置 — 用户保存的值覆盖默认值"""
    cfg = _defaults()
    if not os.path.exists(_CONFIG_FILE):
        return cfg
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for section in cfg:
            if section in saved:
                cfg[section].update(saved[section])
        return cfg
    except (json.JSONDecodeError, IOError):
        return cfg


def save_config(section: str, data: dict) -> bool:
    """保存某个 section 的配置 (本地 JSON)"""
    cfg = load_config()
    cfg[section].update(data)
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return True
