"""Ch03 向量检索：先按元数据过滤，再算余弦相似度取 Top-K。"""

from __future__ import annotations

import sqlite3
from array import array

from ch02.embed import embed_one
from common.paths import INDEX_DB

DEFAULT_K = 5


def _load(db_path: str, where: str = "", params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(db_path)
    sql = ("SELECT chunk_id, ticket_no, product, category, created_at, seq, text, vector "
           f"FROM chunks {where}")
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    out = []
    for r in rows:
        vec = array("f")
        vec.frombytes(r[7])
        out.append({"chunk_id": r[0], "ticket_no": r[1], "product": r[2], "category": r[3],
                    "created_at": r[4], "seq": r[5], "text": r[6], "vector": list(vec)})
    return out


def search(question: str, k: int = DEFAULT_K, product: str | None = None,
           category: str | None = None, db_path: str = str(INDEX_DB)) -> list[dict]:
    """过滤在 SQL 里做，排序在内存里做；返回按分数降序的 k 条。"""
    conds, params = [], []
    if product:
        conds.append("product = ?")
        params.append(product)
    if category:
        conds.append("category = ?")
        params.append(category)
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    rows = _load(db_path, where, tuple(params))
    if not rows:
        return []
    q = embed_one(question)
    for r in rows:
        r["score"] = sum(x * y for x, y in zip(q, r["vector"]))
        r.pop("vector")
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:k]


def main() -> None:
    for question in ("显示器黑屏电源灯亮", "换货要原包装吗"):
        print(f"q={question}")
        for i, hit in enumerate(search(question, 3), 1):
            print(f"  {i}. {hit['score']:.3f} {hit['ticket_no']} {hit['text'][:28]}")
    print("q=打印机报 E-204，先过滤 product=P200 打印机：")
    for hit in search("打印机报 E-204", 2, product="P200 打印机"):
        print(f"  {hit['score']:.3f} {hit['ticket_no']} {hit['text'][:28]}")


if __name__ == "__main__":
    main()
