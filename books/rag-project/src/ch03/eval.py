"""召回初测：先测 20 条，再谈调参。

运行：python src/ch03/eval.py
"""

from __future__ import annotations

import unicodedata

from ch03 import index as index_mod

TOP_K = 5
TARGET_RECALL = 0.80

CASES: list[tuple[str, str]] = [
    ("指示灯不亮", "HY-1001#1"),
    ("急停没有复位", "HY-1001#3"),
    ("主轴一直响", "HY-1002#1"),
    ("轴承要补润滑脂", "HY-1002#2"),
    ("报错 E-204 是什么意思", "HY-1003#1"),
    ("散热不好怎么处理", "HY-1003#2"),
    ("换刀的时候停顿", "HY-1004#1"),
    ("刀库气压不足", "HY-1004#2"),
    ("加工久了尺寸变大", "HY-1005#1"),
    ("丝杠热伸长怎么补偿", "HY-1005#2"),
    ("远程诊断连不上", "HY-1006#1"),
    ("用跳板机转发端口", "HY-1006#2"),
    ("冷却液一直报警", "HY-1007#2"),
    ("浮子开关被铁屑卡住", "HY-1007#1"),
    ("升级包校验失败", "HY-1008#1"),
    ("重新下载安装包", "HY-1008#2"),
    ("设备开不了机", "HY-1001#1"),
    ("机器声音不对", "HY-1002#1"),
    ("面板报警后自动停了", "HY-1003#1"),
    ("换了刀以后动作慢", "HY-1004#1"),
]


def rank_of(results: list[tuple[float, object]], gold: str) -> int:
    for pos, (_, chunk) in enumerate(results, 1):
        if chunk.chunk_id == gold:
            return pos
    return 0


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def main() -> None:
    idx = index_mod.build()
    hits = 0
    hit1 = 0
    mrr = 0.0
    print(f"{'#':<4}{pad('查询', 22)}{pad('首位命中', 12)}{'排名':>4}")
    for i, (query, gold) in enumerate(CASES, 1):
        results = idx.search(query, TOP_K)
        rank = rank_of(results, gold)
        if rank:
            hits += 1
            mrr += 1 / rank
            hit1 += 1 if rank == 1 else 0
        top = results[0][1].chunk_id
        print(f"{i:<4}{pad(query, 22)}{pad(top, 12)}{rank if rank else '-':>4}")

    n = len(CASES)
    print()
    print(f"命中 {hits}/{n} 条，召回@{TOP_K} = {hits / n:.2f}，"
          f"首位命中 {hit1} 条，MRR = {mrr / n:.2f}")
    verdict = "达到约定值" if hits / n >= TARGET_RECALL else "未达到约定值，需要调参"
    print(f"目标 {TARGET_RECALL:.2f}：{verdict}")

    misses = [q for q, g in CASES if not rank_of(idx.search(q, TOP_K), g)]
    if misses:
        print("未命中查询：" + "；".join(misses))


if __name__ == "__main__":
    main()
