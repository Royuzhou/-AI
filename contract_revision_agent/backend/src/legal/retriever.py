"""
法律条文查询模块
使用Pinecone进行向量检索查询相关法律条文
"""

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer


class LegalReferenceRetriever:
    """法律条文检索器"""

    def __init__(self, api_key, index_name, model_name, hf_endpoint=None):
        """
        初始化法律条文检索器

        Args:
            api_key: Pinecone API密钥
            index_name: 索引名称
            model_name: 句子转换器模型名称
            hf_endpoint: HuggingFace镜像地址
        """
        if hf_endpoint:
            import os
            os.environ['HF_ENDPOINT'] = hf_endpoint

        self.model = SentenceTransformer(model_name, local_files_only=True)
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        print("法律条文检索器初始化成功")

    def query(self, clauses, top_k=3):
        """
        查询相关法律条文

        Args:
            clauses: 法律条款列表
            top_k: 返回最相关的K个结果

        Returns:
            查询结果列表，每个结果包含clause, reference, score
        """
        query_results = []

        for clause in clauses:
            try:
                query_vector = self.model.encode(clause).tolist()
                results = self.index.query(
                    vector=query_vector,
                    top_k=top_k,
                    include_metadata=True
                )

                for match in results.matches:
                    query_results.append({
                        'clause': clause,
                        'reference': match.metadata.get('original_text', 'N/A'),
                        'score': match.score
                    })
            except Exception as e:
                print(f"Pinecone查询失败: {e}")
                continue

        return query_results

    def format_results(self, results):
        """
        格式化查询结果

        Args:
            results: 查询结果列表

        Returns:
            格式化后的文本
        """
        formatted = []
        for i, ref in enumerate(results, 1):
            formatted.append(
                f"{i}. 条款: {ref['clause']}\n"
                f"   参考条文: {ref['reference']}\n"
                f"   相似度: {ref['score']:.2f}\n"
            )
        return "\n".join(formatted)
