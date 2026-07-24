"""用户配置 API"""
from flask import request, jsonify
from . import api
from config import MAIN_LLM_CONFIG, PINECONE_CONFIG
from src.web.config_manager import load_config, save_config


def _mask(key: str) -> str:
    if len(key) > 8:
        return key[:8] + "****"
    return "****" if key else ""


@api.route("/config", methods=["GET"])
def get_config():
    cfg = load_config()
    ds = cfg["deepseek"]
    pc = cfg["pinecone"]
    return jsonify({
        "deepseek": {
            "api_key": ds["api_key"],
            "api_key_display": _mask(ds["api_key"]),
            "base_url": ds["base_url"],
            "model": ds["model"],
        },
        "pinecone": {
            "api_key": pc["api_key"],
            "api_key_display": _mask(pc["api_key"]),
            "index_name": pc["index_name"],
            "top_k": pc.get("top_k", 3),
        },
    })


@api.route("/config/test/deepseek", methods=["POST"])
def test_deepseek():
    data = request.json or {}
    api_key = data.get("api_key", "").strip()
    base_url = data.get("base_url", "").strip() or MAIN_LLM_CONFIG["base_url"]
    model = data.get("model", "").strip() or MAIN_LLM_CONFIG["model"]
    if not api_key:
        return jsonify({"connected": False, "error": "please enter API Key"})
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": "OK"}], max_tokens=5)
        return jsonify({"connected": True, "model": resp.model})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@api.route("/config/deepseek", methods=["POST"])
def save_deepseek():
    data = request.json or {}
    save_config("deepseek", {
        "api_key": data.get("api_key", "").strip(),
        "base_url": data.get("base_url", "").strip(),
        "model": data.get("model", "").strip(),
    })
    return jsonify({"success": True})


@api.route("/config/test/pinecone", methods=["POST"])
def test_pinecone():
    data = request.json or {}
    api_key = data.get("api_key", "").strip()
    if not api_key:
        return jsonify({"connected": False, "error": "please enter API Key"})
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        indexes = pc.list_indexes()
        names = [i.get("name", "") if isinstance(i, dict) else str(i)
                 for i in (indexes if isinstance(indexes, list) else [])]
        return jsonify({"connected": True, "indexes": names})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@api.route("/config/pinecone", methods=["POST"])
def save_pinecone():
    data = request.json or {}
    save_config("pinecone", {
        "api_key": data.get("api_key", "").strip(),
        "index_name": data.get("index_name", "").strip(),
        "top_k": data.get("top_k", 3),
    })
    return jsonify({"success": True})
