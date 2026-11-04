"""Ch07 多轮评测：按轮次算命中，末轮通过不等于会话通过。

每个案例是一条脚本化的会话，每轮都标了 gold 工单。
同一批案例跑两遍：一遍带会话状态，一遍每句各问各的。
"""

from __future__ import annotations

from ch07.pipeline import ask, conversation, retriever

K = 5

CASES: list[dict] = [
    {
        "id": "M1", "product": "显卡",
        "rounds": [
            ("显卡花屏出现彩色条纹", "T-1007"),
            ("保修期多久", "T-1026"),
            ("显卡风扇保修吗", "T-1026"),
        ],
    },
    {
        "id": "M2", "product": "显示器",
        "rounds": [
            ("显示器黑屏但电源灯亮着", "T-1004"),
            ("保修期多久", "T-1024"),
            ("换屏要钱吗", "T-1005"),
        ],
    },
    {
        "id": "M3", "product": "打印机",
        "rounds": [
            ("打印机卡纸，取出后仍提示缺纸", "T-1003"),
            ("保修期多久", "T-1027"),
            ("定影单元算不算", "T-1027"),
        ],
    },
]


def run(cases: list[dict], use_session: bool) -> list[dict]:
    get = retriever(K)
    rows: list[dict] = []
    for case in cases:
        conv = conversation(K) if use_session else None
        for i, (question, gold) in enumerate(case["rounds"], 1):
            if conv is None:
                hits = get(question)
                result = ask(question, K)
            else:
                turn = conv.ask(question)
                hits = get(turn.rewritten)
                result = {"refused": turn.refused}
            rank = next((j for j, h in enumerate(hits, 1) if h["ticket_no"] == gold), 0)
            refused = bool(result["refused"])
            rows.append({"case": case["id"], "round": i, "question": question,
                         "gold": gold, "rank": rank, "refused": refused,
                         "right": rank == 1 and not refused,
                         "recall": 0 < rank <= K})
    return rows


def summarize(rows: list[dict]) -> dict:
    cases = sorted({r["case"] for r in rows})
    return {
        "right": sum(1 for r in rows if r["right"]),
        "total": len(rows),
        "recall": sum(1 for r in rows if r["recall"]),
        "refused": sum(1 for r in rows if r["refused"]),
        "cases": len(cases),
        "passed": sum(1 for c in cases if all(r["right"] for r in rows if r["case"] == c)),
    }


def main() -> None:
    for mode, use in (("无状态", False), ("有状态", True)):
        s = summarize(run(CASES, use))
        print(f"{mode}：答对 {s['right']}/{s['total']}　前五命中 {s['recall']}/{s['total']}　"
              f"误拒 {s['refused']}/{s['total']}　会话通过 {s['passed']}/{s['cases']}")
    print()
    print(f"{'案例':<6}{'轮':<4}{'用户问':<14}{'名次':<6}{'答对':<6}拒答")
    for r in run(CASES, True):
        print(f"{r['case']:<6}{r['round']:<4}{r['question']:<14}{r['rank'] or '-':<6}"
              f"{'是' if r['right'] else '否':<6}{'是' if r['refused'] else '否'}")


if __name__ == "__main__":
    main()
