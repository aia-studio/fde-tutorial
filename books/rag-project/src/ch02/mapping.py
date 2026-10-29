"""字段映射与清洗：映射表进版本管理，不写在注释里。

运行：python src/ch02/mapping.py
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

TAG = re.compile(r"<[^>]+>")
PHONE = re.compile(r"1[3-9]\d{9}")
SPACE = re.compile(r"[ \t\u3000]+")

CITY = ("宁波", "苏州", "无锡", "常州", "杭州")


@dataclass(frozen=True)
class FieldMapping:
    source: str
    target: str
    rule: str


MAPPING: tuple[FieldMapping, ...] = (
    FieldMapping("ticket_no", "doc_id", "去空格并转大写，作为唯一键"),
    FieldMapping("title", "title", "去 HTML 标签，压缩空白"),
    FieldMapping("body", "content", "去 HTML 标签，手机号脱敏"),
    FieldMapping("customer", "customer_alias", "截取城市加客户简称，去掉全称"),
    FieldMapping("created_at", "created_at", "统一为 ISO 8601，保留到秒"),
    FieldMapping("status", "status", "收敛到已解决 / 处理中 / 已关闭"),
)


def strip_tags(text: str) -> str:
    return SPACE.sub(" ", TAG.sub("", text)).strip()


def mask_phone(text: str) -> str:
    return PHONE.sub(lambda m: m.group(0)[:3] + "****" + m.group(0)[-4:], text)


def normalize_time(text: str) -> str:
    return text.replace("/", "-").replace("T", " ").strip()


def alias_customer(name: str) -> str:
    """只留城市与简称，全称不进检索语料。"""
    city = next((c for c in CITY if name.startswith(c)), "其他")
    short = name[len(city):] if city != "其他" else name
    suffixes = ("有限公司", "股份有限公司", "机械", "精工", "新材")
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if short.endswith(suffix) and len(short) > len(suffix):
                short = short[: -len(suffix)]
                changed = True
    return f"{city}-{short}"


def apply(row: dict[str, str]) -> dict[str, str]:
    """按 MAPPING 逐字段转换，未登记的源字段直接报错。"""
    missing = unmapped(row.keys())
    if missing:
        raise KeyError(f"源字段未登记映射：{'、'.join(missing)}")
    return {
        "doc_id": row["ticket_no"].strip().upper(),
        "title": strip_tags(row["title"]),
        "content": mask_phone(strip_tags(row["body"])),
        "customer_alias": alias_customer(row["customer"]),
        "created_at": normalize_time(row["created_at"]),
        "status": row["status"],
    }


def mapped_sources() -> set[str]:
    return {m.source for m in MAPPING}


def unmapped(source_fields) -> list[str]:
    return sorted(set(source_fields) - mapped_sources())


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text: str, size: int) -> str:
    return text + " " * max(0, size - width(text))


def report() -> str:
    rows = [("源字段", "目标字段", "规则")]
    rows += [(m.source, m.target, m.rule) for m in MAPPING]
    widths = [max(width(r[i]) for r in rows) for i in range(3)]
    return "\n".join("  ".join(pad(c, widths[i]) for i, c in enumerate(r)).rstrip()
                     for r in rows)


def main() -> None:
    print("字段映射表")
    print(report())
    print()

    row = {
        "ticket_no": " hy-1001 ",
        "title": "设备<em>无法</em>开机",
        "body": "<p>通电后指示灯不亮。客户电话 13800001111。</p>",
        "customer": "宁波华远机械有限公司",
        "created_at": "2026/03/02 09:14",
        "status": "已解决",
    }
    print("清洗前：", row)
    print("清洗后：", apply(row))
    print()
    print(f"覆盖检查：{len(mapped_sources())} 个源字段全部有映射，"
          f"未映射 {len(unmapped(row.keys()))} 个")


if __name__ == "__main__":
    main()
