"""Ch03 小样本召回评估：10 条带标准答案的查询，看 gold 落在第几名。"""

from __future__ import annotations

from ch03.search import search

CASES: list[tuple[str, str]] = [
    ("显示器黑屏但电源灯亮着", "T-1004"),
    ("显卡花屏出现彩色条纹", "T-1007"),
    ("打印机连不上无线网络", "T-1013"),
    ("键盘进水失灵", "T-1021"),
    ("发票丢了还能保修吗", "T-1028"),
    ("怎么预约上门维修", "T-1036"),
    ("换货要不要原包装", "T-1035"),
    ("机器开不了机指示灯不亮", "T-1001"),
    ("E-311 纸张尺寸不匹配", "T-1011"),
    ("墨粉盒用哪个型号", "T-1012"),
]


def rank_of(question: str, gold: str, k: int = 5) -> int:
    for i, hit in enumerate(search(question, k), 1):
        if hit["ticket_no"] == gold:
            return i
    return 0


def main() -> None:
    ranks = []
    print(f"{'查询':<18}{'gold':<8}{'名次':<6}Top-1")
    for q, gold in CASES:
        hits = search(q, 5)
        r = rank_of(q, gold)
        ranks.append(r)
        print(f"{q:<18}{gold:<8}{r or '未命中':<6}{hits[0]['ticket_no']} {hits[0]['score']:.2f}")
    for k in (1, 3, 5):
        hit = sum(1 for r in ranks if 0 < r <= k)
        print(f"recall@{k} = {hit}/{len(ranks)}")


if __name__ == "__main__":
    main()
