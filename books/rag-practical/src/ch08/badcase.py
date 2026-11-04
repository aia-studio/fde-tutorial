"""Ch08 badcase 回流：把散落的差评变成可归因、可复现的条目。

一条差评要变成 badcase，得先过三关：去重、判定失效类型、写清期望结果。
判定用现网链路复跑一遍，不靠客服的转述。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ch07.pipeline import ask, retriever
from common.paths import DATA_DIR

OPS_DIR = DATA_DIR / "ops"
FEEDBACK = OPS_DIR / "feedback.jsonl"
BADCASES = OPS_DIR / "badcase.jsonl"
K = 5

ACTIONS = {
    "误拒": "看 coverage 阈值与口语同义词，证据在前五就别拒",
    "漏召": "查语料是否缺这条，缺就补工单，不缺就查切分",
    "引错": "看第一名被谁顶掉，先查型号与错误码是否完整命中",
    "该拒未拒": "补边界题到评测集，收紧 coverage 阈值",
    "答非所问": "人工复核，多数是同一产品多条口径打架",
    "正确拒答": "不用处理，登记为已覆盖",
}


def load(path: Path = FEEDBACK) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def normalize(question: str) -> str:
    return re.sub(r"[\s，。？！,.?!]+", "", question)


def dedupe(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """同一句话进两次很常见：按归一化后的问句留最早的一条。"""
    kept: dict[str, dict] = {}
    dup: list[dict] = []
    for row in rows:
        key = normalize(row["question"])
        if key in kept:
            dup.append(row)
            continue
        kept[key] = row
    return list(kept.values()), dup


def judge(row: dict) -> tuple[str, str]:
    """跑一遍现网链路，按结果判定失效类型。返回（类型, 实际落到的工单）。

    拒答要分两种：证据在前五却被拒是误拒，证据根本没召回来才是漏召。
    """
    expected = row.get("expect")
    result = ask(row["question"], K)
    hits = retriever(K)(row["question"])
    top = hits[0]["ticket_no"] if hits else ""
    if expected and result["refused"]:
        rank = next((i for i, h in enumerate(hits, 1) if h["ticket_no"] == expected), 0)
        return ("误拒" if 0 < rank <= K else "漏召"), top
    if not expected and not result["refused"]:
        return "该拒未拒", top
    if not expected:
        return "正确拒答", top
    if top != expected:
        return "引错", top
    return "答非所问", top


def collect(rows: list[dict]) -> list[dict]:
    kept, _ = dedupe(rows)
    out: list[dict] = []
    for row in kept:
        if row.get("feedback") != "差":
            continue
        kind, top = judge(row)
        out.append({
            "id": row["id"], "date": row["ts"], "session": row["session"],
            "question": row["question"], "expect": row.get("expect"),
            "actual": top, "type": kind, "note": row.get("note", ""),
            "action": ACTIONS[kind], "status": "待复核",
        })
    return out


def main() -> None:
    rows = load()
    kept, dup = dedupe(rows)
    cases = collect(rows)
    print(f"反馈 {len(rows)} 条，去重后 {len(kept)} 条，重复 {len(dup)} 条")
    print(f"差评 {len(cases)} 条，登记为 badcase")
    print()
    print(f"{'编号':<8}{'类型':<10}{'期望':<8}{'实际':<8}问句")
    for c in cases:
        print(f"{c['id']:<8}{c['type']:<10}{c['expect'] or '-':<8}{c['actual'] or '-':<8}"
              f"{c['question']}")
    print()
    by_type: dict[str, int] = {}
    for c in cases:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    for kind, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"{kind}：{n} 条 → {ACTIONS[kind]}")
    BADCASES.write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    print()
    print(f"已写入 {BADCASES.relative_to(OPS_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
