"""RAG 更新管线 — CLI 编排 7 个节点顺序执行"""
from . import nodes


def run_rag_update(*, url: str = "", file_path: str = "",
                   text: str = "", source_name: str = "",
                   chunk_size: int = 500) -> dict:
    """RAG 更新入口 — 三种输入归一:

    - url:       从 URL 下载
    - file_path: 从本地文件提取
    - text:      直接传入纯文本

    source_name 用于标记来源。返回 {status, source, chunks, upserted, errors}
    """
    errors = []

    try:
        # ── 1. 获取文本 ──
        if file_path:
            clean_text, source_name = nodes.file_extract(file_path, source_name)
            print(f"[1/7] 文件提取: {source_name} ({len(clean_text)} chars)")
        elif url:
            print(f"[1/7] 下载: {url}")
            raw = nodes.fetch(url)
            print(f"[2/7] 解析 ({len(raw)} bytes)")
            clean_text = nodes.parse(raw)
        elif text:
            clean_text = text
            print(f"[1/7] 直接传入 ({len(text)} chars)")
        else:
            return {"status": "failed", "errors": ["url / file_path / text 至少提供一个"]}

        # ── 3. 分块 ──
        print(f"[3/7] 分块...")
        chunks = nodes.chunk(clean_text, chunk_size)
        print(f"   → {len(chunks)} 块")

        # ── 4. 向量化 ──
        print(f"[4/7] 向量化...")
        vectors = nodes.embed(chunks)
        print(f"   → {len(vectors)} 个向量")

        # ── 5. 入库 ──
        print(f"[5/7] 写入 Pinecone...")
        count = nodes.upsert(chunks, vectors, source_name or "rag_update")
        print(f"   → {count} 条已入库")

        # ── 6. 验证 ──
        print(f"[6/7] 验证...")
        result = nodes.verify(count)
        result["source"] = source_name or url or "text"
        result["chunks"] = len(chunks)
        return result

    except Exception as e:
        errors.append(str(e))
        return {"status": "failed", "errors": errors, "chunks": 0, "upserted": 0}
