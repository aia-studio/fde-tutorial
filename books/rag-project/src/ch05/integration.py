"""与业务系统联调：先对齐字段与时序，再谈联调通过。

运行：python src/ch05/integration.py
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

REQUEST_SPEC = {"session_id": str, "question": str, "channel": str}
RESPONSE_SPEC = {"session_id": str, "answer": str, "citations": list, "trace_id": str}

CALLS: list[str] = []


def validate(payload: dict, spec: dict[str, type]) -> list[str]:
    errors: list[str] = []
    for name, kind in spec.items():
        if name not in payload:
            errors.append(f"缺字段 {name}")
            continue
        if not isinstance(payload[name], kind):
            errors.append(f"{name} 类型应为 {kind.__name__}")
    extra = sorted(set(payload) - set(spec))
    if extra:
        errors.append(f"多余字段 {'、'.join(extra)}")
    return errors


def answer(payload: dict) -> dict:
    """桩服务：只验证协议，不验证答案质量。"""
    key = f"{payload['session_id']}:{payload['question']}"
    if key in CALLS:
        cached = True
    else:
        CALLS.append(key)
        cached = False
    return {
        "session_id": payload["session_id"],
        "answer": "主轴异响多为轴承缺油，补脂后可消除。",
        "citations": [{"ticket_no": "HY-1002", "section": "处理"}],
        "trace_id": f"trace-{len(CALLS):03d}",
        "cached": cached,
    }


@dataclass
class Trace:
    steps: list[tuple[int, str, str]] = field(default_factory=list)

    def add(self, direction: str, text: str) -> None:
        self.steps.append((len(self.steps) + 1, direction, text))


def sequence() -> Trace:
    trace = Trace()
    trace.add("客服系统 → 问答服务", "session.open 带坐席工号与租户标识")
    trace.add("问答服务 → 客服系统", "session.opened 返回会话号，后续请求复用它")
    trace.add("客服系统 → 问答服务", "question 带问题原文与工单号")
    trace.add("问答服务 → 检索", "取候选并记录 trace_id")
    trace.add("问答服务 → 模型", "只带候选片段，不带全库")
    trace.add("问答服务 → 客服系统", "answer + citations + trace_id")
    return trace


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def main() -> None:
    good = {"session_id": "s-001", "question": "主轴异响怎么处理", "channel": "web"}
    missing = {"session_id": "s-002", "question": "换刀停顿"}
    wrong = {"session_id": "s-003", "question": 42, "channel": "web"}

    print("请求校验")
    for name, payload in (("合法", good), ("缺字段", missing), ("类型错", wrong)):
        errs = validate(payload, REQUEST_SPEC)
        print(f"  {pad(name, 8)}{'通过' if not errs else '；'.join(errs)}")

    print()
    print("响应校验")
    resp = answer(good)
    print(f"  必填字段：{len(RESPONSE_SPEC)} 个，校验"
          f"{'通过' if not validate({k: resp[k] for k in RESPONSE_SPEC}, RESPONSE_SPEC) else '不通过'}")
    again = answer(good)
    print(f"  幂等：同一问题重复提交，缓存命中 {again['cached']}，检索调用仍为 {len(CALLS)} 次")

    print()
    print("时序")
    for no, direction, text in sequence().steps:
        print(f"  {no}. {pad(direction, 24)}{text}")


if __name__ == "__main__":
    main()
