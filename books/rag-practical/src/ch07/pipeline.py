"""Ch07 门面：单轮链路直接复用 Ch06 评测里跑的那条，会话层包在外面。

这样会话层与单轮评测用的是同一套检索、重排与拒答规则，
多轮的指标才有资格和 Ch06 的基线放在一张表里比。
"""

from __future__ import annotations

from ch06 import eval as ch06_eval
from ch07.session import Conversation, demo_turns


def ask(question: str, k: int = 5) -> dict:
    return ch06_eval.ask(question, k=k)


def retriever(k: int = 5):
    return ch06_eval.build_retriever(k)


def conversation(k: int = 5) -> Conversation:
    return Conversation(ask_fn=ask, retrieve=retriever(k), k=k)


def main() -> None:
    conv = conversation()
    print(f"{'轮次':<8}{'用户问':<12}{'改写后':<22}{'动作':<8}{'工单':<8}状态/全量字符")
    for i, q in enumerate(demo_turns(), 1):
        turn = conv.ask(q)
        flag = "拒答" if turn.refused else turn.ticket_no
        note = "+".join(turn.notes) or "不改写"
        print(f"第 {i} 轮  {turn.question:<12}{turn.rewritten:<22}{note:<8}{flag:<8}"
              f"{conv.kept_chars()}/{conv.full_chars()}")
    print()
    print(f"状态字段 product={conv.product} last_ticket={conv.last_ticket}")
    print("同三句各问各的：")
    for q in demo_turns():
        r = ask(q, 5)
        hits = retriever(5)(q)
        tag = "拒答" if r["refused"] else hits[0]["ticket_no"] if hits else "-"
        print(f"  {q:<12}→ {tag}")


if __name__ == "__main__":
    main()
