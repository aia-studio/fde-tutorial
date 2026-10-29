"""Ch05 融合：两路分数不可比，按名次做 RRF。"""

from __future__ import annotations

from ch04.answer import retrieve
from ch05.bm25 import search as bm25_search

RRF_K = 60


def rrf(rankings: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """rankings 是几组按名次排好的 id；每条得分按 1/(k+名次) 累加。"""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for i, key in enumerate(ranking, 1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + i)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def vector_search(question: str, k: int = 5, db_path: str | None = None) -> list[dict]:
    """只走向量一路，用于和三档链路做对照。"""
    kw = {"db_path": db_path} if db_path else {}
    return retrieve(question, k, **kw)


def hybrid_search(question: str, k: int = 5, pool: int = 20,
                  db_path: str | None = None) -> list[dict]:
    kw = {"db_path": db_path} if db_path else {}
    vec = vector_search(question, pool, db_path)
    lex = bm25_search(question, pool, **kw)
    meta: dict[str, dict] = {}
    vec_rank = {h["chunk_id"]: i for i, h in enumerate(vec, 1)}
    lex_rank = {h["chunk_id"]: i for i, h in enumerate(lex, 1)}
    for h in vec + lex:
        meta.setdefault(h["chunk_id"], h)
    fused = rrf([list(vec_rank), list(lex_rank)])
    out = []
    seen_ticket: set[str] = set()
    for cid, s in fused:
        if meta[cid]["ticket_no"] in seen_ticket:
            continue
        seen_ticket.add(meta[cid]["ticket_no"])
        item = dict(meta[cid])
        item["score"] = s
        item["vec_rank"] = vec_rank.get(cid, 0)
        item["lex_rank"] = lex_rank.get(cid, 0)
        out.append(item)
        if len(out) == k:
            break
    return out


def main() -> None:
    for q in ("机器开不了机指示灯不亮", "E-311 纸张尺寸不匹配"):
        vec = retrieve(q, 5)
        lex = bm25_search(q, 5)
        print(f"q={q}")
        print(f"  向量：{[h['ticket_no'] for h in vec]}")
        print(f"  字面：{[h['ticket_no'] for h in lex]}")
        print(f"  融合：{[h['ticket_no'] for h in hybrid_search(q, 5)]}")


if __name__ == "__main__":
    main()
