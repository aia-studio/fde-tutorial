# genres/ · 体裁目录

这一层决定「一章长什么样」和「这本书有没有主线」。新增体裁不需要改 `check.py`：
可用体裁由本目录的 `*.yaml` **自动发现**（`scripts/schema_check.py` 的
`available_genres()`），`book.schema.json` 的 `genre` 只做格式校验，不再硬编码四种。

## 目录里有什么

| 文件 | 谁读 | 作用 |
| --- | --- | --- |
| `_core.yaml` / `_core.md` | 全部类型 | 跨类型宪法：语体、事实纪律、排版阈值、通用反模式、工具箱用途表 |
| `<genre>.yaml` | `check.py` / `plan.py` / `assemble.py` | 可量化字段：骨架、阈值、指纹初值、章纲必填字段、曲线、标注 |
| `<genre>.md` | 写手 / `assemble.py` | 散文解释：段落怎么写、标注含义表、反模式 |
| `presets.yaml` | `init_book.py --preset` | 混合 genre 预设组合（不是体裁，不参与自动发现） |

`_core` 与 `presets` 被自动发现排除，不要拿它们当体裁名。

## 新增一个体裁的最小步骤

1. **建两份文件**：`genres/<name>.yaml` + `genres/<name>.md`，文件名小写、只用
   `[a-z0-9_-]`。复制最接近的现有体裁改，不要从空文件开始。
2. **yaml 必填**（缺了不会被闸门发现，等于空壳）：

   ```yaml
   genre: <name>
   label: 一句话类型名
   extends: _core
   exclusive:
     skeleton: <name>-N          # 骨架标识，混合时用它判冲突
     spine_constraint: null      # null 不约束 / "none" / "capstone"
   stackable:
     annotations: [...]          # 【标注】白名单
     exercise_form: [...]
     code_required: false
   skeleton:                    # H2 骨架，detect: keys / heading / h3_range
     - {id: header, detect: keys, keys: [...], required: true}
     - {id: body, detect: h3_range, min: 4, max: 6, required: true}
   defaults:
     words_per_chapter: [4000, 6000]
     info_density_min: 1.0
     difficulty_curve: ramp      # ramp / flat / wave，check.py S19 会消费
   fingerprint: {...}
   plan_required_fields: [chapter, title, requires, references,
                          target_words, difficulty, deliverable]
   tool_purposes: {}             # 可选：覆盖 _core.yaml 的工具箱用途
   ```

3. **md 必填**：骨架各段的写法、一张 `| 【标注】 | 含义 |` 表（装配前言要读它，
   缺表会出现「（待补含义）」并被装配闸门判为占位）、练习形式、反模式清单。
4. **不用改的东西**：`schemas/book.schema.json`（genre 已改为 pattern + 动态发现）、
   `init_book.py`（自动发现）、`check.py`（按 yaml 字段消费）。只有引入了
   **全新的字段语义**才需要改脚本，改完在 SPEC §18 记一笔。
5. **最小样本**：在 `tests/` 下建 `fixture-<name>/`，两章、每章跑通全部骨架段，
   在 `tests/run_tests.py` 的 `BASELINE` 里加一行 `0 error / 0 warn`。
   没有通过样本的体裁等于「想象的模板」——条款都对，但没人照着写过。

## 混合 genre 的规则

- 排他维度只有两项：**章节骨架**与 `spine`，由 genre 列表第一个（主类型）决定。
- `spine_constraint` 现在由 `check.py` 的 P12 执行：主类型要求 `capstone` 而书写了
  `none` 会报 error；副类型的约束被忽略时会给 info，不静默调和。
- 可叠加维度取并集 / 取严：标注、反模式、断言词、`plan_required_fields` 取并；
  字数取交集；图表下限与信息密度取高；代码要求取严。
- 骨架全书统一，做不到「前 5 章原理骨架、后 5 章实战骨架」。这类书的解法见
  `GUIDE.md §6.3`：主类型骨架 + 在 H3 层容纳副体裁的固定小节。

## 阈值从哪来

四套现有体裁的阈值（如面试本一句话答案 ≤30 字）本质是**为唯一样本调的**。
第二本真书产出后应回归重定，不要为单一本书继续加阈值。
