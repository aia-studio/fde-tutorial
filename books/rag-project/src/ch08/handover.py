"""交接演练：找一个没参与项目的人，照文档走一遍，卡住的步骤就是缺口。

演练不通过的交接，签字也不算交完。文档没人照着跑过，等于没写。

运行（在 src/ 下）：python -m ch08.handover
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace

DONE, STUCK, UNTRIED = "通过", "卡住", "未试"


@dataclass(frozen=True)
class Drill:
    task: str
    section: str
    result: str
    note: str = ""
    patch: str = ""


DRILLS: tuple[Drill, ...] = (
    Drill("启动服务", "怎么起", STUCK, "缺 DB_DSN 环境变量，文档没列",
          "在「怎么起」补一张环境变量表：变量名、示例值、谁能给"),
    Drill("更新一条语料并生效", "怎么改", STUCK, "重建命令少了库名参数",
          "把索引重建写成完整命令行，含参数含义"),
    Drill("用链路号查一次故障", "怎么查", DONE),
    Drill("回退到上一版", "怎么回滚", UNTRIED, "只写了「回退镜像」，没有命令",
          "补三条命令与回退成功判据"),
    Drill("调一条字段映射并验证", "怎么改", DONE),
    Drill("看告警并判断要不要处理", "怎么查", DONE),
)

FIXES = {
    "启动服务": "按补的环境变量表重跑",
    "更新一条语料并生效": "按完整命令行重跑",
    "回退到上一版": "按补的回退命令演练一次",
}


def by_result(drills: tuple[Drill, ...], result: str) -> list[Drill]:
    return [d for d in drills if d.result == result]


def after_patch(drills: tuple[Drill, ...]) -> tuple[Drill, ...]:
    return tuple(replace(d, result=DONE, note=FIXES[d.task]) if d.result != DONE else d
                 for d in drills)


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def show(title: str, drills: tuple[Drill, ...]) -> None:
    print(title)
    print(pad("演练项", 26) + pad("文档位置", 14) + f"{'结果':<6}说明")
    for d in drills:
        print(pad(d.task, 26) + pad(d.section, 14) + f"{d.result:<6}{d.note}")


def main() -> None:
    show("交接演练（第一轮，新同事独立操作）", DRILLS)
    done = len(by_result(DRILLS, DONE))
    print()
    print(f"完成 {done}/{len(DRILLS)}，卡住 {len(by_result(DRILLS, STUCK))}，"
          f"未试 {len(by_result(DRILLS, UNTRIED))}")

    gaps = [d for d in DRILLS if d.result != DONE]
    print("文档缺口与补法：")
    for d in gaps:
        print(f"  - {d.task}：{d.patch}")

    print()
    second = after_patch(DRILLS)
    show("交接演练（补文档后，换一位新同事）", second)
    left = [d for d in second if d.result != DONE]
    print()
    if left:
        print(f"仍有 {len(left)} 项没过，交接不算完成。")
    else:
        print("结论：交接完成。两位新同事都能独立走完全部演练项。")
        print("演练记录归档进交接文档，卡点与补法一并留档。")


if __name__ == "__main__":
    main()
