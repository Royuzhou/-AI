"""Agent 工具函数 — LangChain @tool 装饰器

三个暴露方式共用同一个函数体:
  1. @tool (LangGraph Agent 内部调用)
  2. MCP Server (外部 AI 通过 stdio 调用)
  3. CLI (python cli.py tool ...)
"""

import os
from langchain_core.tools import tool


# ═══════════════════════════════════════════════════════════
# 1. extract_document — 文档提取
# ═══════════════════════════════════════════════════════════

@tool
def extract_document(file_path: str) -> str:
    """从合同文件（PDF/DOCX）中提取原始文本。

    必须先调用此工具获取合同全文后才能进行后续的法律分析和修订。
    支持 .docx 和 .pdf 格式。

    Args:
        file_path: 合同文件的完整路径
    """
    from src.document.extractor import DocumentExtractor
    if not os.path.exists(file_path):
        return f"错误: 找不到文件 '{file_path}'"
    try:
        extractor = DocumentExtractor()
        return extractor.extract(file_path)
    except Exception as e:
        return f"文档提取失败: {e}"


# ═══════════════════════════════════════════════════════════
# 2. retrieve_legal_references — 法条检索
# ═══════════════════════════════════════════════════════════

@tool
def retrieve_legal_references(query: str) -> str:
    """从 Pinecone 法律知识库检索与合同条款相关的法律法规。

    关键规则:
    - 检索结果是语义匹配——逐条批判判断是否真正适用
    - 如果检索质量差，换关键词重新检索

    Args:
        query: 要检索的法律条款或关键词
    """
    from config import PINECONE_CONFIG
    from sentence_transformers import SentenceTransformer
    from pinecone import Pinecone

    if not query:
        return "未提供查询关键词"

    try:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
        pc = Pinecone(api_key=PINECONE_CONFIG["api_key"])
        index = pc.Index(PINECONE_CONFIG["index_name"])
        vec = model.encode([query]).tolist()[0]
        results = index.query(vector=vec, top_k=PINECONE_CONFIG.get("top_k", 3), include_metadata=True)

        items = []
        for i, m in enumerate(results.matches or [], 1):
            d = m.to_dict() if hasattr(m, 'to_dict') else {}
            meta = d.get("metadata", {}) or {}
            text = meta.get("original_text") or meta.get("text") or ""
            items.append(
                f"{i}. 相似度: {d.get('score', 0):.4f}\n"
                f"   法条原文: {text[:600]}"
            )

        if not items:
            return "未检索到相关法条。建议用不同关键词重新检索。"

        return "检索结果——请逐条批判判断其适用性:\n\n" + "\n\n".join(items)

    except Exception as e:
        return f"检索失败: {e}"


# ═══════════════════════════════════════════════════════════
# 3. finalize_revision — 格式校验 + 保存
# ═══════════════════════════════════════════════════════════

@tool
def finalize_revision(revised_content: str, output_path: str) -> str:
    """保存最终修订结果到文件。调用后任务结束，无法再修改。

    调用前必须确保 revised_content 严格符合以下格式（系统会校验）:
    - 整体须含【修订后的完整合同】和【修改建议清单】
    - 每条修改用 §CHANGE §ORIGINAL §LAW §SUGGESTION §REVISED §END 标签
    - 每条建议须注明法条依据

    如果格式不满足要求，系统将拒绝保存并返回错误信息。
    你需要根据错误信息修正后重新调用。

    Args:
        revised_content: 完整修订输出
        output_path: 输出文件的完整路径
    """
    from src.hooks import validate_revision_format

    if not revised_content:
        return "保存失败: 修订内容为空。"
    if not output_path:
        return "保存失败: 缺少输出路径。"

    valid, errors = validate_revision_format(revised_content)
    if not valid:
        return ("格式校验失败！请修正后重新调用:\n" +
                "\n".join(f"  - {e}" for e in errors) +
                "\n\n补充缺失内容后再次调用此工具。")

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(revised_content)
        return f"格式校验通过，已保存到: {output_path}"
    except Exception as e:
        return f"文件保存失败: {e}"


# ── 工具列表 ────────────────────────────────────────────

AGENT_TOOLS = [
    extract_document,
    retrieve_legal_references,
    finalize_revision,
]
