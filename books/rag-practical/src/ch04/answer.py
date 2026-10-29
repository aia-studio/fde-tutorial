"""Ch04 问答：先检索，再判断该不该答，最后给出带原文的答案。"""

from __future__ import annotations

import re
import sqlite3
from functools import lru_cache

from ch03.search import search
from ch04.cite import make_citation, verify
from common.text import tokens
from common.paths import INDEX_DB

MIN_COVERAGE = 0.35      # 查询词在语料里的覆盖率，低于它算范围外
MIN_SCORE = 0.15         # Top-1 相似度低于它算没有证据
POLICY_WORDS = ("保修", "质保", "延保", "退", "换", "发票", "凭证", "价格", "报价", "费用")
DURATION = re.compile(r"([一二三四五六七八九十两\d]+)\s*(年|个月)")

REFUSALS = {
    "out_of_scope": "这个问题不在现有工单的范围里。补充设备型号与现象，或者转人工客服登记服务单。",
    "no_evidence": "现有工单里没有能支撑答案的记录。补充型号、错误码或现象细节，或者转人工登记。",
    "need_model": "这条要按型号分开看，不同型号的处理不一样。请补充型号或机身序列号。",
    "conflict": "现有两条记录的口径不一致。按出货批次区分，请提供序列号确认批次，或转人工确认。",
}


@lru_cache(maxsize=4)
def _vocab(db_path: str, mtime: float) -> frozenset[str]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT text FROM chunks").fetchall()
    conn.close()
    vocab: set[str] = set()
    for (text,) in rows:
        vocab.update(tokens(text))
    return frozenset(vocab)


def coverage(question: str, db_path: str = str(INDEX_DB)) -> float:
    import os

    ts = tokens(question)
    if not ts:
        return 0.0
    vocab = _vocab(db_path, os.path.getmtime(db_path))
    return sum(1 for t in ts if t in vocab) / len(ts)


def _products(db_path: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT DISTINCT product FROM chunks").fetchall()
    conn.close()
    return [r[0] for r in rows if r[0] != "通用"]


def _split_product(product: str) -> tuple[str, str]:
    """'HY-100 显示器' → ('HY-100', '显示器')。"""
    parts = product.split(" ", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (product, "")


def _need_model(question: str, db_path: str) -> bool:
    if not any(w in question for w in POLICY_WORDS):
        return False
    kinds = {_split_product(p)[1] for p in _products(db_path)}
    models = {_split_product(p)[0] for p in _products(db_path)}
    if any(m in question for m in models):
        return False
    return any(k and k in question for k in kinds)


def _conflict(hits: list[dict]) -> bool:
    """同一产品、来自不同工单的保修时长互相不一致。"""
    if len(hits) < 2:
        return False
    product = hits[0]["product"]
    by_ticket: dict[str, set[str]] = {}
    for h in hits:
        if h["product"] != product:
            continue
        found = {"".join(m) for m in DURATION.findall(h["text"])}
        if found:
            by_ticket.setdefault(h["ticket_no"], set()).update(found)
    if len(by_ticket) < 2:
        return False
    values = [v for vs in by_ticket.values() for v in vs]
    return len(set(values)) > 1


def retrieve(question: str, k: int = 5, **kw) -> list[dict]:
    return search(question, k, **kw)


def answer(question: str, k: int = 5, retriever=None, db_path: str = str(INDEX_DB)) -> dict:
    get = retriever or retrieve
    out = {"question": question, "answer": "", "citations": [], "refused": False,
           "reason": "", "hits": []}
    if coverage(question, db_path) < MIN_COVERAGE:
        out.update(refused=True, reason="out_of_scope", answer=REFUSALS["out_of_scope"])
        return out

    hits = get(question, k)
    out["hits"] = [{"ticket_no": h["ticket_no"], "chunk_id": h["chunk_id"],
                    "score": round(h.get("score", 0.0), 3)} for h in hits]
    top_conf = hits[0].get("confidence", hits[0].get("score", 0.0)) if hits else 0.0
    if not hits or top_conf < MIN_SCORE:
        out.update(refused=True, reason="no_evidence", answer=REFUSALS["no_evidence"])
        return out
    if _need_model(question, db_path):
        out.update(refused=True, reason="need_model", answer=REFUSALS["need_model"])
        return out
    if _conflict(hits):
        out.update(refused=True, reason="conflict", answer=REFUSALS["conflict"])
        return out

    citation = make_citation(hits[0], question)
    out["answer"] = citation["quote"]
    out["citations"] = [citation]
    return out


def verify_citations(result: dict, sources: dict[str, str]) -> bool:
    """逐条回查：引文必须能在对应块的原文里找到。"""
    return all(verify(c["quote"], sources.get(c["chunk_id"], "")) for c in result["citations"])


def main() -> None:
    cases = ["HY-100 保修几年", "显示器保修几年", "你们支持比特币付款吗", "换货要不要原包装"]
    for q in cases:
        r = answer(q)
        flag = f"拒答({r['reason']})" if r["refused"] else "作答"
        print(f"q={q}\n  {flag} → {r['answer'][:48]}")
        if r["citations"]:
            print(f"  引用：{r['citations'][0]['ticket_no']}｜{r['citations'][0]['quote'][:32]}")


if __name__ == "__main__":
    main()
