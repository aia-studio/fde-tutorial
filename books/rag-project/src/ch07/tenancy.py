"""权限与多租户：过滤放在检索前，不放在回答后。

这里把检索分数固定，只验证一件事：过滤位置不同，模型看到的候选差多少。
企业里最常见的错法不是漏做权限，而是把权限做在生成之后的展示层——
卡片看不见了，答案里已经把那句话写出来了。

运行（在 src/ 下）：python -m ch07.tenancy
"""

from __future__ import annotations

from dataclasses import dataclass

K = 3


@dataclass(frozen=True)
class Chunk:
    id: str
    tenant: str
    groups: frozenset[str]
    text: str
    score: float


@dataclass(frozen=True)
class Ctx:
    tenant: str
    groups: frozenset[str]


CORPUS: tuple[Chunk, ...] = (
    Chunk("L1", "华阳物流", frozenset({"物流"}), "运单查询与签收异常处理", 0.95),
    Chunk("F1", "华阳精工", frozenset({"财务"}), "差旅报销的提交时限", 0.91),
    Chunk("S1", "华阳精工", frozenset({"售后"}), "备件到货时间以供应商排产为准", 0.88),
    Chunk("F2", "华阳精工", frozenset({"财务"}), "发票抬头与税号的填写要求", 0.84),
    Chunk("S2", "华阳精工", frozenset({"售后"}), "备件退换需要先登记故障现象", 0.80),
    Chunk("I1", "华阳精工", frozenset({"IT"}), "VPN 账号申请与重置", 0.77),
    Chunk("S3", "华阳精工", frozenset({"售后"}), "备件缺货时的替代型号建议", 0.74),
)


def allowed(c: Chunk, ctx: Ctx) -> bool:
    return c.tenant == ctx.tenant and c.groups <= ctx.groups


def visible(chunks: tuple[Chunk, ...], ctx: Ctx) -> list[Chunk]:
    """可检索范围：同租户，且文档受众是当前身份的组集合的子集。"""
    return [c for c in chunks if allowed(c, ctx)]


def retrieve(chunks: tuple[Chunk, ...], ctx: Ctx, k: int = K) -> list[Chunk]:
    """正确做法：先收窄范围，再按分数取前 k。模型只看得到这些。"""
    return sorted(visible(chunks, ctx), key=lambda c: -c.score)[:k]


def context_late(chunks: tuple[Chunk, ...], ctx: Ctx, k: int = K) -> list[Chunk]:
    """错误做法：全局取前 k 直接喂给模型，展示层再按身份隐藏卡片。"""
    return sorted(chunks, key=lambda c: -c.score)[:k]


def shown(chunks: tuple[Chunk, ...], ctx: Ctx) -> list[Chunk]:
    """展示层过滤后的卡片。过滤发生在这里时，模型已经读过越权内容。"""
    return [c for c in context_late(chunks, ctx) if allowed(c, ctx)]


def leaks(context: list[Chunk], ctx: Ctx) -> int:
    return sum(1 for c in context if not allowed(c, ctx))


IDENTITIES: tuple[Ctx, ...] = (
    Ctx("华阳精工", frozenset({"售后"})),
    Ctx("华阳精工", frozenset({"财务"})),
    Ctx("华阳精工", frozenset({"IT"})),
    Ctx("华阳精工", frozenset({"售后", "财务"})),
    Ctx("华阳物流", frozenset({"物流"})),
)
QUESTIONS = ("备件多久到货", "报销时限是几天", "发票怎么开", "VPN 连不上")


def main() -> None:
    ctx = Ctx("华阳精工", frozenset({"售后"}))
    early = retrieve(CORPUS, ctx)
    late = context_late(CORPUS, ctx)
    print(f"检索位置对比（k={K}，身份：华阳精工 / 售后）")
    print(f"  前置过滤  模型看到 {len(early)} 条：{' / '.join(c.id for c in early)}")
    print(f"            越权 {leaks(early, ctx)} 条")
    print(f"  后置过滤  模型看到 {len(late)} 条：{' / '.join(c.id for c in late)}")
    print(f"            越权 {leaks(late, ctx)} 条，展示层可见 {len(shown(CORPUS, ctx))} 条")
    print("  卡片能藏，答案藏不住。空出来的名额也补不回来。")
    print()

    bad_early = bad_late = 0
    total = 0
    for ctx in IDENTITIES:
        for _ in QUESTIONS:
            total += 1
            bad_early += leaks(retrieve(CORPUS, ctx), ctx)
            bad_late += leaks(context_late(CORPUS, ctx), ctx)
    print(f"越权扫描（{len(QUESTIONS)} 个问题 × {len(IDENTITIES)} 个身份，共 {total} 次）")
    print(f"  前置过滤  越权 {bad_early} 条")
    print(f"  后置过滤  越权 {bad_late} 条")
    print()

    for ctx in IDENTITIES:
        assert not leaks(retrieve(CORPUS, ctx), ctx), ctx
    print("断言通过：前置过滤下，进入模型的每一条都属于当前租户与当前组。")
    print("口径：越权指进入模型上下文的文档里，租户不同或受众组不在当前身份中。")


if __name__ == "__main__":
    main()
