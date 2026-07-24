"""知识库管理 API"""
import os
from flask import request, jsonify
from . import api
from config import PINECONE_CONFIG
from src.web.kb_manager import KnowledgeBaseManager
from src.web.config_manager import load_config

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_kb():
    """优先用用户保存的 key，否则 fallback config.py"""
    cfg = load_config()
    pc = cfg["pinecone"]
    api_key = pc["api_key"] or PINECONE_CONFIG["api_key"]
    index_name = pc["index_name"] or PINECONE_CONFIG["index_name"]
    return KnowledgeBaseManager(api_key=api_key, index_name=index_name)


@api.route("/kb/status", methods=["GET"])
def kb_status():
    try:
        return jsonify(_get_kb().test_connection())
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@api.route("/kb/upload", methods=["POST"])
def kb_upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "no file"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "empty filename"}), 400
    fp = os.path.join(UPLOAD_DIR, file.filename)
    file.save(fp)
    return jsonify({"success": True, "filename": file.filename, "path": fp})


@api.route("/kb/process", methods=["POST"])
def kb_process():
    data = request.json or {}
    fp = data.get("filepath", "")
    if not fp or not os.path.exists(fp):
        return jsonify({"success": False, "error": "file not found"}), 400
    try:
        return jsonify(_get_kb().process_document(fp, chunk_size=data.get("chunk_size", 500)))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@api.route("/kb/search", methods=["GET"])
def kb_search():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"results": []})
    try:
        return jsonify(_get_kb().search(q, top_k=int(request.args.get("top_k", 5))))
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})


@api.route("/kb/entries", methods=["DELETE"])
def kb_delete():
    ids = (request.json or {}).get("ids", [])
    if not ids:
        return jsonify({"success": False, "error": "no ids"}), 400
    _get_kb().delete_entries(ids)
    return jsonify({"success": True, "deleted": len(ids)})
