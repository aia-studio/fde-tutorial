"""故障演练：检索失败、模型超时、从库断连，各演一次。

运行：python src/ch05/drill.py
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Callable


class RetrievalTimeout(Exception):
    pass


class ModelUnavailable(Exception):
    pass


class ReplicaDown(Exception):
    pass


@dataclass
class Outcome:
    mode: str          # normal / degraded / abstain / handoff
    text: str
    note: str


def call_retrieval(ticket: str) -> str:
    if ticket == "timeout":
        raise RetrievalTimeout("检索超过 800 毫秒")
    return "HY-1002#2 轴承缺油，补脂后异响消失"


def call_model(prompt: str, attempt: int = 1) -> str:
    if prompt == "model-5xx":
        raise ModelUnavailable(f"上游返回 503（第 {attempt} 次）")
    return "主轴异响多为轴承缺油。"


def call_replica() -> str:
    raise ReplicaDown("只读从库连接被重置")


def handle(ticket: str) -> Outcome:
    try:
        context = call_retrieval(ticket)
    except RetrievalTimeout:
        context = ""
    except ReplicaDown:
        return Outcome("abstain", "现在查不到工单记录，请过一会儿再试或转人工。", "从库不可用，不返回缓存旧答案")

    if not context:
        return Outcome("degraded", "只找到少量相关记录，先给出关键词结果供参看。", "检索降级为关键词兜底")

    prompt = "model-5xx" if ticket == "model" else "ok"
    calls = 0
    for attempt in (1, 2):
        calls += 1
        try:
            return Outcome("normal", call_model(prompt, attempt),
                           "首次成功" if attempt == 1 else "重试成功")
        except ModelUnavailable:
            continue
    return Outcome("handoff", "答案生成暂不可用，已转人工处理。", f"模型调用 {calls} 次均失败")


def route(kind: str) -> Outcome:
    if kind == "replica":
        try:
            call_replica()
        except ReplicaDown as exc:
            return Outcome("abstain", "现在查不到工单记录，请过一会儿再试或转人工。", str(exc))
    return handle(kind)


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


CASES: list[tuple[str, str, str]] = [
    ("正常", "normal", "normal"),
    ("检索超时", "timeout", "degraded"),
    ("模型 5xx", "model", "handoff"),
    ("从库断连", "replica", "abstain"),
]


def main() -> None:
    print(f"{pad('场景', 12)}{pad('期望', 10)}{pad('实际', 10)}结论  说明")
    failed = 0
    for name, kind, expected in CASES:
        out = route(kind)
        ok = out.mode == expected
        failed += 0 if ok else 1
        print(f"{pad(name, 12)}{pad(expected, 10)}{pad(out.mode, 10)}"
              f"{'通过' if ok else '失败'}  {out.note}")
    print()
    print(f"演练 {len(CASES)} 个场景，失败 {failed} 个")
    for name, kind, _ in CASES:
        print(f"  {name} 对客回复：{route(kind).text}")


if __name__ == "__main__":
    main()
