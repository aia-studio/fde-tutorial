"""Ch01 最小问答：关键词包含 + 返回原文。"""


def answer(question: str, rows: list[dict]) -> dict:
    """按问题前两个字做关键词匹配，返回原文与工单号。"""
    hits = [r for r in rows if question[:2] in r["description"]]
    if not hits:
        return {"answer": "", "source": ""}
    top = hits[0]
    return {"answer": top["description"], "source": top["ticket_no"]}
