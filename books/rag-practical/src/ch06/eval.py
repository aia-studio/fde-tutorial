"""Ch06 评测：20 题跑一遍，分开算召回、引用、拒答三个指标。"""

from __future__ import annotations

import json
import sqlite3
import sys

from ch05.fuse import hybrid_search, vector_search
from ch05.rerank import ask, build_retriever, rerank
from common.paths import EVAL_SET, INDEX_DB
from common.text import overlap_chars

K = 5


def load_set(path: str = str(EVAL_SET)) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def ticket_texts(ticket_no: str, db_path: str = str(INDEX_DB)) -> list[str]:
    """按工单号取回它的全部块，用来校验引文是不是原文。"""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT text FROM chunks WHERE ticket_no=? ORDER BY seq",
                        (ticket_no,)).fetchall()
    conn.close()
    return [r[0] for r in rows]


def run(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        hits = build_retriever(K)(item["question"])
        result = ask(item["question"], k=K)
        rank = next((i + 1 for i, h in enumerate(hits)
                     if h["ticket_no"] == item["gold_ticket"]), 0) if item["gold_ticket"] else 0
        quote = result["citations"][0]["quote"] if result["citations"] else ""
        sources = ticket_texts(item["gold_ticket"]) if item["gold_ticket"] else []
        rec = {
            "id": item["id"], "type": item["type"], "question": item["question"],
            "expect": item["expect"], "refused": result["refused"], "reason": result["reason"],
            "rank": rank, "quote": quote,
            "verbatim": bool(quote) and any(quote in s for s in sources),
            "aligned": bool(quote) and overlap_chars(quote, item["gold_span"]) >= 6,
        }
        rec["cite_ok"] = rec["verbatim"] and rec["aligned"]
        records.append(rec)
    return records


def summarize(records: list[dict]) -> dict:
    answerable = [r for r in records if r["expect"] == "answer"]
    boundary = [r for r in records if r["expect"] == "refuse"]
    answered = [r for r in records if not r["refused"]]
    recall = sum(1 for r in answerable if 0 < r["rank"] <= K)
    cite = sum(1 for r in answered if r["cite_ok"])
    refuse_ok = sum(1 for r in boundary if r["refused"])
    false_refuse = sum(1 for r in answerable if r["refused"])
    return {
        "recall": (recall, len(answerable)),
        "citation": (cite, len(answered)),
        "refusal": (refuse_ok, len(boundary)),
        "false_refuse": (false_refuse, len(answerable)),
    }


def compare(items: list[dict]) -> list[tuple[str, int, int]]:
    """同一条链路拆成三档：纯向量、混合、混合加重排。"""
    usable = [i for i in items if i["expect"] == "answer"]
    plans = [
        ("纯向量", lambda q: vector_search(q, K)),
        ("混合", lambda q: hybrid_search(q, K)),
        ("混合+重排", lambda q: rerank(q, hybrid_search(q, 20), K)),
    ]
    rows = []
    for name, fn in plans:
        at1 = at5 = 0
        for item in usable:
            hits = fn(item["question"])
            rank = next((i for i, h in enumerate(hits, 1)
                         if h["ticket_no"] == item["gold_ticket"]), 0)
            at1 += 1 if rank == 1 else 0
            at5 += 1 if 0 < rank <= K else 0
        rows.append((name, at1, at5))
    return rows


def main() -> None:
    items = load_set()
    if "--compare" in sys.argv:
        print(f"{'链路':<10}{'第一名命中':<10}{'前五名命中'}")
        for name, at1, at5 in compare(items):
            print(f"{name:<10}{at1}/{len([i for i in items if i['expect'] == 'answer']):<10}"
                  f"{at5}/{len([i for i in items if i['expect'] == 'answer'])}")
        return
    records = run(items)
    print(f"{'题号':<5}{'题型':<7}{'名次':<5}{'拒答':<5}{'引用':<5}问题")
    for r in records:
        flag = "OK" if r["refused"] else ("OK" if r["cite_ok"] else "差")
        print(f"{r['id']:<5}{r['type']:<7}{r['rank'] or '-':<5}"
              f"{'是' if r['refused'] else '否':<5}{flag:<5}{r['question']}")
    s = summarize(records)
    print()
    for name, (ok, total) in (("召回@5", s["recall"]), ("引用准确", s["citation"]),
                              ("拒答正确", s["refusal"]), ("误拒", s["false_refuse"])):
        print(f"{name} = {ok}/{total}")
    for t in ("事实型", "型号与代码", "边界型"):
        sub = [r for r in records if r["type"] == t]
        ok = sum(1 for r in sub if (r["refused"] if r["expect"] == "refuse" else r["cite_ok"]))
        print(f"{t}：{ok}/{len(sub)}")


if __name__ == "__main__":
    main()
