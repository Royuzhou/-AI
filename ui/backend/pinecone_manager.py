"""
Pinecone 向量数据库连接管理模块
直接连接 Pinecone 云服务，不通过 Milvus SDK
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

try:
    from pinecone import Pinecone, ServerlessSpec, PodSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("pinecone-client not installed")


class PineconeManager:
    """Pinecone 数据库管理器"""
    
    def __init__(self, api_key: str, environment: Optional[str] = None):
        """
        初始化 Pinecone 客户端
        
        Args:
            api_key: Pinecone API Key
            environment: Pinecone 环境（可选，新版不需要）
        """
        if not PINECONE_AVAILABLE:
            raise ImportError("pinecone-client is not installed")
        
        self.api_key = api_key
        self.pc = Pinecone(api_key=api_key)
        logger.info("Pinecone client initialized successfully")
    
    def list_indexes(self) -> List[str]:
        """列出所有索引"""
        try:
            indexes = self.pc.list_indexes()
            return [idx.name for idx in indexes]
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """获取索引统计信息"""
        try:
            index = self.pc.Index(index_name)
            stats = index.describe_index_stats()
            return {
                "name": index_name,
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("index_fullness", 0),
                "total_vector_count": stats.get("total_vector_count", 0),
                "namespaces": stats.get("namespaces", {})
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
    
    def query(self, index_name: str, vector: List[float], top_k: int = 10, 
              filter_dict: Optional[Dict] = None, include_metadata: bool = True) -> Dict:
        """
        查询向量
        
        Args:
            index_name: 索引名称
            vector: 查询向量
            top_k: 返回数量
            filter_dict: 元数据过滤条件
            include_metadata: 是否包含元数据
            
        Returns:
            查询结果
        """
        try:
            index = self.pc.Index(index_name)
            response = index.query(
                vector=vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            return response.to_dict()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"matches": []}
    
    def upsert(self, index_name: str, vectors: List[tuple]):
        """
        插入向量
        
        Args:
            index_name: 索引名称
            vectors: 向量列表，格式 [(id, vector, metadata), ...]
        """
        try:
            index = self.pc.Index(index_name)
            index.upsert(vectors=vectors)
            logger.info(f"Upserted {len(vectors)} vectors to {index_name}")
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise
    
    def delete_index(self, index_name: str):
        """删除索引"""
        try:
            self.pc.delete_index(name=index_name)
            logger.info(f"Deleted index: {index_name}")
        except Exception as e:
            logger.error(f"Delete index failed: {e}")
            raise
    
    def create_index(self, name: str, dimension: int = 768, 
                     metric: str = "cosine", spec: Optional[Any] = None):
        """
        创建索引
        
        Args:
            name: 索引名称
            dimension: 向量维度
            metric: 相似度度量方式 (cosine, dotproduct, euclidean)
            spec: 索引规格 (ServerlessSpec 或 PodSpec)
        """
        try:
            if spec is None:
                # 默认使用 Serverless 规格
                spec = ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            
            self.pc.create_index(
                name=name,
                dimension=dimension,
                metric=metric,
                spec=spec
            )
            logger.info(f"Created index: {name}")
        except Exception as e:
            logger.error(f"Create index failed: {e}")
            raise


def load_pinecone_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载 Pinecone 配置
    
    Args:
        config_path: 配置文件路径，默认为 kb_config.json
        
    Returns:
        配置字典
    """
    if config_path is None:
        # 默认路径
        base_dir = Path(__file__).parent.parent.parent
        config_path = base_dir / "data" / "knowledge_base" / "kb_config.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 支持两种配置格式
    if "pinecone" in config:
        return config["pinecone"]
    elif "milvus" in config:
        # 兼容 Milvus 格式的配置
        milvus_cfg = config["milvus"]
        if "pinecone.io" in milvus_cfg.get("uri", ""):
            # 如果 URI 是 Pinecone 格式，转换为 Pinecone 配置
            return {
                "api_key": milvus_cfg.get("token", ""),
                "environment": None  # 新版 Pinecone 不需要
            }
    
    return {}


def get_pinecone_client() -> Optional[PineconeManager]:
    """获取 Pinecone 客户端"""
    config = load_pinecone_config()
    api_key = config.get("api_key", "")
    
    if not api_key:
        logger.warning("Pinecone API key not configured")
        return None
    
    try:
        return PineconeManager(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")
        return None
