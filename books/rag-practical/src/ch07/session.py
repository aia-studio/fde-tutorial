"""Ch07 会话层：只存必要轮次，每轮先改写再检索。

状态里放两样东西：当前产品、上一轮工单号，再加最近几轮的问句。
原文与答案不进状态，它们会让上下文越长越贵，对下一轮判断也没有帮助。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ch07.rewrite import rewrite

MAX_TURNS = 3


@dataclass
class Turn:
    question: str
    rewritten: str
    notes: list[str]
    ticket_no: str = ""
    product: str = ""
    answer: str = ""
    refused: bool = False


@dataclass
class Conversation:
    """一次会话。ask_fn 与 retrieve 由上层注入，会话层不认具体模型。"""

    ask_fn: Callable[..., dict]
    retrieve: Callable[..., list[dict]]
    k: int = 5
    max_turns: int = MAX_TURNS
    turns: list[Turn] = field(default_factory=list)
    product: str = ""
    last_ticket: str = ""

    def state(self) -> dict:
        return {"product": self.product, "ticket": self.last_ticket}

    def ask(self, question: str) -> Turn:
        rewritten, notes = rewrite(question, self.state())
        result = self.ask_fn(rewritten, self.k)
        hits = self.retrieve(rewritten)
        top = hits[0] if hits else {}
        turn = Turn(
            question=question,
            rewritten=rewritten,
            notes=notes,
            ticket_no=top.get("ticket_no", ""),
            product=top.get("product", ""),
            answer=result.get("answer", ""),
            refused=bool(result.get("refused")),
        )
        if turn.product:
            self.product = turn.product
        if turn.ticket_no:
            self.last_ticket = turn.ticket_no
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)
        return turn

    def kept_chars(self) -> int:
        """状态实际占用的字符数：只算留下的问句与工单号。"""
        return sum(len(t.question) + len(t.ticket_no) for t in self.turns)

    def full_chars(self) -> int:
        """对照口径：把每轮问句与答案全文都带着会占多少字符。"""
        return sum(len(t.question) + len(t.answer) for t in self.turns)


def demo_turns() -> list[str]:
    """一条真实会出现的三轮追问：第一轮说现象，后两轮省主语。"""
    return ["显卡花屏出现彩色条纹", "保修期多久", "显卡风扇保修吗"]
