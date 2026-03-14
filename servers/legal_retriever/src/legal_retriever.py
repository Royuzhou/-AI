"""
Legal Reference Retriever Server - 法律条文检索服务
使用 Pinecone 向量数据库进行相似度搜索
"""

from typing import Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from ultrarag.server import UltraRAG_MCP_Server

app = UltraRAG_MCP_Server("legal_retriever")


# 缓存嵌入模型和 Pinecone 客户端
_embedding_model = None
_pinecone_client = None


def get_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """获取或加载嵌入模型"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def get_pinecone_client(api_key: str):
    """获取或初始化 Pinecone 客户端"""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=api_key)
    return _pinecone_client


@app.tool(output="clauses->legal_references")
def search_references(
    clauses: List[str],
    index_name: str = "software",
    api_key: str = None,
    top_k: int = 3,
    similarity_threshold: float = 0.6,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> Dict:
    """
    检索相关法律条文
    
    Args:
        clauses: 法律条款文本列表
        index_name: Pinecone 索引名称
        api_key: Pinecone API 密钥
        top_k: 返回最相似的 K 个结果
        similarity_threshold: 相似度阈值
        embedding_model: 嵌入模型名称
    
    Returns:
        包含法律参考条文的字典
    """
    try:
        # 验证输入
        if not clauses:
            return {"legal_references": [], "message": "未提供法律条款"}
        
        # 检查 API 密钥
        if not api_key:
            app.logger.warning("Pinecone API Key 未配置，将返回空结果")
            return {"legal_references": []}
        
        # 获取嵌入模型
        model = get_embedding_model(embedding_model)
        
        # 生成条款的向量表示
        clause_embeddings = model.encode(clauses, convert_to_numpy=True)
        
        # 初始化 Pinecone 客户端
        pc = get_pinecone_client(api_key)
        
        # 获取索引
        index = pc.Index(index_name)
        
        # 执行向量搜索
        legal_references = []
        for i, clause in enumerate(clauses):
            # 查询相似向量
            query_response = index.query(
                vector=clause_embeddings[i].tolist(),
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # 处理查询结果
            for match in query_response.matches:
                score = match.score
                if score >= similarity_threshold:
                    reference_text = match.metadata.get('text', '') if match.metadata else ''
                    legal_references.append({
                        "clause": clause,
                        "reference": reference_text,
                        "score": float(score),
                        "id": match.id
                    })
        
        # 按相似度排序
        legal_references.sort(key=lambda x: x['score'], reverse=True)
        
        app.logger.info(f"成功检索{len(legal_references)}条法律参考")
        
        return {
            "legal_references": legal_references,
            "total_count": len(legal_references)
        }
        
    except Exception as e:
        app.logger.error(f"法律条文检索失败：{e}")
        return {
            "error": str(e),
            "legal_references": []
        }


if __name__ == "__main__":
    app.run(transport="stdio")
