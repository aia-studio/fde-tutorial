"""最终验收：签字看证据包，不看演示。

每一项都要能被第三个人按同样步骤复测一次。演示只能证明「刚才那一刻是好的」。

运行（在 src/ 下）：python -m ch08.signoff
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace

PASS, TODO = "通过", "待补"


@dataclass(frozen=True)
class Item:
    name: str
    evidence: str
    repro: bool
    status: str
    signer: str
    gap: str = ""


ITEMS: tuple[Item, ...] = (
    Item("范围与口径", "二期范围表 v3", True, PASS, "业务主管"),
    Item("权限隔离", "越权扫描记录", True, PASS, "客户信息安全"),
    Item("索引升级", "影子比对报告", True, PASS, "客户技术负责人"),
    Item("回答质量", "二十条样本逐条结论", True, TODO, "业务主管",
         "样本表缺两条，补跑后再交"),
    Item("监控告警", "告警规则截图", False, TODO, "客户运维",
         "截图不可复测，改为给出查询语句与当前值"),
    Item("交接演练", "演练记录", True, TODO, "客户技术负责人",
         "尚未演练"),
)

FIXES = {
    "回答质量": ("补跑两条样本并写结论", "二十条样本逐条结论 v2", True, PASS, ""),
    "监控告警": ("把截图换成查询语句与当日取值", "告警规则查询语句 + 当日取值", True, PASS, ""),
    "交接演练": ("按交接文档完整走一遍并记录卡点", "演练记录 v1", True, PASS, ""),
}


def blocked(items: tuple[Item, ...]) -> list[Item]:
    return [i for i in items if i.status != PASS or not i.repro or not i.signer]


def apply_fixes(items: tuple[Item, ...]) -> tuple[Item, ...]:
    out = []
    for i in items:
        fix = FIXES.get(i.name)
        if fix and i.status != PASS:
            _, evidence, repro, status, gap = fix
            out.append(replace(i, evidence=evidence, repro=repro, status=status, gap=gap))
        else:
            out.append(i)
    return tuple(out)


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def show(title: str, items: tuple[Item, ...]) -> None:
    print(title)
    print(pad("验收项", 12) + pad("证据", 32) + f"{'可复测':<7}{'结论':<6}签字人")
    for i in items:
        print(pad(i.name, 12) + pad(i.evidence, 32)
              + f"{'是' if i.repro else '否':<7}{i.status:<6}{i.signer}")


def main() -> None:
    show("终验清单（第一轮）", ITEMS)
    first = blocked(ITEMS)
    print()
    print(f"阻断 {len(first)} 项，不能签字：")
    for i in first:
        print(f"  - {i.name}：{i.gap or '签字人未定'}")

    print()
    second = apply_fixes(ITEMS)
    show("终验清单（补证后）", second)
    left = blocked(second)
    print()
    if left:
        print(f"仍有 {len(left)} 项未过，继续补：{'、'.join(i.name for i in left)}")
    else:
        print("结论：可签字。逐项复测通过，签字人齐。")
        print("签字顺序：业务主管 → 客户信息安全 → 客户技术负责人。任何一项缺证据，签字页不发起。")


if __name__ == "__main__":
    main()
