"""监控与告警：只看可用性会漏掉「答得多但答错」。

用一天的埋点算四项指标，再按阈值触发告警。

运行：python src/ch06/monitor.py
"""

from __future__ import annotations

from dataclasses import dataclass

REQUESTS = 1000
MAX_ABSTAIN = 0.20
MIN_CITATION_CLICK = 0.10
MAX_EMPTY_RECALL = 0.15
MAX_ERROR = 0.02
MAX_P95 = 2500


@dataclass
class Metrics:
    requests: int
    answered: int
    abstained: int
    errors: int
    empty_recall: int
    citation_click: int
    p95: int

    @property
    def availability(self) -> float:
        return (self.requests - self.errors) / self.requests

    @property
    def abstain_rate(self) -> float:
        return self.abstained / self.requests

    @property
    def empty_rate(self) -> float:
        return self.empty_recall / self.requests

    @property
    def click_rate(self) -> float:
        return self.citation_click / max(self.answered, 1)

    @property
    def error_rate(self) -> float:
        return self.errors / self.requests


def snapshot() -> Metrics:
    """一天的埋点汇总，固定值便于逐日对比。"""
    answered = 830
    abstained = 150
    errors = REQUESTS - answered - abstained
    return Metrics(REQUESTS, answered, abstained, errors,
                   empty_recall=168, citation_click=282, p95=2180)


def alerts(m: Metrics) -> list[str]:
    out: list[str] = []
    if m.error_rate > MAX_ERROR:
        out.append(f"错误率 {m.error_rate:.2%} 超阈值")
    if m.p95 > MAX_P95:
        out.append(f"P95 {m.p95} 毫秒超阈值")
    if m.abstain_rate > MAX_ABSTAIN:
        out.append(f"拒答率 {m.abstain_rate:.1%} 超阈值")
    if m.empty_rate > MAX_EMPTY_RECALL:
        out.append(f"空召回 {m.empty_rate:.1%} 超阈值")
    if m.click_rate < MIN_CITATION_CLICK:
        out.append(f"引用点击率 {m.click_rate:.1%} 低于下限")
    return out


def main() -> None:
    m = snapshot()
    print("当日指标")
    print(f"  请求 {m.requests} 次，作答 {m.answered}，拒答 {m.abstained}，错误 {m.errors}")
    print(f"  可用性      {m.availability:.2%}")
    print(f"  拒答率      {m.abstain_rate:.1%}")
    print(f"  空召回率    {m.empty_rate:.1%}")
    print(f"  引用点击率  {m.click_rate:.1%}")
    print(f"  P95         {m.p95} 毫秒")
    print()
    items = alerts(m)
    if items:
        print("告警")
        for item in items:
            print(f"  ✗ {item}")
    else:
        print("告警：无，四项指标都在阈值内")

    print()
    print("为什么盯后三项：可用性满分时，答案仍可能是「查不到」或「答了没人点」。"
          "只报警可用性，等于放弃质量。")


if __name__ == "__main__":
    main()
