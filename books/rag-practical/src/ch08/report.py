"""Ch08 运营月报：把反馈、badcase、回归三份数据合成一页能对着上月比的东西。

月报只回答三个问题：这个月错在哪、修了什么、下个月先动哪一件。
写不出这三句的报告，指标再多也没人看。
"""

from __future__ import annotations

import json
from pathlib import Path

from ch08.badcase import BADCASES, FEEDBACK, load as load_feedback
from ch08.release import CASES, compare
from common.paths import DATA_DIR

OPS_DIR = DATA_DIR / "ops"
REPORT = OPS_DIR / "monthly-report.md"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def ratio(ok: int, total: int) -> str:
    return f"{ok}/{total}"


def build(badcases: list[dict], feedback: list[dict], rows: list[dict]) -> str:
    a, b = rows
    by_type: dict[str, int] = {}
    for c in badcases:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    top = max(by_type.items(), key=lambda kv: kv[1]) if by_type else ("无", 0)
    bad = [r for r in feedback if r.get("feedback") == "差"]

    lines = [
        "# 客服问答月报",
        "",
        f"- 反馈条数：{len(feedback)}，其中差评 {len(bad)} 条",
        f"- 去重合并：{len(bad) - len(badcases)} 条，同一句话被两个客户各反馈一次",
        f"- 登记 badcase：{len(badcases)} 条，待复核 {sum(1 for c in badcases if c['status'] == '待复核')} 条",
        f"- 差评率：{ratio(len(bad), len(feedback))}，分母是有反馈的会话，不是全部提问",
        "",
        "## 质量",
        "",
        "| 版本 | 答对 | 前五命中 | 误拒 | 会话通过 |",
        "| --- | --- | --- | --- | --- |",
        f"| {a['name']} | {ratio(a['right'], a['total'])} | {ratio(a['recall'], a['total'])} "
        f"| {ratio(a['refused'], a['total'])} | {ratio(a['passed'], a['cases'])} |",
        f"| {b['name']} | {ratio(b['right'], b['total'])} | {ratio(b['recall'], b['total'])} "
        f"| {ratio(b['refused'], b['total'])} | {ratio(b['passed'], b['cases'])} |",
        "",
        "## 失效分布",
        "",
        "| 类型 | 条数 | 处理动作 |",
        "| --- | --- | --- |",
    ]
    for kind, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        action = next((c["action"] for c in badcases if c["type"] == kind), "")
        lines.append(f"| {kind} | {n} | {action} |")

    lines += [
        "",
        "## 结论",
        "",
        f"- 本月最主要失效是「{top[0]}」，{top[1]} 条，占 badcase 的 {ratio(top[1], len(badcases))}。",
        f"- 会话版比单轮版多答对 {b['right'] - a['right']} 轮，会话通过多 {b['passed'] - a['passed']} 条。",
        f"- 全量题库只有 {len(CASES)} 条会话，涨几条只能看方向，下月扩到十组以上。",
        "",
        "## 下月动作",
        "",
        f"1. 先修「{top[0]}」：{top[1]} 条里有共同点的话，一条改动能带走一批。",
        "2. 把本月 badcase 里已复核的并入回归集，跑通再关单。",
        "3. 语料变更按增量重建，重建后复核上月的 badcase 是否仍然复现。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    feedback = load_feedback(FEEDBACK)
    badcases = load_jsonl(BADCASES)
    rows = compare(CASES, [("A 单轮", False), ("B 会话", True)])
    text = build(badcases, feedback, rows)
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    print(f"已写入 {REPORT.relative_to(DATA_DIR.parent)}")


if __name__ == "__main__":
    main()
