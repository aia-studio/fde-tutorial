"""Ch07 指代消解：把「它」「那保修呢」补成能检索的完整问句。

只补槽位，不搬旧话题：状态里的产品名、型号可以进来，
上一轮的错误码与故障词不能跟着进来，否则新问题会被旧问题压住。
"""

from __future__ import annotations

import re

PRONOUNS = ("它", "这台", "那台", "这个", "那个", "该设备", "这玩意")
FILLERS = ("那么", "那", "还有", "另外", "再问一下", "顺便问")


def split_product(product: str) -> tuple[str, str]:
    """'A100 显卡' → ('A100', '显卡')；没有型号时返回 ('', 原名)。"""
    parts = product.split(" ", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("", product)


def _strip_filler(q: str) -> tuple[str, bool]:
    for f in FILLERS:
        if q.startswith(f):
            return q[len(f):].lstrip("，, "), True
    return q, False


def rewrite(question: str, state: dict) -> tuple[str, list[str]]:
    """返回（改写后的查询, 改了什么）。state 为空时原样返回。"""
    q, notes = question.strip(), []
    product = str(state.get("product") or "")
    if not product:
        return q, notes

    model, kind = split_product(product)
    q, dropped = _strip_filler(q)
    if dropped:
        notes.append("去语气词")

    for p in PRONOUNS:
        if p in q:
            q = q.replace(p, product)
            notes.append(f"还原「{p}」")
            break

    if model and model.lower() in q.lower():
        return q, notes

    if kind and kind in q:
        q = q.replace(kind, product, 1)
        notes.append("补型号")
    else:
        q = f"{product} {q}"
        notes.append("补产品")
    return re.sub(r"\s+", " ", q).strip(), notes


def main() -> None:
    state = {"product": "A100 显卡", "ticket": "T-1007"}
    cases = ["它保修多久", "保修期多久", "显卡风扇保修吗", "那换屏要钱吗",
             "A100 的发票丢了怎么办", "你们支持比特币付款吗"]
    print(f"{'用户问':<18}{'带状态':<26}{'动作':<12}空状态")
    for q in cases:
        with_state, notes = rewrite(q, state)
        raw, _ = rewrite(q, {})
        print(f"{q:<18}{with_state:<26}{'+'.join(notes):<12}{raw}")


if __name__ == "__main__":
    main()
