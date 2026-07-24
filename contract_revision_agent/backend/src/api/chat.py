"""SSE 流式对话 — 支持 MCP 工具调用"""
import json
import os
import uuid
from datetime import datetime
from flask import request, jsonify, Response
from . import api
from config import MAIN_LLM_CONFIG, PINECONE_CONFIG, MODEL_CONFIG
from src.web.config_manager import load_config

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
CHAT_HISTORY_FILE = os.path.join(HISTORY_DIR, "chat_history.json")


def _get_llm_config() -> dict:
    cfg = load_config()
    ds = cfg["deepseek"]
    return {
        "api_key": ds["api_key"] or MAIN_LLM_CONFIG["api_key"],
        "base_url": ds["base_url"] or MAIN_LLM_CONFIG["base_url"],
        "model": ds["model"] or MAIN_LLM_CONFIG["model"],
    }

SYSTEM_PROMPT = """你是一个专业的法律助手，精通中国法律法规。
你可以使用 retrieve_legal_references 工具在本地 Pinecone 知识库中检索相关法条。

重要规则:
- 最多调用工具 1 次，之后必须直接回答用户问题
- 如果检索返回空结果，基于你的法律知识直接回答
- 回答时引用具体法条来源
- 请用专业、清晰的中文回答。"""

# ── 工具定义 (OpenAI function calling 格式) ──

CHAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_legal_references",
            "description": "从本地法律知识库 (Pinecone) 检索与条款相关的法律法规原文",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要检索的法律条款或关键词"}
                },
                "required": ["query"]
            }
        }
    },
]


def _execute_tool(name: str, args: dict) -> str:
    """执行工具调用并返回结果文本"""
    try:
        if name == "retrieve_legal_references":
            return _retrieve_legal(args.get("query", ""))
        else:
            return f"未知工具: {name}"
    except Exception as e:
        return f"工具执行错误: {e}"


# 模块级缓存 — 避免每次查询都重载模型
_retrieve_model = None
_retrieve_pc = None
_retrieve_index = None


def _get_retriever():
    global _retrieve_model, _retrieve_pc, _retrieve_index
    if _retrieve_model is None:
        from sentence_transformers import SentenceTransformer
        _retrieve_model = SentenceTransformer(MODEL_CONFIG["sentence_transformer"], local_files_only=True)
    if _retrieve_pc is None:
        from pinecone import Pinecone
        _retrieve_pc = Pinecone(api_key=PINECONE_CONFIG["api_key"])
        _retrieve_index = _retrieve_pc.Index(PINECONE_CONFIG["index_name"])
    return _retrieve_model, _retrieve_index


def _retrieve_legal(query: str) -> str:
    try:
        model, index = _get_retriever()
        vec = model.encode([query]).tolist()[0]
        results = index.query(vector=vec, top_k=3, include_metadata=True)
        items = []
        for m in (results.matches or []):
            d = m.to_dict() if hasattr(m, 'to_dict') else (m if isinstance(m, dict) else {})
            meta = d.get("metadata", {}) or {}
            text = meta.get("original_text") or meta.get("text") or str(meta)[:500]
            items.append(f"相似度 {d.get('score', 0):.4f}:\n{text[:600]}")
        if not items:
            return "未检索到相关法条"
        return f"知识库检索 '{query}' 结果:\n\n" + "\n\n---\n\n".join(items)
    except Exception as e:
        return f"知识库检索失败: {e}。请基于您的法律知识直接回答用户问题。"


def _load_history() -> list[dict]:
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(history: list[dict]):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@api.route("/chat/list", methods=["GET"])
def chat_list():
    history = _load_history()
    summaries = [{"id": h["id"], "title": h.get("title", ""), "created_at": h.get("created_at", ""),
                  "message_count": len(h.get("messages", []))} for h in history]
    return jsonify(summaries[::-1])


@api.route("/chat/<chat_id>", methods=["GET"])
def chat_detail(chat_id):
    history = _load_history()
    for h in history:
        if h["id"] == chat_id:
            return jsonify(h)
    return jsonify({"error": "not found"}), 404


@api.route("/chat/send", methods=["POST"])
def chat_send():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    chat_id = data.get("chat_id", "")
    files = data.get("files", [])

    if not user_message and not files:
        return jsonify({"error": "empty message"}), 400

    history = _load_history()
    chat = None
    if chat_id:
        for h in history:
            if h["id"] == chat_id:
                chat = h
                break
    if chat is None:
        chat = {"id": str(uuid.uuid4())[:8], "title": user_message[:30] or "新对话",
                "created_at": datetime.now().isoformat(), "messages": []}
        history.append(chat)

    if files:
        from src.document.extractor import DocumentExtractor
        extractor = DocumentExtractor()
        file_texts = []
        for fp in files:
            if os.path.exists(fp):
                try:
                    txt = extractor.extract(fp)
                    file_texts.append(f"[文件: {os.path.basename(fp)}]\n{txt[:3000]}")
                except Exception:
                    file_texts.append(f"[文件读取失败: {os.path.basename(fp)}]")
        if file_texts:
            user_message = "\n\n".join(file_texts) + "\n\n" + (user_message or "请分析以上文件内容。")

    chat["messages"].append({"role": "user", "content": user_message})

    def generate():
        try:
            llm = _get_llm_config()
            from openai import OpenAI
            client = OpenAI(api_key=llm["api_key"], base_url=llm["base_url"])

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in chat["messages"][-20:]:
                messages.append({"role": m["role"], "content": m["content"]})

            max_tool_rounds = 3
            for _ in range(max_tool_rounds):
                resp = client.chat.completions.create(
                    model=llm["model"],
                    messages=messages,
                    tools=CHAT_TOOLS,
                    tool_choice="auto",
                    stream=False,  # 非流式处理 tool calls
                )
                choice = resp.choices[0]
                msg = choice.message

                # LLM 要求调工具
                if msg.tool_calls:
                    messages.append(msg)
                    for tc in msg.tool_calls:
                        tool_name = tc.function.name
                        tool_args = json.loads(tc.function.arguments)
                        # 通知前端工具调用
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name}, ensure_ascii=False)}\n\n"
                        result = _execute_tool(tool_name, tool_args)
                        yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_name, 'text': result[:200]}, ensure_ascii=False)}\n\n"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result[:4000],
                        })
                else:
                    # 最终回答 — 流式输出
                    full = msg.content or ""
                    # 用流式模拟输出（非流式结果拆成 token 发送）
                    for i in range(0, len(full), 4):
                        yield f"data: {json.dumps({'token': full[i:i+4]}, ensure_ascii=False)}\n\n"
                    chat["messages"].append({"role": "assistant", "content": full})
                    _save_history(history)
                    yield f"data: {json.dumps({'done': True, 'chat_id': chat['id']}, ensure_ascii=False)}\n\n"
                    return

            # 超过最大工具轮数
            chat["messages"].append({"role": "assistant", "content": "抱歉，查询次数过多，请重新描述您的问题。"})
            _save_history(history)
            yield f"data: {json.dumps({'done': True, 'chat_id': chat['id']}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api.route("/chat/context", methods=["POST"])
def chat_context():
    data = request.json or {}
    chat_id = data.get("chat_id", "")
    revision_text = data.get("revision_text", "")
    if not revision_text:
        return jsonify({"error": "empty revision text"}), 400
    history = _load_history()
    chat = None
    if chat_id:
        for h in history:
            if h["id"] == chat_id: chat = h; break
    if chat is None:
        chat = {"id": str(uuid.uuid4())[:8], "title": "合同修订讨论",
                "created_at": datetime.now().isoformat(), "messages": []}
        history.append(chat)
    chat["messages"].append({"role": "system", "content": f"[系统] 以下是对合同的修订结果，请基于此回答后续问题:\n\n{revision_text[:5000]}"})
    _save_history(history)
    return jsonify({"success": True, "chat_id": chat["id"]})


@api.route("/chat/<chat_id>", methods=["DELETE"])
def chat_delete(chat_id):
    history = _load_history()
    history = [h for h in history if h["id"] != chat_id]
    _save_history(history)
    return jsonify({"success": True})
