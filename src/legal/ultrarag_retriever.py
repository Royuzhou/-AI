"""
UltraRAG 检索器封装

为了平滑迁移现有的 LegalReferenceRetriever，
此模块提供一个简单的 UltraRAG 封装层。
"""

try:
    from ultrarag.api import initialize, ToolCall
except ImportError:  # pragma: no cover - 运行环境可能未安装
    initialize = None
    ToolCall = None


class UltraRAGRetriever:
    """UltraRAG 检索器包装

    目前仅演示最小功能：初始化 retriever server 并提供
    与原有类兼容的 query / format_results 接口。
    如果 UltraRAG 没有安装或初始化失败，会抛出异常。
    """

    def __init__(self, server_root=None, retriever_model="Qwen/Qwen3-Embedding-0.6B"):
        if initialize is None or ToolCall is None:
            raise ImportError("UltraRAG 库未安装，请先通过 uv pip install -e . 或者 Docker 部署")

        # initialize 只需在第一次创建时调用即可
        initialize(["retriever"], server_root=server_root)
        # 默认先初始化检索器模型
        ToolCall.retriever.retriever_init(model_name_or_path=retriever_model)
        self._model = retriever_model

    def query(self, clauses, top_k=3):
        # clauses 应该是字符串列表
        result = ToolCall.retriever.retriever_search(
            query_list=clauses,
            top_k=top_k,
        )
        query_results = []
        # UltraRAG 返回的 ret_psg 结构通常是一个嵌套列表
        ret_psg = result.get("ret_psg", [])
        for clause, passages in zip(clauses, ret_psg):
            for match in passages:
                query_results.append({
                    "clause": clause,
                    "reference": match.get("passage", ""),
                    "score": match.get("score", 0.0),
                })
        return query_results

    def format_results(self, results):
        formatted = []
        for i, ref in enumerate(results, 1):
            formatted.append(
                f"{i}. 条款: {ref['clause']}\n"
                f"   参考条文: {ref['reference']}\n"
                f"   相似度: {ref['score']:.2f}\n"
            )
        return "\n".join(formatted)
