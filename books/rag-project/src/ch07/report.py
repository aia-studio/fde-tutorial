"""把三节的结论汇成一份可提交的二期方案。

方案能不能交评审，不靠谁觉得差不多，靠四条闸门都是通过。
少一条就写清缺什么，退回补，不改口径。

运行（在 src/ 下）：python -m ch07.report
"""

from __future__ import annotations

from ch07.intake import REQUESTS, evaluate
from ch07.tenancy import CORPUS, IDENTITIES, QUESTIONS, leaks, retrieve
from ch07.upgrade import DOCS, build, metrics

OWNERS = {
    "售后备件问答": "售后主管",
    "财务报销政策": "财务共享中心负责人",
    "员工 IT 工单": "IT 服务台主管",
    "供应商合同条款": "法务",
}


def gate_rows() -> list[tuple[str, str, str, bool]]:
    entered = [r for r in REQUESTS if r.verdict == "接入"]
    bad = sum(leaks(retrieve(CORPUS, ctx), ctx) for ctx in IDENTITIES for _ in QUESTIONS)
    _, m_old, _ = metrics(build(use_title=False, with_synonym=False), False)
    _, m_new, _ = metrics(build(use_title=True, with_synonym=True), True)

    all_owned = all(OWNERS.get(r.name) for r in entered)
    return [
        ("接入条目", f"{len(entered)} 条", "至少 1 条", bool(entered)),
        ("越权扫描", f"{bad} 条", "等于 0", bad == 0),
        ("索引升级", f"名次 {m_old:.3f} → {m_new:.3f}", "不下降", m_new >= m_old),
        ("验收人", "全覆盖" if all_owned else "有缺口", "每条都有", all_owned),
    ]


def main() -> None:
    entered = [r for r in REQUESTS if r.verdict == "接入"]
    watched = [r for r in REQUESTS if r.verdict == "观察"]
    declined = [r for r in REQUESTS if r.verdict == "不接"]

    print("二期范围与接入方案")
    print()
    print("接入")
    for i, r in enumerate(entered, 1):
        _, why = evaluate(r)
        print(f"  {i} {r.name}｜验收人：{OWNERS.get(r.name, '待定')}")
        print(f"    前置：{why}")
    print("观察")
    for r in watched:
        _, why = evaluate(r)
        print(f"  - {r.name}｜{why}")
    print("不接")
    for r in declined:
        _, why = evaluate(r)
        print(f"  - {r.name}｜{why}")

    print()
    print("闸门")
    rows = gate_rows()
    for name, value, need, ok in rows:
        print(f"  {name:<8}{value:<18}要求 {need:<8}{'通过' if ok else '不通过'}")

    print()
    if all(ok for *_, ok in rows):
        print(f"结论：可提交评审。语料 {len(DOCS)} 块（合并重复后 "
              f"{len({d.text for d in DOCS})}），覆盖 {len(IDENTITIES)} 个身份。")
    else:
        miss = [name for name, *_, ok in rows if not ok]
        print(f"结论：退回。缺 {'、'.join(miss)}。")


if __name__ == "__main__":
    main()
