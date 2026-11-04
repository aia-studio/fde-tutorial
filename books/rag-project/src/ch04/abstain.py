"""拒答：证据不足时说答不了，而不是编一个。

运行：python src/ch04/abstain.py
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

MIN_SCORE = 0.30
MIN_TERMS = 2

PHRASES = {
    "no_evidence": "这个工单库里没有查到相关记录，建议转人工确认。",
    "low_match": "找到的内容与问题关联不大，为避免误导，先不给结论。",
    "conflict": "查到两条互相矛盾的处理记录，需要客服主管确认后再答。",
}


@dataclass(frozen=True)
class Evidence:
    name: str
    top_score: float
    support_terms: int
    conflict: bool = False


CASES: list[Evidence] = [
    Evidence("轴承缺油", 0.62, 4),
    Evidence("换刀停顿", 0.41, 3),
    Evidence("滤网堵塞", 0.35, 2),
    Evidence("模糊提问", 0.24, 3),
    Evidence("只对一个词", 0.38, 1),
    Evidence("两条记录矛盾", 0.55, 3, True),
]


def decide(ev: Evidence) -> str:
    """先看冲突，再看分数，最后看支撑词数。顺序不能反。"""
    if ev.conflict:
        return "conflict"
    if ev.top_score < MIN_SCORE:
        return "no_evidence"
    if ev.support_terms < MIN_TERMS:
        return "low_match"
    return "answer"


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def main() -> None:
    print(f"阈值：分数 ≥ {MIN_SCORE}，支撑词 ≥ {MIN_TERMS}，冲突优先")
    print(f"{pad('用例', 14)}{pad('分数', 8)}{pad('支撑词', 8)}冲突  结论")
    counts: dict[str, int] = {}
    for ev in CASES:
        action = decide(ev)
        counts[action] = counts.get(action, 0) + 1
        mark = "是" if ev.conflict else "否"
        label = "作答" if action == "answer" else f"拒答（{action}）"
        print(f"{pad(ev.name, 14)}{pad(f'{ev.top_score:.2f}', 8)}"
              f"{pad(str(ev.support_terms), 8)}{pad(mark, 6)}{label}")

    print()
    print("统计：" + "，".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print()
    print("对客话术（需客户签字）")
    for key, phrase in PHRASES.items():
        print(f"  {key}: {phrase}")


if __name__ == "__main__":
    main()
