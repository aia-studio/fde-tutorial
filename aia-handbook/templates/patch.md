# 波次 {{N}} 缝合清单

> 先出清单再落地，禁止边看边改。每波一个 commit，可整体回滚。
>
> 生成方式（不必手写骨架）：
> `python scripts/stitch.py --book <书目录> --wave {{N}} --out patches/wave-{{N}}.md`
> 它从 `check.py --json` 的 error/warn 转成清单，并排除章纲/配置类问题
> （G4、P12、B01、S19、S24）——那些不在缝合 agent 的权限内。

## 概览

- 波次：{{N}}　涉及章节：{{chNN, chMM}}
- 问题数：术语 {{a}} / 重复 {{b}} / 事实 {{c}} / 指纹 {{d}}
- 改动预算：单章 ≤20% 正文；触及结论段 → 打回原写手重跑

## ch{{NN}}

| # | 类别 | 位置 | 问题 | 修法 | 依据 |
| --- | --- | --- | --- | --- | --- |
| P1 | 术语 | 3.2 节 | 「召回」应为「检索召回」 | 全文替换 | glossary C021 |
| P2 | 重复 | 与 Ch05 5.3 重 4 句 | 删本章部分 | 改为「见 Ch05」 | X04 最长连续重复 |
| P3 | 事实 | 正文 92% | 与账本不一致 | 依 F023 改为 92% | claims F023 |

## 不可改动清单（越权即回滚）

- 章纲 `04-chapter-plans/**`
- 宪法 `03-style-guide.md`
- 章节结论与主张
- 事实账本的 `source` / `date`
- 依赖声明 `requires` / `references`

## 验收

- [ ] `check.py --book <书目录> --chapter ch{{NN}}` 0 error
- [ ] 改动行数 ≤ 正文 20%：`python scripts/stitch.py --budget --before <旧稿> --after <新稿>`
- [ ] 未新增未登记术语；X09 未报别名替代正名
- [ ] 事实性修改都能在 `claims.jsonl` / `glossary.json` 里找到依据
