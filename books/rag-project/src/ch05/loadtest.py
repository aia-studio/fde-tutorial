"""延迟与并发：先看 P95，不看平均值。

模拟一条固定流量曲线，输出各并发档位的分位延迟与错误率。

运行：python src/ch05/loadtest.py
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

SEED = 11
REQUESTS = 200
P95_BUDGET = 2500        # 毫秒，合同约定的 P95 上限
ERROR_BUDGET = 0.02
SERVICE_CAPACITY = 8     # 同时在跑的请求上限，超过就排队


@dataclass
class Result:
    concurrency: int
    p50: float
    p95: float
    p99: float
    error_rate: float


def percentile(values: list[float], pct: float) -> float:
    """最近秩法：ceil(n × p) 那一档。"""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, math.ceil(pct / 100 * len(ordered)) - 1)
    return ordered[min(idx, len(ordered) - 1)]


def one_round(concurrency: int, rng: random.Random) -> Result:
    latencies: list[float] = []
    errors = 0
    for _ in range(REQUESTS):
        base = 900 + rng.gauss(0, 160)
        queue = max(0, concurrency - SERVICE_CAPACITY) * 120
        wait = rng.expovariate(1 / (60 + queue)) if concurrency > SERVICE_CAPACITY else 0
        latency = max(120.0, base + queue + wait)
        if latency > P95_BUDGET * 1.6:
            errors += 1
            latency = P95_BUDGET * 1.6
        latencies.append(latency)
    return Result(
        concurrency=concurrency,
        p50=percentile(latencies, 50),
        p95=percentile(latencies, 95),
        p99=percentile(latencies, 99),
        error_rate=errors / REQUESTS,
    )


def verdict(r: Result) -> str:
    if r.error_rate > ERROR_BUDGET:
        return "不达标（错误率）"
    if r.p95 > P95_BUDGET:
        return "不达标（P95）"
    return "达标"


def main() -> None:
    rng = random.Random(SEED)
    print(f"每档 {REQUESTS} 个请求，服务容量 {SERVICE_CAPACITY} 并发，"
          f"P95 预算 {P95_BUDGET} 毫秒")
    print(f"{'并发':>4}{'P50':>8}{'P95':>8}{'P99':>8}{'错误率':>8}  结论")
    for level in (1, 4, 8, 12, 16):
        r = one_round(level, rng)
        print(f"{r.concurrency:>4}{r.p50:>8.0f}{r.p95:>8.0f}{r.p99:>8.0f}"
              f"{r.error_rate:>8.2%}  {verdict(r)}")
    print()
    print("说明：并发 12 的 P50 还在一秒八，P95 已经越过预算。"
          "只看均值会漏掉这一档，用户投诉集中在长尾。")


if __name__ == "__main__":
    main()
