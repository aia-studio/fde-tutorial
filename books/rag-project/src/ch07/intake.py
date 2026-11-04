"""新业务线接入评估：四项打分，把「不接」也写成结论。

评估表只在接入前填一次，作用是让客户自己看到哪条线缺什么。
总分高不等于该接，卡在关键项上的一律先补条件。

运行（在 src/ 下）：python -m ch07.intake
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

DIMENSIONS = ("data", "auth", "reuse", "owner")
LABELS = {
    "data": "数据就绪",
    "auth": "权限可得",
    "reuse": "链路复用",
    "owner": "业务负责人",
}
HINTS = {
    "data": "数据来源还没有可导出的结构化接口",
    "auth": "谁能看哪一批数据没有书面结论",
    "reuse": "问答对象与一期语料不重叠，等于新建一套",
    "owner": "客户侧没有能签字确认口径的人",
}

ENTER, WATCH, DECLINE = 6, 4, 3


@dataclass(frozen=True)
class Request:
    name: str
    scores: dict[str, int]
    note: str = ""

    @property
    def total(self) -> int:
        return sum(self.scores.values())

    @property
    def weakest(self) -> str:
        return min(self.scores, key=lambda k: self.scores[k])

    @property
    def verdict(self) -> str:
        if self.scores[self.weakest] == 0:
            return "不接"
        if self.total >= ENTER:
            return "接入"
        if self.total >= WATCH:
            return "观察"
        return "不接"


REQUESTS: tuple[Request, ...] = (
    Request("售后备件问答", {"data": 2, "auth": 1, "reuse": 2, "owner": 2},
            "备件成本价只对内部开放"),
    Request("财务报销政策", {"data": 2, "auth": 1, "reuse": 1, "owner": 2},
            "按成本中心分权"),
    Request("员工 IT 工单", {"data": 1, "auth": 2, "reuse": 1, "owner": 1},
            "工单系统只提供页面，没有导出接口"),
    Request("供应商合同条款", {"data": 0, "auth": 0, "reuse": 1, "owner": 1},
            "合同为扫描件，且保密范围未定"),
)


def evaluate(r: Request) -> tuple[str, str]:
    """返回（结论，卡点说明）。"""
    if r.verdict == "接入":
        return "接入", f"四项均达线，{r.note}"
    if r.verdict == "观察":
        return "观察", f"卡在{HINTS[r.weakest]}；{r.note}"
    return "不接", f"卡在{HINTS[r.weakest]}；{r.note}"


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def main() -> None:
    head = pad("业务线", 16) + "".join(f"{LABELS[d]:>6}" for d in DIMENSIONS)
    print(head + f"{'合计':>6}  结论")
    for r in REQUESTS:
        verdict, why = evaluate(r)
        row = pad(r.name, 16) + "".join(f"{r.scores[d]:>6}" for d in DIMENSIONS)
        print(f"{row}{r.total:>6}  {verdict}")
        print(f"{'':16}{why}")

    order = [r.name for r in REQUESTS if r.verdict == "接入"]
    print()
    print(f"接入 {len(order)} 条：{'、'.join(order)}")
    print(f"观察 {sum(1 for r in REQUESTS if r.verdict == '观察')} 条，"
          f"不接 {sum(1 for r in REQUESTS if r.verdict == '不接')} 条")
    print("结论先给客户看，再谈排期。客户改口径，分数跟着改，不另开一张表。")


if __name__ == "__main__":
    main()
