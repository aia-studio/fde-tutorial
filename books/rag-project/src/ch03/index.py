"""向量化与索引：先离线跑通，再谈增量。

字符二元组哈希成定长向量，不依赖外部模型，离线可复现。

运行：python src/ch03/index.py
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict
from pathlib import Path

from ch03.chunk import Chunk, chunk_docs, DOCS

DIM = 512
HAN = re.compile(r"[\u4e00-\u9fff]")


def _terms(text: str) -> list[tuple[str, float]]:
    """单字给低权重，二元组给高权重，标题一起进向量。"""
    han = "".join(HAN.findall(text))
    terms: list[tuple[str, float]] = [(c, 0.5) for c in han]
    terms += [(han[i:i + 2], 1.0) for i in range(len(han) - 1)]
    return terms


def embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for term, weight in _terms(text):
        digest = hashlib.md5(term.encode("utf-8")).hexdigest()
        vec[int(digest[:8], 16) % DIM] += weight
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class Index:
    """先用暴力检索，量级上来再换向量库。"""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.vectors: list[list[float]] = []

    def add(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)
        self.vectors.append(embed(f"{chunk.title} {chunk.section} {chunk.text}"))

    def search(self, query: str, k: int = 5) -> list[tuple[float, Chunk]]:
        q = embed(query)
        scored = [(cosine(q, v), c) for v, c in zip(self.vectors, self.chunks)]
        scored.sort(key=lambda x: (-x[0], x[1].chunk_id))
        return scored[:k]

    def save(self, path: Path) -> None:
        payload = {
            "dim": DIM,
            "items": [{"chunk": asdict(c), "vector": v}
                      for c, v in zip(self.chunks, self.vectors)],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Index":
        data = json.loads(path.read_text(encoding="utf-8"))
        idx = cls()
        for item in data["items"]:
            idx.chunks.append(Chunk(**item["chunk"]))
            idx.vectors.append(item["vector"])
        return idx


def build(docs: list[dict[str, str]] | None = None) -> Index:
    idx = Index()
    for chunk in chunk_docs(docs or DOCS):
        idx.add(chunk)
    return idx


def main() -> None:
    idx = build()
    path = Path(__file__).with_name("index.json")
    idx.save(path)
    print(f"建索引 {len(idx.chunks)} 块，维度 {DIM}，落盘 {path.name}")

    reloaded = Index.load(path)
    print(f"重新加载 {len(reloaded.chunks)} 块，与内存一致："
          f"{[c.chunk_id for c in reloaded.chunks] == [c.chunk_id for c in idx.chunks]}")

    for query in ("主轴有异响", "换刀停顿", "冷却液报警"):
        print(f"\n查询：{query}")
        for score, chunk in reloaded.search(query, 3):
            print(f"  {score:.3f}  {chunk.chunk_id}  {chunk.section}  {chunk.text[:24]}")


if __name__ == "__main__":
    main()
