"""Ch02 嵌入：把文本压成定长向量，默认用不联网、结果确定的哈希嵌入。"""

from __future__ import annotations

import hashlib
import math

from common.text import tokens

DEFAULT_DIM = 256


def _bucket(token: str, dim: int) -> tuple[int, int]:
    h = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")
    return h % dim, (1 if (h >> 63) & 1 else -1)


def embed_one(text: str, dim: int = DEFAULT_DIM) -> list[float]:
    vec = [0.0] * dim
    for tok in tokens(text):
        idx, sign = _bucket(tok, dim)
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def embed_texts(texts: list[str], dim: int = DEFAULT_DIM) -> list[list[float]]:
    return [embed_one(t, dim) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def main() -> None:
    pairs = [
        ("显示器黑屏电源灯亮", "显示器黑屏但电源灯亮着"),
        ("显示器黑屏电源灯亮", "打印机卡纸取不出来"),
        ("E-204 定影单元温度异常", "打印机报 E-204"),
    ]
    print(f"向量维度 {DEFAULT_DIM}，分词示例 {tokens(pairs[0][0])[:6]}")
    for a, b in pairs:
        print(f"cos({a} | {b}) = {cosine(embed_one(a), embed_one(b)):.3f}")
    print(f"单条向量长度 {len(embed_one(pairs[0][0]))}，模长 "
          f"{math.sqrt(sum(v * v for v in embed_one(pairs[0][0]))):.3f}")


if __name__ == "__main__":
    main()
