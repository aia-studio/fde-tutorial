"""Ch05 字面检索：BM25，按词频与逆文档频率给候选打分。"""

from __future__ import annotations

import math
import sqlite3
from collections import Counter

from common.paths import INDEX_DB
from common.text import tokens


class BM25:
    def __init__(self, docs: list[dict], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.tf = [Counter(tokens(d["text"])) for d in docs]
        self.lens = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.lens) / max(len(self.lens), 1)
        df: Counter = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, q_tokens: list[str], i: int) -> float:
        tf, dl = self.tf[i], self.lens[i]
        s = 0.0
        for t in q_tokens:
            f = tf.get(t)
            if not f:
                continue
            idf = self.idf.get(t, 0.0)
            s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
        return s

    def search(self, query: str, k: int = 5) -> list[dict]:
        q = tokens(query)
        scored = []
        for i, doc in enumerate(self.docs):
            s = self.score(q, i)
            if s > 0:
                scored.append({**{x: doc[x] for x in ("chunk_id", "ticket_no", "product",
                                                       "category", "text")}, "score": s})
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:k]


def load_docs(db_path: str = str(INDEX_DB)) -> list[dict]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT chunk_id, ticket_no, product, category, text FROM chunks").fetchall()
    conn.close()
    return [{"chunk_id": r[0], "ticket_no": r[1], "product": r[2],
             "category": r[3], "text": r[4]} for r in rows]


def search(query: str, k: int = 5, db_path: str = str(INDEX_DB)) -> list[dict]:
    return BM25(load_docs(db_path)).search(query, k)


def main() -> None:
    for q in ("机器开不了机指示灯不亮", "E-311 纸张尺寸不匹配", "换货要不要原包装"):
        print(f"q={q}")
        for i, hit in enumerate(search(q, 3), 1):
            print(f"  {i}. {hit['score']:.2f} {hit['ticket_no']} {hit['text'][:26]}")


if __name__ == "__main__":
    main()
