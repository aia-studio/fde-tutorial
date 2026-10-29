"""数据质量验收：抽样十条零差异才算过。

运行：python src/ch02/check.py
"""

from __future__ import annotations

import re
import sqlite3
import tempfile
from pathlib import Path

from ch02 import db, mapping

HAN = re.compile(r"[\u4e00-\u9fff]")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$")
TAG = re.compile(r"<[^>]+>")
FULL_PHONE = re.compile(r"1[3-9]\d{9}")

SAMPLE_SIZE = 10


def load_rows(path: Path, limit: int) -> list[dict[str, str]]:
    conn: sqlite3.Connection = db.connect_readonly(str(path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "select * from tickets order by ticket_no limit ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def checks(src: dict[str, str], cleaned: dict[str, str]) -> list[str]:
    """独立复算，不复用 mapping 的成品结果。"""
    problems: list[str] = []
    src_han = "".join(HAN.findall(TAG.sub("", src["body"])))
    out_han = "".join(HAN.findall(cleaned["content"]))
    if src_han != out_han:
        problems.append("正文汉字序列与源不一致")
    if TAG.search(cleaned["content"]) or TAG.search(cleaned["title"]):
        problems.append("仍有 HTML 标签")
    if FULL_PHONE.search(cleaned["content"]):
        problems.append("手机号未脱敏")
    if not ISO.match(cleaned["created_at"]):
        problems.append("时间格式不统一")
    if not cleaned["doc_id"].isupper():
        problems.append("单号未转大写")
    if len(cleaned["content"]) < 10:
        problems.append("正文过短")
    return problems


def main() -> None:
    demo = Path(tempfile.gettempdir()) / "huayang_tickets_demo.sqlite"
    db.build_demo(demo)
    rows = load_rows(demo, SAMPLE_SIZE)
    print(f"数据质量验收：抽样 {len(rows)} 条，固定取单号最小的十条")

    diffs = 0
    for src in rows:
        cleaned = mapping.apply(src)
        problems = checks(src, cleaned)
        diffs += len(problems)
        mark = "一致" if not problems else "差异：" + "；".join(problems)
        print(f"  {cleaned['doc_id']}  汉字 {len(HAN.findall(cleaned['content'])):>3}  "
              f"{cleaned['customer_alias']:<10}{mark}")

    status = "通过" if diffs == 0 else "不通过"
    print()
    print(f"差异合计 {diffs} 处，结论：{status}")

    total = load_rows(demo, 1000)
    empty = [r["ticket_no"] for r in total if not r["body"].strip()]
    dup = len(total) - len({r["ticket_no"] for r in total})
    print(f"全量 {len(total)} 条：空正文 {len(empty)} 条，重复单号 {dup} 条")


if __name__ == "__main__":
    main()
