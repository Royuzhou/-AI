"""RAG 更新管线 — 7 个节点（纯函数，无 LangGraph 依赖）"""
import re, os
import httpx
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from config import PINECONE_CONFIG, MODEL_CONFIG

_embedder: SentenceTransformer = None
_pc: Pinecone = None
_index = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_CONFIG["sentence_transformer"], local_files_only=True)
    return _embedder


def _get_index():
    global _pc, _index
    if _pc is None:
        _pc = Pinecone(api_key=PINECONE_CONFIG["api_key"])
        _index = _pc.Index(PINECONE_CONFIG["index_name"])
    return _index


# ═══════════════════════════════════════════════════════════
# 节点 1: file_extract — 从本地文件提取文本 (新增)
# ═══════════════════════════════════════════════════════════

def file_extract(file_path: str, source_name: str) -> tuple[str, str]:
    """从本地 PDF/DOCX/TXT 文件中提取文本。返回 (clean_text, source_name)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if file_path.lower().endswith(('.txt', '.md')):
        with open(file_path, 'r', encoding='utf-8') as f:
            clean = f.read()
        return clean, source_name or os.path.basename(file_path)

    from src.document.extractor import DocumentExtractor
    extractor = DocumentExtractor()
    text = extractor.extract(file_path)
    if not text or len(text) < 50:
        raise ValueError(f"文件提取文本过短 ({len(text)} chars)")
    return text, source_name or os.path.basename(file_path)


# ═══════════════════════════════════════════════════════════
# 节点 2: fetch — 从 URL 下载 (保留)
# ═══════════════════════════════════════════════════════════

def fetch(url: str) -> str:
    """从 URL 下载原始 HTML"""
    resp = httpx.get(url, timeout=30, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text


# ═══════════════════════════════════════════════════════════
# 节点 3: parse — HTML → 纯文本
# ═══════════════════════════════════════════════════════════

def parse(raw_html: str) -> str:
    """从 HTML 中提取清洗后的纯文本"""
    soup = BeautifulSoup(raw_html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    clean = '\n'.join(lines)
    if len(clean) < 100:
        raise ValueError(f"解析文本过短 ({len(clean)} chars)")
    return clean


# ═══════════════════════════════════════════════════════════
# 节点 4: chunk — 分块
# ═══════════════════════════════════════════════════════════

def chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按句边界分块"""
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
    if not chunks:
        raise ValueError("分块结果为空")
    return chunks


# ═══════════════════════════════════════════════════════════
# 节点 5: embed — 向量化
# ═══════════════════════════════════════════════════════════

def embed(chunks: list[str]) -> list[list[float]]:
    """文本 → 向量"""
    model = _get_embedder()
    embeddings = model.encode(chunks, show_progress_bar=False)
    return embeddings.tolist()


# ═══════════════════════════════════════════════════════════
# 节点 6: upsert — 写入 Pinecone
# ═══════════════════════════════════════════════════════════

def upsert(chunks: list[str], vectors: list[list[float]],
           source_name: str) -> int:
    """批量写入 Pinecone，返回入库向量数"""
    import hashlib
    # Pinecone ID 只接受 ASCII，用 hash 转中文文件名
    safe_id = hashlib.md5(source_name.encode()).hexdigest()[:12]
    index = _get_index()
    to_upsert = []
    for i, (vec, chunk) in enumerate(zip(vectors, chunks)):
        cid = f"{safe_id}_{i}"
        to_upsert.append((cid, vec, {
            "source": source_name,
            "chunk_index": i,
            "text": chunk[:1000],
            "original_text": chunk[:2000],
        }))
    batch_size = 100
    for start in range(0, len(to_upsert), batch_size):
        batch = to_upsert[start:start + batch_size]
        index.upsert(vectors=batch)
    return len(to_upsert)


# ═══════════════════════════════════════════════════════════
# 节点 7: verify — 验证入库
# ═══════════════════════════════════════════════════════════

def verify(count: int) -> dict:
    """验证入库结果"""
    if count > 0:
        return {"status": "completed", "upserted": count}
    return {"status": "failed", "upserted": 0}
