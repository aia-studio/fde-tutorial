"""数据源盘点：先把清单摆到桌上，再答应对接。

运行：python src/ch02/source.py
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    owner: str
    access: str
    sensitive: tuple[str, ...] = ()
    verdict: str = "可接"
    note: str = ""


SOURCES: tuple[Source, ...] = (
    Source("工单主表", "PostgreSQL", "客服系统厂商", "只读从库", ("客户手机号", "客户地址")),
    Source("工单回复", "PostgreSQL", "客服系统厂商", "只读从库", ("坐席工号",)),
    Source("产品手册", "共享网盘", "产品部", "人工导出"),
    Source("历史邮件", "对象存储", "客服主管", "未授权", ("客户邮箱",), "暂缓", "无书面授权"),
)


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text: str, size: int) -> str:
    return text + " " * max(0, size - width(text))


def render_rows(rows: list[tuple[str, ...]]) -> str:
    widths = [max(width(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = []
    for row in rows:
        line = "  ".join(pad(cell, widths[i]) for i, cell in enumerate(row))
        out.append(line.rstrip())
    return "\n".join(out)


def inventory() -> list[Source]:
    return list(SOURCES)


def blocked() -> list[Source]:
    return [s for s in SOURCES if s.verdict != "可接"]


def sensitive_fields() -> dict[str, tuple[str, ...]]:
    return {s.name: s.sensitive for s in SOURCES if s.sensitive}


def report() -> str:
    rows: list[tuple[str, ...]] = [("数据源", "类型", "责任方", "接入方式", "敏感字段", "结论")]
    for s in SOURCES:
        rows.append((s.name, s.kind, s.owner, s.access,
                     "、".join(s.sensitive) or "无", s.verdict))
    return render_rows(rows)


def main() -> None:
    print("数据源盘点")
    print(report())
    print()
    print(f"可接 {len(inventory()) - len(blocked())} 个，暂缓 {len(blocked())} 个")
    for s in blocked():
        print(f"  暂缓 {s.name}：{s.note}，需 {s.owner} 出具书面授权")
    print()
    print("敏感字段清单")
    for name, fields in sensitive_fields().items():
        print(f"  {name}: {'、'.join(fields)}")


if __name__ == "__main__":
    main()
