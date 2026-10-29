"""Ch06 成本：按上下文与答案长度估 token，再算钱与延迟分位。"""

from __future__ import annotations

import math
import time

from ch05.rerank import ask, build_retriever
from ch06.eval import load_set
from common.text import tokens

PRICE_IN = 0.004    # 示例单价：元 / 千 token，输入
PRICE_OUT = 0.012   # 示例单价：元 / 千 token，输出
CONTEXT_K = 3


def estimate_tokens(text: str) -> int:
    """粗略口径：一个汉字算一个 token，英文与数字整词算一个。"""
    latin = sum(1 for t in tokens(text) if t[0].isascii())
    return len(text) - latin * 3 + latin


def cost_of(prompt_tokens: int, answer_tokens: int) -> float:
    return (prompt_tokens * PRICE_IN + answer_tokens * PRICE_OUT) / 1000


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[idx]


def measure(items: list[dict], k: int = CONTEXT_K) -> list[dict]:
    get = build_retriever(k)
    rows = []
    for item in items:
        t0 = time.perf_counter()
        result = ask(item["question"], k=k)
        elapsed = (time.perf_counter() - t0) * 1000
        ctx = "".join(h["text"] for h in get(item["question"]))
        prompt_tokens = estimate_tokens(item["question"]) + estimate_tokens(ctx)
        answer_tokens = estimate_tokens(result["answer"])
        rows.append({"id": item["id"], "question": item["question"],
                     "prompt": prompt_tokens, "answer": answer_tokens,
                     "cost": cost_of(prompt_tokens, answer_tokens),
                     "ms": round(elapsed, 1), "refused": result["refused"]})
    return rows


def main() -> None:
    rows = measure(load_set())
    print(f"{'题号':<5}{'输入':<8}{'答案':<6}{'成本(元)':<12}{'耗时(ms)':<9}问题")
    for r in rows[:5]:
        print(f"{r['id']:<5}{r['prompt']:<8}{r['answer']:<6}{r['cost']:<12.6f}{r['ms']:<9}{r['question']}")
    lat = [r["ms"] for r in rows]
    total = sum(r["cost"] for r in rows)
    print()
    print(f"题数 {len(rows)}")
    print(f"平均上下文 {sum(r['prompt'] for r in rows) // len(rows)} token")
    print(f"单次成本 平均 {total / len(rows):.6f} 元，{len(rows)} 题合计 {total:.6f} 元")
    print(f"延迟 p50 {percentile(lat, 0.5):.1f} ms，p95 {percentile(lat, 0.95):.1f} ms，"
          f"最大 {max(lat):.1f} ms")


if __name__ == "__main__":
    main()
