"""Ch05 重排：对融合后的候选再打一次分，用查询覆盖率与型号一致性。"""

from __future__ import annotations

import time

from ch04.answer import answer
from ch05.fuse import hybrid_search
from common.text import tokens


def _latin(toks: list[str]) -> set[str]:
    return {t for t in toks if t[0].isascii() and t[0].isalnum()}


def rerank(question: str, hits: list[dict], top_n: int = 5) -> list[dict]:
    q = tokens(question)
    q_set = set(q)
    q_latin = _latin(q)
    for h in hits:
        toks = tokens(h["text"])
        t_set = set(toks)
        cover = len(q_set & t_set) / max(len(q_set), 1)
        latin_hit = 1.0 if q_latin and q_latin <= _latin(toks) else 0.0
        model_hit = 1.0 if any(m.lower() in h["product"].lower() for m in q_latin) else 0.0
        h["confidence"] = round(cover, 3)
        h["rerank"] = round(cover + 0.6 * latin_hit + 0.3 * model_hit, 4)
    hits.sort(key=lambda h: h["rerank"], reverse=True)
    return hits[:top_n]


def build_retriever(k: int = 5, pool: int = 20):
    def _get(question: str, top: int = k) -> list[dict]:
        return rerank(question, hybrid_search(question, pool), top)
    return _get


def ask(question: str, k: int = 5) -> dict:
    return answer(question, k=k, retriever=build_retriever(k))


def main() -> None:
    for q in ("机器开不了机指示灯不亮", "HY-200 支架孔距", "换货要不要原包装"):
        t0 = time.perf_counter()
        fused = hybrid_search(q, 5)
        t1 = time.perf_counter()
        ranked = rerank(q, [dict(h) for h in fused])
        t2 = time.perf_counter()
        print(f"q={q}")
        print(f"  融合：{[h['ticket_no'] for h in fused]}")
        print(f"  重排：{[h['ticket_no'] for h in ranked]}")
        print(f"  耗时：融合 {(t1 - t0) * 1000:.1f} ms，重排 {(t2 - t1) * 1000:.2f} ms")
    r = ask("键盘进水失灵")
    print(f"ask → {r['answer'][:40]}")


if __name__ == "__main__":
    main()
