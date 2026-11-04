"""Ch08 版本对比与灰度：同一批会话、两套链路、逐项对照。

对比的规矩只有一条：除被改的那一项，其余全部相同。
跑完先看变差的项，再看变好的项；有一项明显变差就不该放量。
"""

from __future__ import annotations

import time
import zlib

from ch07.eval_multi import CASES
from ch07.pipeline import ask, conversation, retriever

K = 5


def run(cases: list[dict], use_session: bool) -> list[dict]:
    get = retriever(K)
    rows: list[dict] = []
    for case in cases:
        conv = conversation(K) if use_session else None
        for i, (question, gold) in enumerate(case["rounds"], 1):
            t0 = time.perf_counter()
            if conv is None:
                result = ask(question, K)
                query = question
            else:
                turn = conv.ask(question)
                result, query = {"refused": turn.refused}, turn.rewritten
            cost = (time.perf_counter() - t0) * 1000
            hits = get(query)
            rank = next((j for j, h in enumerate(hits, 1) if h["ticket_no"] == gold), 0)
            refused = bool(result["refused"])
            rows.append({"case": case["id"], "round": i, "rank": rank,
                         "refused": refused, "right": rank == 1 and not refused,
                         "recall": 0 < rank <= K, "ms": cost})
    return rows


def summarize(rows: list[dict]) -> dict:
    times = sorted(r["ms"] for r in rows)
    cases = sorted({r["case"] for r in rows})
    return {
        "right": sum(1 for r in rows if r["right"]),
        "total": len(rows),
        "recall": sum(1 for r in rows if r["recall"]),
        "refused": sum(1 for r in rows if r["refused"]),
        "turn1": sum(1 for r in rows if r["round"] == 1 and r["right"]),
        "passed": sum(1 for c in cases if all(r["right"] for r in rows if r["case"] == c)),
        "cases": len(cases),
        "p50": times[len(times) // 2],
        "p95": times[min(len(times) - 1, int(len(times) * 0.95))],
    }


def compare(cases: list[dict], plans: list[tuple[str, bool]]) -> list[dict]:
    return [{"name": name, "mode": use, **summarize(run(cases, use))} for name, use in plans]


def bucket(session: str, percent: int = 10) -> str:
    """按会话号分桶：同一个会话始终落同一边，避免用户看到两套答案。"""
    return "B" if zlib.crc32(session.encode("utf-8")) % 100 < percent else "A"


def main() -> None:
    rows = compare(CASES, [("A 单轮", False), ("B 会话", True)])
    print(f"{'版本':<8}{'答对':<8}{'前五':<8}{'误拒':<8}{'首轮':<8}{'会话通过':<10}{'p50':<8}p95")
    for r in rows:
        print(f"{r['name']:<8}{r['right']}/{r['total']:<5}{r['recall']}/{r['total']:<5}"
              f"{r['refused']}/{r['total']:<5}{r['turn1']}/{r['cases']:<5}"
              f"{r['passed']}/{r['cases']:<7}{r['p50']:.1f}ms {r['p95']:.1f}ms")

    a, b = rows
    print()
    print(f"答对 {b['right'] - a['right']:+d}，会话通过 {b['passed'] - a['passed']:+d}，"
          f"误拒 {b['refused'] - a['refused']:+d}，p50 {b['p50'] - a['p50']:+.1f}ms")

    sessions = [f"S-{2000 + i}" for i in range(100)]
    share = sum(1 for s in sessions if bucket(s) == "B")
    print()
    print(f"灰度：{share}/{len(sessions)} 个会话进 B 版，同一会话号始终落同一边")
    print("前 8 个：" + " ".join(f"{s[-4:]}:{bucket(s)}" for s in sessions[:8]))


if __name__ == "__main__":
    main()
