"""Ch02 切分：按句子边界切块，带重叠与元数据。"""

from __future__ import annotations

import csv

from common.text import split_sentences

DEFAULT_SIZE = 90
DEFAULT_OVERLAP = 20
MIN_TAIL = 25


def chunk_text(text: str, size: int = DEFAULT_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """把一段文本切成不超过 size 字的块，块之间按整句重叠。"""
    sentences = split_sentences(text)
    chunks: list[str] = []
    cur: list[str] = []
    for s in sentences:
        if cur and sum(len(x) for x in cur) + len(s) > size:
            chunks.append("".join(cur))
            tail: list[str] = []
            acc = 0
            for prev in reversed(cur):
                tail.insert(0, prev)
                acc += len(prev)
                if acc >= overlap:
                    break
            cur = tail if acc + len(s) <= size else []
        cur.append(s)
    if cur:
        chunks.append("".join(cur))
    if len(chunks) >= 2 and len(chunks[-1]) < MIN_TAIL:
        chunks[-2] += chunks[-1]
        chunks.pop()
    return [c for c in chunks if c]


def build_chunks(rows: list[dict], size: int = DEFAULT_SIZE,
                 overlap: int = DEFAULT_OVERLAP) -> list[dict]:
    """一行工单变成一个文档：现象 + 处理结果，再切成块并挂元数据。"""
    out: list[dict] = []
    for row in rows:
        text = f"{row['description']}。处理：{row['resolution']}"
        for seq, piece in enumerate(chunk_text(text, size, overlap)):
            out.append({
                "chunk_id": f"{row['ticket_no']}-{seq:02d}",
                "ticket_no": row["ticket_no"],
                "product": row["product"],
                "category": row["category"],
                "created_at": row["created_at"],
                "seq": seq,
                "text": piece,
            })
    return out


def load_rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    from common.paths import TICKETS_CSV

    rows = load_rows(str(TICKETS_CSV))
    chunks = build_chunks(rows)
    lens = [len(c["text"]) for c in chunks]
    print(f"工单 {len(rows)} 条 → 块 {len(chunks)} 个")
    print(f"块长 min={min(lens)} max={max(lens)} 平均={sum(lens) // len(lens)}")
    for c in chunks[:2]:
        print(f"[{c['chunk_id']}] {c['text']}")


if __name__ == "__main__":
    main()
