"""
知识库管理器 — Pinecone RAG 知识库的文档处理与索引

管道: 文档上传 → 文本提取 → 分块 → Embedding → Pinecone Upsert

所有重依赖均延迟导入，避免模块加载时触发包冲突。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import MODEL_CONFIG, PINECONE_CONFIG


class KnowledgeBaseManager:
    """Pinecone 知识库管理器"""

    def __init__(self, api_key: str = None, index_name: str = None,
                 embedding_model: str = None):
        self.api_key = api_key or PINECONE_CONFIG["api_key"]
        self.index_name = index_name or PINECONE_CONFIG["index_name"]
        self.embedding_model_name = embedding_model or MODEL_CONFIG["sentence_transformer"]

        self._pc = None
        self._index = None
        self._model = None

    # ── 连接 ──────────────────────────────────────────

    def connect(self) -> bool:
        """连接 Pinecone"""
        try:
            from pinecone import Pinecone
            self._pc = Pinecone(api_key=self.api_key)
            self._index = self._pc.Index(self.index_name)
            return True
        except Exception as e:
            raise ConnectionError(f"Pinecone 连接失败: {e}")

    def test_connection(self) -> dict:
        """测试 Pinecone 连接并返回状态"""
        import json as _json
        try:
            self.connect()
            # Pinecone v5+ 返回 IndexModel 对象，需转为 dict
            raw = self._pc.list_indexes()
            if isinstance(raw, dict):
                index_list = [raw]
            elif hasattr(raw, '__iter__') and not isinstance(raw, str):
                index_list = list(raw)
            else:
                index_list = []

            index_names = []
            for idx in index_list:
                if isinstance(idx, dict):
                    index_names.append(idx.get("name", str(idx)))
                elif hasattr(idx, 'name'):
                    index_names.append(idx.name)
                else:
                    index_names.append(str(idx))

            stats_raw = self._index.describe_index_stats()
            stats = stats_raw.to_dict() if hasattr(stats_raw, 'to_dict') else vars(stats_raw)

            return {
                "connected": True,
                "indexes": index_names,
                "current_index": self.index_name,
                "total_vectors": int(stats.get("total_vector_count", 0)),
                "dimension": int(stats.get("dimension", 0)),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    # ── Embedding ─────────────────────────────────────

    def _load_model(self):
        if self._model is None:
            import os as _os
            from config import MODEL_CONFIG
            # 使用国内镜像避免 SSL/网络问题
            if MODEL_CONFIG.get("hf_endpoint"):
                _os.environ.setdefault("HF_ENDPOINT", MODEL_CONFIG["hf_endpoint"])
            _os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
            _os.environ.setdefault("CURL_CA_BUNDLE", "")
            _os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self.embedding_model_name,
                trust_remote_code=True,
                local_files_only=True,  # 模型已缓存，跳过网络请求
            )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """文本向量化"""
        self._load_model()
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    # ── 文本分块 ──────────────────────────────────────

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """将长文本按句子边界分块"""
        sentences = re.split(r'(?<=[。！？\n])', text)
        chunks = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= chunk_size:
                current += sent
            else:
                if current.strip():
                    chunks.append(current.strip())
                overlap_text = current[-overlap:] if len(current) > overlap else ""
                current = overlap_text + sent
        if current.strip():
            chunks.append(current.strip())
        return chunks

    # ── 文档处理管道 ──────────────────────────────────

    def process_document(self, file_path: str, chunk_size: int = 500,
                         overlap: int = 50) -> dict:
        """处理单个文档: 提取 → 分块 → Embedding → Upsert"""
        # 1. 连接
        if self._pc is None:
            self.connect()

        # 2. 提取文本 (延迟导入避免 fitz 包冲突)
        from src.document.extractor import DocumentExtractor
        filename = os.path.basename(file_path)
        extractor = DocumentExtractor()
        text = extractor.extract(file_path)

        # 3. 分块
        chunks = self.chunk_text(text, chunk_size, overlap)
        if not chunks:
            return {"success": False, "error": "无法从文档中提取有效文本"}

        # 4. Embedding
        self._load_model()
        vectors = self.embed(chunks)

        # 5. Upsert (Pinecone ID 只接受 ASCII)
        import hashlib
        safe = hashlib.md5(filename.encode()).hexdigest()[:12]
        ids = [f"{safe}_{i}" for i in range(len(chunks))]
        to_upsert = []
        for i, (cid, vec, chunk) in enumerate(zip(ids, vectors, chunks)):
            to_upsert.append((cid, vec, {
                "source": filename,
                "chunk_index": i,
                "text": chunk[:1000],
                "original_text": chunk[:2000],
            }))

        # 批量 upsert
        batch_size = 100
        for start in range(0, len(to_upsert), batch_size):
            batch = to_upsert[start:start + batch_size]
            self._index.upsert(vectors=batch)

        return {
            "success": True,
            "filename": filename,
            "chunks": len(chunks),
            "vectors": len(vectors),
        }

    # ── 搜索 ─────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """搜索知识库"""
        if self._pc is None:
            self.connect()
        self._load_model()

        query_vec = self._model.encode([query]).tolist()[0]
        results = self._index.query(vector=query_vec, top_k=top_k, include_metadata=True)

        def _extract(m):
            d = m.to_dict() if hasattr(m, 'to_dict') else (m if isinstance(m, dict) else vars(m))
            meta = d.get("metadata", {}) or {}
            # 兼容多种 metadata key 格式
            text = (meta.get("text") or meta.get("original_text") or
                     meta.get("content") or str(meta.get("text", meta.get("original_text", ""))))
            source = (meta.get("source") or meta.get("filename") or
                       meta.get("law_name") or "")
            return {
                "id": d.get("id", ""),
                "score": round(d.get("score", 0), 4),
                "text": (text or "")[:1000],
                "source": (source or ""),
                "metadata": {k: str(v)[:200] for k, v in meta.items()},  # 完整 metadata
                "vector_id": d.get("id", ""),
            }

        matches = results.matches if hasattr(results, "matches") else []
        return {
            "query": query,
            "top_k": top_k,
            "total_found": len(matches),
            "results": [_extract(m) for m in matches],
        }

    # ── 删除 ─────────────────────────────────────────

    def delete_entries(self, ids: list[str]) -> int:
        """删除指定条目"""
        if self._pc is None:
            self.connect()
        self._index.delete(ids=ids)
        return len(ids)
