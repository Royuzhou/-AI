"""
rag-updater MCP Server — RAG 知识库更新

通过 MCP/stdio 协议提供知识库更新工具。
底层: src.rag.pipeline (LangGraph)

注册的 Tool:
  - update_law_by_url: 下载指定 URL 的法律 → RAG 管线入库
  - check_rag_status: 查询当前 Pinecone 索引状态
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.mcp import SimpleMCPServer
from src.rag import run_rag_update
from config import PINECONE_CONFIG

server = SimpleMCPServer("rag-updater", version="1.0.0")


@server.tool()
async def update_law_by_url(url: str, law_name: str = "") -> str:
    """从指定 URL 下载法律法规全文，通过 RAG 管线完成:
    下载 → 解析 → 分块 → 向量化 → 写入 Pinecone。

    调用此工具后，LLM 即可在后续对话中检索到该法律的相关条文。

    Args:
        url: 法律法规页面 URL（如 https://flk.npc.gov.cn/...）
        law_name: 法律名称（用于标记来源），如 '民法典'
    """
    if not url:
        return "错误: URL 不能为空"

    try:
        result = run_rag_update(url=url, source_name=law_name or url)
        if result["status"] == "completed":
            return (
                f"RAG 入库成功!\n"
                f"  法律: {result.get('source', '')}\n"
                f"  分块数: {result['chunks']}\n"
                f"  入库向量: {result.get('upserted', 0)}\n"
                f"  状态: {result['status']}"
            )
        else:
            errors = result.get("errors", [])
            return f"RAG 入库失败: {'; '.join(errors)}"
    except Exception as e:
        return f"RAG 管线执行异常: {e}"


@server.tool()
async def check_rag_status() -> str:
    """查询当前 Pinecone 知识库状态（向量总数、维度等）"""
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_CONFIG["api_key"])
        index = pc.Index(PINECONE_CONFIG["index_name"])
        stats_raw = index.describe_index_stats()
        stats = stats_raw.to_dict() if hasattr(stats_raw, 'to_dict') else vars(stats_raw)
        return (
            f"Pinecone 知识库状态:\n"
            f"  索引名: {PINECONE_CONFIG['index_name']}\n"
            f"  向量总数: {stats.get('total_vector_count', 'N/A')}\n"
            f"  维度: {stats.get('dimension', 'N/A')}\n"
            f"  命名空间: {list(stats.get('namespaces', {}).keys()) or 'default'}"
        )
    except Exception as e:
        return f"查询失败: {e}"


if __name__ == "__main__":
    server.run_sync()
