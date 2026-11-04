"""从项目到产品的边界：把收尾阶段涌进来的需求分成三类。

分类靠三个问题，不靠感觉：是不是只改参数、别的客户要不要、动不动数据或权限模型。
答完就落一个去处，不留「再看看」。

运行（在 src/ 下）：python -m ch08.boundary
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

PRODUCT, CONFIG, DECLINE, HOLD = "产品能力", "配置项", "不接", "待评估"


@dataclass(frozen=True)
class Ask:
    text: str
    param_only: bool        # 只改参数、文案或映射
    multi_need: bool        # 其他客户也需要
    model_change: bool      # 要动数据模型或权限模型
    owner: str = "产品"


def classify(a: Ask) -> tuple[str, str]:
    if a.param_only:
        return CONFIG, "只改参数或文案，写进配置项清单，交付侧自己改"
    if a.multi_need and a.model_change:
        return PRODUCT, "多个客户都要，且要动模型，进产品需求池排期"
    if a.multi_need:
        return PRODUCT, "多个客户都要，先做成可选开关"
    if a.model_change:
        return DECLINE, "只有一个客户要，还要改模型，走定制合同另立项"
    return HOLD, "只有一个客户要，改动边界还没看清，定复查日再评"


ASKS: tuple[Ask, ...] = (
    Ask("把对话记录导出成表格", False, True, False),
    Ask("回答里加上我们公司的审批流", False, False, True),
    Ask("支持单点登录", False, True, True),
    Ask("改欢迎语与拒答话术", True, False, False),
    Ask("接入内部 OA 待办", False, False, False),
    Ask("答案改用方言回复", False, False, False),
    Ask("按成本中心限制可见范围", False, False, True),
    Ask("首页加一张使用量卡片", False, True, False),
)


def pad(text: str, size: int) -> str:
    width = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, size - width)


def main() -> None:
    print(pad("需求", 30) + f"{'结论':<8}理由")
    counts: dict[str, int] = {}
    for a in ASKS:
        verdict, why = classify(a)
        counts[verdict] = counts.get(verdict, 0) + 1
        print(pad(a.text, 30) + f"{verdict:<8}{why}")

    print()
    for k in (PRODUCT, CONFIG, HOLD, DECLINE):
        if k in counts:
            print(f"  {k}  {counts[k]} 条")
    print()
    print("四类去处不同：产品能力进需求池，配置项进清单，待评估定复查日，不接当场回。")
    print("边界写在合同附件里，比写在会议纪要里管用。")


if __name__ == "__main__":
    main()
