"""灰度发布：每一档都要有继续或回滚的判据。

运行：python src/ch06/canary.py
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

MAX_ERROR = 0.02
MAX_P95 = 2500
MAX_ABSTAIN = 0.20
MAX_HANDOFF = 0.08


@dataclass(frozen=True)
class Sample:
    stage: str
    traffic: int          # 百分比
    error: float
    p95: int
    abstain: float
    handoff: float
    note: str = ""


SAMPLES: tuple[Sample, ...] = (
    Sample("第一档", 1, 0.004, 1450, 0.12, 0.03),
    Sample("第二档", 5, 0.006, 1680, 0.14, 0.04),
    Sample("第三档", 25, 0.009, 2680, 0.15, 0.05, "并发上来了，P95 超预算"),
    Sample("第三档复测", 25, 0.006, 1980, 0.14, 0.04, "加了一层候选缓存"),
    Sample("第四档", 50, 0.008, 2100, 0.15, 0.05),
    Sample("全量", 100, 0.011, 2260, 0.16, 0.06),
)


def decide(s: Sample) -> tuple[str, str]:
    if s.error > MAX_ERROR:
        return "回滚", f"错误率 {s.error:.2%} 超过 {MAX_ERROR:.0%}"
    if s.p95 > MAX_P95:
        return "停在当前档", f"P95 {s.p95} 毫秒超过 {MAX_P95} 毫秒"
    if s.abstain > MAX_ABSTAIN:
        return "停在当前档", f"拒答率 {s.abstain:.0%} 超过 {MAX_ABSTAIN:.0%}"
    if s.handoff > MAX_HANDOFF:
        return "停在当前档", f"转人工 {s.handoff:.0%} 超过 {MAX_HANDOFF:.0%}"
    return "放量", "四项指标都在预算内"


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def main() -> None:
    print(f"判据：错误率 ≤ {MAX_ERROR:.0%}，P95 ≤ {MAX_P95} 毫秒，"
          f"拒答率 ≤ {MAX_ABSTAIN:.0%}，转人工 ≤ {MAX_HANDOFF:.0%}")
    print(f"{pad('档位', 12)}{'流量':>5}{'错误率':>9}{'P95':>7}{'拒答':>7}{'转人工':>8}  决策")
    for s in SAMPLES:
        action, reason = decide(s)
        print(f"{pad(s.stage, 12)}{s.traffic:>4}%{s.error:>9.2%}{s.p95:>7}"
              f"{s.abstain:>7.0%}{s.handoff:>8.0%}  {action}")
        print(f"{'':12}{reason}")
        if s.note:
            print(f"{'':12}现场记录：{s.note}")

    stops = [s.stage for s in SAMPLES if decide(s)[0] == "停在当前档"]
    rolls = [s.stage for s in SAMPLES if decide(s)[0] == "回滚"]
    print()
    print(f"全线 {len(SAMPLES)} 档，停留 {len(stops)} 次"
          f"（{'、'.join(stops) or '无'}），回滚 {len(rolls)} 次")


if __name__ == "__main__":
    main()
