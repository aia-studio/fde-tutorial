# tests/ · 闸门自测样本

每套都是一个能直接跑通的最小书项目，用来回归闸门与装配。字数刻意压到 300–500，
真实书稿按 genre 默认（practical 5000–7000）。

| 目录 | genre | 预期 `check.py` |
| --- | --- | --- |
| `fixture/` | practical | ch01 通过；ch02 反例 → **8 error / 2 warn** |
| `fixture-principle/` | principle | **0 error / 0 warn** |
| `fixture-project/` | project | **0 error / 0 warn** |
| `fixture-interview/` | interview | **0 error / 0 warn** |
| `fixture-smoke8/` | practical × 8 | **0 error / 28 warn**（X04 连续重复，故意保留） |
| `fixture-ledger/` | principle | **0 error / 0 warn**，账本非空（claims/promises/ladder 都有数据） |

## 怎么跑

```bash
# 一次跑完全部基线与注入用例（推荐）
python tests/run_tests.py

# 或逐个跑
python scripts/check.py    --book tests/fixture-principle
python scripts/plan.py     --book tests/fixture-project
python scripts/state.py    --book tests/fixture-project --init
python scripts/state.py    --book tests/fixture-project --report
python scripts/assemble.py --book tests/fixture-project
```

`assemble.py` 在账本为空时会报占位问题（结语缺能力阶梯），这是设计行为——
"留占位"不等于通过，中英文占位都算。

## 为什么要有 `fixture-ledger`

`fixture/` 到 `fixture-interview/` 的账本基本是空的。空账本能跑出 0 error，
只证明**不误报**，证明不了**查过**——F 组（事实）和 X 组（一致性）此前就卡在这个状态。

`fixture-ledger/` 填满了四本账：两条带出处的 claim、一条已结清的承诺、两条单调的能力阶梯。
它同时承担两件事：

1. **正例**：有数据也应该 0 error，说明闸门不会因为"有账本"就乱报。
2. **注入基底**：`tests/run_tests.py` 在它的临时副本上故意造违规，断言每个错误码真能抓到。

注入用例（现 9 个）：

| 注入 | 期望 |
| --- | --- |
| 删掉一条 claim | `F01` |
| claim 去掉 source | `F02` |
| 承诺改 open | `X06` + 装配阻断 |
| 清空 promises | `X02` |
| 阶梯倒退 | `X03` |
| 同一别名挂两个术语 | `X08` |
| 首现术语未登记 | `X01` |
| 有 `src/chNN/` 无 `versions.lock` | `C04` |
| 合同缺必填字段 | `C06` |

## 各样本验证的重点

- **practical**：9 段骨架、标注白名单、禁用词、越级引用、代码路径、常见坑 3–5 条。
- **principle**：权衡表必须含「代价 / 适用条件」两列；失效边界 3–5 条；延伸阅读 2–3 条；
  反直觉开场 ≤10 行。
- **project**：每个 H3 必须含「决策 → 实施 → 验证」；交付物表含验收标准列；
  复盘必须有三段；风险登记必须是表。
- **interview**：一句话答案 ≤30 字；三档答案（及格/良好/优秀）；追问链固定三层；
  高频错误 3–5 条；自测必须给评分标准。

## 反例说明

`fixture/chapters/ch02.md` 是**刻意保留**的反例，用来验证闸门抓错，不要"修好"它。
它同时命中：缺骨架段、未知 H2、常见坑不足、非白名单标注、禁用词、不存在的代码路径、
越级引用、引用未声明章。

## 八章规模样本

`fixture-smoke8/` 是 8 章、5 波的规模样本：`ch02/ch03` 并行、`ch04/ch05` 并行、`ch06/ch07` 并行。
它由同一模板生成，整段文字重复，所以 X04 会报 28 条 warn——这是**故意保留**的。
注意 X04 现在量的是「最长连续重复」，报出来的都是 ≥60 字的成段复制；
真书里那种「这一节解决…」的套话碎片不会再累积成告警。

## 账本

除 `fixture-ledger/` 外，样本的 `.book/` 只有空 `glossary.json`。
事实组(F)与一致性组(X)因此无数据可判——不误报，也不代表查过。
需要验证 F/X 时用 `tests/run_tests.py` 的注入用例，或参照 `fixture-ledger/` 补账。
