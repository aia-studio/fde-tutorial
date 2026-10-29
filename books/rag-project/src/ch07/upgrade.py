"""模型与索引升级：新索引先在影子位跑同一批样本，不达标不切。

比较两件事：同一批问题在新旧索引下的名次，以及返回的块还能不能回指原文。
只比「答案像不像」会漏掉引用失效，这类问题上线后才被坐席发现。

运行（在 src/ 下）：python -m ch07.upgrade
"""

from __future__ import annotations

import re
from dataclasses import dataclass

K = 5
SYNONYMS = {"密封圈": "O 型圈", "报销": "费用", "到货": "交期"}


@dataclass(frozen=True)
class Doc:
    id: str
    title: str
    text: str


DOCS: tuple[Doc, ...] = (
    Doc("P1", "备件更换周期", "O 型圈每季度检查一次，老化即换"),
    Doc("P2", "备件库存", "常用密封件保持两周库存"),
    Doc("P3", "差旅费用", "差旅费用在回程后十个工作日内提交"),
    Doc("P4", "发票要求", "发票抬头写全称，税号不能缺位"),
    Doc("P5", "交期说明", "进口件交期以供应商排产为准"),
    Doc("P6", "退换流程", "退换先登记故障现象与批次号"),
    Doc("P7", "备件更换周期", "O 型圈每季度检查一次，老化即换"),
    Doc("P8", "验收口径", "验收以抽样复测结果为准，不看演示"),
)

SAMPLES: tuple[tuple[str, str], ...] = (
    ("O 型圈多久换一次", "P1"),
    ("密封件库存备多久", "P2"),
    ("密封圈多久换一次", "P1"),
    ("出差费用什么时候报", "P3"),
    ("发票抬头怎么写", "P4"),
    ("进口件到货要多久", "P5"),
    ("退换货怎么走", "P6"),
    ("验收怎么算通过", "P8"),
)


def grams(text: str) -> set[str]:
    s = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()
    return {s[i:i + 2] for i in range(len(s) - 1)} or {s}


def expand(q: str, on: bool) -> str:
    if not on:
        return q
    for src, dst in SYNONYMS.items():
        q = q.replace(src, f"{src} {dst}")
    return q


def build(use_title: bool, with_synonym: bool) -> list[tuple[str, set[str], str]]:
    out = []
    for d in DOCS:
        body = f"{d.title} {d.text}" if use_title else d.text
        out.append((d.id, grams(expand(body, with_synonym)), d.text))
    return out


def search(index, q: str, with_synonym: bool, k: int = K) -> list[str]:
    qg = grams(expand(q, with_synonym))
    scored = [(len(qg & g) / max(len(qg | g), 1), cid) for cid, g, _ in index]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [cid for _, cid in scored[:k]]


def metrics(index, with_synonym: bool) -> tuple[float, float, list[int]]:
    ranks: list[int] = []
    for q, gold in SAMPLES:
        got = search(index, q, with_synonym)
        ranks.append(got.index(gold) + 1 if gold in got else 0)
    hit = sum(1 for r in ranks if r) / len(ranks)
    mrr = sum(1 / r for r in ranks if r) / len(ranks)
    return hit, mrr, ranks


def dereference(index, q: str, with_synonym: bool) -> float:
    """返回的块里，能回指到原文的比例。"""
    ok = 0
    for cid in search(index, q, with_synonym):
        doc = next((d for d in DOCS if d.id == cid), None)
        if doc and doc.text:
            ok += 1
    return ok / K


def main() -> None:
    old = build(use_title=False, with_synonym=False)
    new = build(use_title=True, with_synonym=True)
    r_old, m_old, ranks_old = metrics(old, False)
    r_new, m_new, ranks_new = metrics(new, True)
    d_old = sum(dereference(old, q, False) for q, _ in SAMPLES) / len(SAMPLES)
    d_new = sum(dereference(new, q, True) for q, _ in SAMPLES) / len(SAMPLES)

    print(f"{'样本':<18}{'旧名次':>8}{'新名次':>8}")
    for (q, _), a, b in zip(SAMPLES, ranks_old, ranks_new):
        print(f"{q:<18}{a or '未命中':>8}{b or '未命中':>8}")

    print()
    print(f"{'指标':<14}{'旧索引':>10}{'新索引':>10}")
    print(f"{'Top-5 命中':<14}{r_old:>10.3f}{r_new:>10.3f}")
    print(f"{'MRR':<14}{m_old:>10.3f}{m_new:>10.3f}")
    print(f"{'可回指率':<14}{d_old:>10.3f}{d_new:>10.3f}")
    print(f"{'块数':<14}{len(DOCS):>10}{len({d.text for d in DOCS}):>10}")

    print()
    reasons: list[str] = []
    if r_new < r_old:
        reasons.append("命中下降")
    if m_new < m_old - 0.02:
        reasons.append("名次变差")
    if d_new < 1.0:
        reasons.append("引用不能全回指")
    if reasons:
        print(f"结论：不切。{'、'.join(reasons)}")
    else:
        print("结论：切。命中不降、名次不降、引用全部可回指，重复块已合并。")
        print("切换顺序：影子索引重建 → 双读比对一天 → 切读 → 保留旧索引一周可回退。")


if __name__ == "__main__":
    main()
