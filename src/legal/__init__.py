"""法律模块"""

from .identifier import LegalClauseIdentifier
from .retriever import LegalReferenceRetriever

# UltraRAG 封装可能不存在，故以 try/except 保护
try:
	from .ultrarag_retriever import UltraRAGRetriever
except ImportError:  # pragma: no cover - optional dependency
	UltraRAGRetriever = None

__all__ = ['LegalClauseIdentifier', 'LegalReferenceRetriever', 'UltraRAGRetriever']