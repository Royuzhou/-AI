"""
legal-retriever MCP Server

通过 MCP/stdio 协议提供法条检索工具。
底层: LegalReferenceRetriever (Pinecone + SentenceTransformer)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.mcp import SimpleMCPServer
from config import PINECONE_CONFIG, MODEL_CONFIG
from src.legal.retriever import LegalReferenceRetriever

server = SimpleMCPServer("legal-retriever", version="1.0.0")

# 初始化检索器（模块级，复用）
_retriever = LegalReferenceRetriever(
    api_key=PINECONE_CONFIG["api_key"],
    index_name=PINECONE_CONFIG["index_name"],
    model_name=MODEL_CONFIG["sentence_transformer"],
    hf_endpoint=MODEL_CONFIG.get("hf_endpoint"),
)


@server.tool()
async def retrieve_legal_references(clauses: list[str]) -> str:
    """从 Pinecone 法律知识库批量检索与合同条款相关的法律法规。

    关键规则:
    - 一次性传入所有需要检索的条款，不要逐条分次调用
    - 检索结果是语义匹配——逐条批判判断是否真正适用
    - 如果某条检索质量差，对那条换关键词重新检索

    Args:
        clauses: 所有需要检索的条款文本列表（一次性全部传入，不要拆分）
    """
    if not clauses:
        return "未提供条款文本，无法检索。"

    top_k = PINECONE_CONFIG.get("top_k", 3)
    try:
        references = _retriever.query(clauses, top_k=top_k)
    except Exception as e:
        return f"检索失败: {e}"

    if not references:
        return "未检索到相关法条。建议用不同关键词重新检索。"

    parts = ["检索结果——请逐条批判判断其适用性（语义相似≠法律相关）:\n"]
    for i, ref in enumerate(references, 1):
        parts.append(
            f"{i}. 条款: {ref['clause'][:120]}\n"
            f"   法条: {ref['reference'][:250]}\n"
            f"   相似度: {ref['score']:.4f}\n"
            f"   → 此条法条是否真正适用？请在 think 中判断。"
        )
    return "\n".join(parts)


if __name__ == "__main__":
    server.run_sync()
