"""Run model on JSONL dataset and compute embedding similarity.

This script uses the project's existing model stack only:
- `ContractRevisionAgent` / `ContractReviser` to generate model outputs
- `SentenceTransformer` model as configured in `CONFIG['model_config']['sentence_transformer']`

It does NOT add new external APIs beyond those already used in the repo.

Usage:
  python -m src.evaluation.run_model_vector_eval --input data/法律赛题训练集.jsonl --output report.json

"""

import os
import json
import argparse
from typing import List
import sys

# Ensure project root is on sys.path so `from src...` works when running as module/script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import CONFIG
# Use the lighter-weight ContractReviser directly to avoid initializing other heavy modules
from src.revision.reviser import ContractReviser
from src.legal.identifier import LegalClauseIdentifier
from src.legal.retriever import LegalReferenceRetriever

from sentence_transformers import SentenceTransformer
import math
import time
import concurrent.futures
import threading
import random


def read_jsonl(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            yield json.loads(ln)


def cosine(a: List[float], b: List[float]) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def main():
    parser = argparse.ArgumentParser(description="Run model and compute embedding similarity against reference outputs")
    parser.add_argument('--input', '-i', required=False, default='data/法律赛题训练集.jsonl', help='Path to JSONL dataset')
    parser.add_argument('--limit', '-n', type=int, default=0, help='Limit number of records (0 = all)')
    parser.add_argument('--output', '-o', default=None, help='Optional output JSON file for detailed results')
    parser.add_argument('--device', default='cpu', help='SentenceTransformer device (cpu or cuda)')
    parser.add_argument('--concurrency', '-c', type=int, default=24, help='Number of concurrent model calls (default: 24)')
    parser.add_argument('--retries', type=int, default=2, help='Number of retries per model call on failure')
    parser.add_argument('--backoff', type=float, default=1.0, help='Base backoff seconds for retries')
    parser.add_argument('--qps', type=float, default=4.0, help='Max requests per second (global rate limit)')
    parser.add_argument('--mode', choices=['contract', 'consultation'], default='contract', help='Run mode: contract (default) or consultation')
    args = parser.parse_args()

    dataset_path = args.input
    if not os.path.exists(dataset_path):
        # try relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_path = os.path.join(project_root, args.input)
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {args.input}")

    # Instantiate a lightweight reviser (avoids loading DocumentExtractor, LegalReferenceRetriever, etc.)
    reviser = ContractReviser(
        api_key=CONFIG['qwen_config']['api_key'],
        base_url=CONFIG['qwen_config']['base_url'],
        model=CONFIG['qwen_config'].get('model')
    )

    # Instantiate legal clause identifier and reference retriever according to CONFIG
    identifier = LegalClauseIdentifier(
        api_key=CONFIG['qwen_config']['api_key'],
        base_url=CONFIG['qwen_config']['base_url'],
        model=CONFIG['qwen_config'].get('model')
    )

    # Read Pinecone configuration (config.py uses 'pinecone_config')
    retriever_cfg = CONFIG.get('pinecone_config', CONFIG.get('retriever', {}))
    retriever = None
    try:
        pinecone_api_key = retriever_cfg.get('api_key') or retriever_cfg.get('pinecone_api_key')
        index_name = retriever_cfg.get('index_name')
        retriever = LegalReferenceRetriever(
            api_key=pinecone_api_key,
            index_name=index_name,
            model_name=CONFIG.get('model_config', {}).get('sentence_transformer', 'sentence-transformers/all-MiniLM-L6-v2'),
            hf_endpoint=retriever_cfg.get('hf_endpoint')
        )
    except Exception as e:
        print(f"初始化法律检索器失败，将进入离线模式: {e}")
        retriever = None

    # Load sentence-transformer model as configured in CONFIG
    st_model_name = CONFIG.get('model_config', {}).get('sentence_transformer', 'sentence-transformers/all-MiniLM-L6-v2')
    print(f"Loading SentenceTransformer model: {st_model_name} (device={args.device})")
    st = SentenceTransformer(st_model_name, device=args.device)

    # Read dataset into memory (respecting limit) to allow batching of reference embeddings
    records = []
    for i, rec in enumerate(read_jsonl(dataset_path), start=1):
        if args.limit and i > args.limit:
            break
        records.append(rec)

    if not records:
        print("No records to process.")
        return

    # Precompute reference embeddings in batch to avoid re-encoding per sample
    references = [r.get('output', '') or '' for r in records]
    print(f"Encoding {len(references)} reference texts (batch)...")
    try:
        ref_embeddings = st.encode(references, show_progress_bar=True, convert_to_numpy=True)
    except TypeError:
        # older sentence-transformers versions may not support convert_to_numpy arg
        ref_embeddings = st.encode(references)

    results = []
    total_sim = 0.0
    count = 0

    # Concurrently generate predictions using a ThreadPoolExecutor to parallelize network calls
    # Default concurrency is 24 (user requested). Can be overridden via CLI args.
    concurrency = int(args.concurrency)
    retries = int(args.retries)
    backoff = float(args.backoff)

    print(f"Generating predictions with concurrency={concurrency}, retries={retries}, backoff={backoff}s")

    # Simple token-bucket rate limiter to avoid bursty concurrent requests.
    class TokenBucket:
        def __init__(self, rate: float, capacity: float):
            self.rate = float(rate)
            self.capacity = float(capacity)
            self._tokens = float(capacity)
            self._last = time.time()
            self._lock = threading.Lock()

        def _refill(self):
            now = time.time()
            delta = now - self._last
            if delta <= 0:
                return
            self._tokens = min(self.capacity, self._tokens + delta * self.rate)
            self._last = now

        def consume(self, tokens: float = 1.0) -> bool:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                return False

        def wait_for_token(self):
            # busy-wait with small sleeps until a token is available
            while True:
                if self.consume(1.0):
                    return
                time.sleep(max(0.01, 1.0 / (self.rate * 4)))

    bucket = TokenBucket(rate=max(0.1, float(args.qps)), capacity=max(1.0, float(args.qps)))

    def build_consultation_prompt(input_text, references):
        """Construct a prompt for legal consultation mode.

        `input_text` is the user's question or case description.
        `references` is a list of reference dicts (each may have 'reference' and 'score').
        """
        ref_text = ''
        if references:
            parts = []
            for r in references:
                # r may come from retriever.query: contains 'clause','reference','score'
                parts.append(f"- {r.get('reference', 'N/A')} (相似度: {r.get('score', 0):.2f})")
            ref_text = "\n相关法律参考：\n" + "\n".join(parts)

        prompt = f"""下面是一位用户的法律咨询请求，请基于现有的法律条文参考给出明确、可执行的咨询回复：

用户咨询：\n{input_text}\n
{ref_text}

回答要求：
1) 给出简洁明确的法律意见或建议（不超过 400 字）。
2) 如果有适用的法律条文或要点，请引用并简短说明其适用理由；若无可用参考则说明依据的法律原则。
3) 标注是否需要进一步信息以给出更精确建议（列出 2-3 项）。

请仅返回咨询回复正文（不要返回多余的调试信息）。"""
        return prompt

    def generate_with_retries(idx, input_text, references):
        attempt = 0
        while attempt <= retries:
            try:
                # Respect global rate limit before calling the model API
                try:
                    bucket.wait_for_token()
                except Exception:
                    pass
                # For consultation mode we craft a consultation prompt and call the reviser's client directly
                if args.mode == 'consultation':
                    # Build consultation prompt
                    consult_prompt = build_consultation_prompt(input_text, references or [])
                    try:
                        completion = reviser.client.chat.completions.create(
                            model=reviser.model,
                            messages=[
                                {"role": "system", "content": "你是一个专业的法律咨询助手，回答要简洁、准确并引用相关法律条文。"},
                                {"role": "user", "content": consult_prompt}
                            ]
                        )
                        out = completion.choices[0].message.content
                    except Exception as e:
                        raise
                else:
                    # Pass the retrieved legal references to the reviser (contract mode)
                    out = reviser.revise(input_text, references or [])
                return idx, out
            except Exception as e:
                attempt += 1
                # If the error indicates rate limiting (429 or 'limit_requests'), extend backoff
                msg = str(e).lower()
                extra_sleep = 0.0
                if '429' in msg or 'rate' in msg or 'limit_requests' in msg:
                    extra_sleep = backoff * 4
                if attempt > retries:
                    print(f"Failed to generate for #{idx+1} after {retries} retries: {e}")
                    return idx, ''
                # add jitter to avoid thundering herd
                jitter = random.uniform(0, min(1.0, backoff))
                sleep_time = backoff * (2 ** (attempt - 1)) + extra_sleep + jitter
                print(f"Retry #{attempt} for #{idx+1} after error: {e}, sleeping {sleep_time:.2f}s (jitter={jitter:.2f})")
                time.sleep(sleep_time)

    predictions = [None] * len(records)
    gen_done = 0
    gen_lock = threading.Lock()

    # Precompute legal references for each record (identifier -> retriever.query)
    # Parallelize retrievals to speed up processing (bounded by `concurrency`)
    refs_per_record = [None] * len(records)

    def _compute_refs(i, rec):
        input_text = rec.get('input', '')
        try:
            if args.mode == 'contract':
                # throttle identification calls to avoid exceeding API rate limits
                try:
                    bucket.wait_for_token()
                except Exception:
                    pass
                identified = identifier.identify(input_text)
                clauses = identifier.extract_clauses(identified)
            else:
                # consultation mode: use full input as the single clause
                clauses = [input_text] if input_text else []

            if retriever and not retriever.offline_mode and clauses:
                # Apply token-bucket rate limiting for retrieval calls as well
                try:
                    bucket.wait_for_token()
                except Exception:
                    pass
                refs = retriever.query(clauses, top_k=3)
            else:
                refs = []
        except Exception as e:
            print(f"提取/检索参考条文失败 for idx {i}: {e}")
            refs = []
        return i, refs

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as retriever_exe:
        futs = {retriever_exe.submit(_compute_refs, i, rec): i for i, rec in enumerate(records)}
        for fut in concurrent.futures.as_completed(futs):
            try:
                i, refs = fut.result()
            except Exception as e:
                i = futs[fut]
                refs = []
                print(f"检索任务异常 idx={i}: {e}")
            refs_per_record[i] = refs

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as exe:
        futures = {exe.submit(generate_with_retries, idx, rec.get('input', ''), refs_per_record[idx]): idx for idx, rec in enumerate(records)}
        total = len(records)
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            try:
                ret_idx, pred = fut.result()
            except Exception as e:
                print(f"Unexpected error in future for idx {idx}: {e}")
                pred = ''
                ret_idx = idx
            predictions[ret_idx] = pred
            # Print live generation progress and id
            with gen_lock:
                gen_done += 1
                try:
                    rec_id = records[ret_idx].get('id')
                except Exception:
                    rec_id = ret_idx
                print(f"[generate] {gen_done}/{total} generated id={rec_id}")

    # Now batch-encode predictions in chunks and compute similarity against precomputed ref_embeddings
    batch_size = 16
    for start in range(0, len(predictions), batch_size):
        end = min(start + batch_size, len(predictions))
        batch_preds = [predictions[i] or '' for i in range(start, end)]
        try:
            pred_embs = st.encode(batch_preds, convert_to_numpy=True)
        except TypeError:
            pred_embs = st.encode(batch_preds)

        for j, emb in enumerate(pred_embs):
            idx = start + j
            rec = records[idx]
            ref_emb = ref_embeddings[idx]
            sim = float(cosine(list(emb), list(ref_emb)))
            results.append({
                'id': rec.get('id'),
                'input': rec.get('input', ''),
                'reference': rec.get('output', ''),
                'prediction': batch_preds[j],
                'embedding_cosine': sim
            })
            total_sim += sim
            count += 1
            print(f"#{idx+1} id={rec.get('id')} sim={sim:.4f}")

    avg_sim = (total_sim / count) if count else 0.0
    summary = {
        'total': count,
        'average_embedding_cosine': avg_sim
    }

    output = {'summary': summary, 'results_sample': results}

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Report written to {args.output}")
    else:
        print('\nSummary:')
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
