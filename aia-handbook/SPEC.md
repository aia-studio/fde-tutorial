# 技术书生成 SKILL · 设计规格

> 状态：v1.0 · 规格锁定，§16 待定项不阻塞开工
> 本文件定义 skill 的调度模型与验收标准。实现以本文件为准。

## 1. 一句话

把「写一本书」当成一次构建调度：**章是节点，依赖是边，拓扑序给波次，同波并行，跨波只传合同。**

## 2. 核心模型

```
章 (chapter)   = 节点
requires       = 硬边（下游可无解释使用上游概念）
references     = 软边（下游只能写「详见 ChNN」）
mentions       = 不入图，不产生义务
波 (wave)      = 同一拓扑层，可并发
合同 (contract)= 节点产出物，跨波传递的唯一载体
```

**没有「样章阶段」这个独立工序。** 根节点（无上游的 1–3 章）在拓扑序上必须最先写，
它们在第一个会话里串行完成，天然承担定标作用。

## 3. 依赖声明

写在章纲 front-matter，由脚本编译成图，**禁止手绘**：

```yaml
# 04-chapter-plans/ch05.md
---
chapter: "05"
title: "混合检索"
requires: ["03"]          # 必须是完整章号
references: ["06", "08"]  # 允许前向
provides:
  concepts: ["C021", "C022"]
  modules: ["src/ch05/retriever.py"]
target_words: 6000
difficulty: 3             # 1–5，与全书节奏曲线对齐
deliverable: 带引用的问答服务   # 本章产出的可验收物，必须是名词
---
```

编译规则：

1. `requires` 必须无环 → 否则 `plan.py` 直接失败，报出环上的章号链
2. 解环只有两个手段：降级为 `references`，或把共享概念上提到更早的锚点节
3. `references` 允许指向更大的章号（前向引用），`requires` 不允许

**第 3 条的副作用：环在结构上不可能出现。** 只允许指向更小的章号，
等于强制章序 = 拓扑序，任何回路都会先被判成前向依赖。

所以 `plan.py` 里的环检测是**防御性代码**——防的是将来放开顺序约束。
现在跑不出来不要以为是漏测：在「章号即阅读顺序」的前提下，这是设计使然而非遗漏。

代价是不能表达「Ch07 依赖 Ch09 的结论」。真实需要时用 `references` 表达，
读者跳读也不会断。

**反向校验**（`check.py`）：正文出现 `ChNN`，但 `NN` 既不在 `requires` 也不在
`references` → 报警；反之声明了却没引用 → 提示清理。

## 4. 代码依赖规则

章内 code-first，因此跨章 import 必然存在。**不引入第二张 DAG**，改用一条校验：

> **代码的 import 图，必须是章依赖图的子图。**

即：跨章 import 必须蕴含 `requires` 边。Ch08 用了 Ch04 的 `cleaner.py`
→ Ch08 必须 `requires: ["04"]`。

```
check: import_graph ⊆ chapter_dag
exempt: src/common/**      # 公共库，无章归属，任何章可用
```

失败报错模板：

```
✗ Ch08 引用了 Ch04 的 cleaner.py，但章纲未声明 requires: ["04"]
  → 修 A：在 ch08.md 补声明（说明这确实是依赖）
  → 修 B：把 cleaner 抽到 src/common/（若只是工具函数复用）
```

**提取规则（rule of two）：** 同一个模块被 ≥2 章 import → 强制提取到 `src/common/`，
此时「补 `requires` 声明」不再是可接受解法。判定按阶递进：

| 引用情况 | 处理 |
| --- | --- |
| 单章内部使用 | 留在 `src/chNN/`，无约束 |
| 被另 1 章 import | 允许，但必须补 `requires` 边 |
| 被 ≥2 章 import | **强制提取**到 `src/common/`，`check.py` 直接判失败 |

`src/common/` 自身的约束：

- 每个模块必须有 `README.md`，写明职责、稳定接口签名、变更影响范围
- 只放**纯功能**，不放章节业务语义（`cleaner.py` 可以，`rag_pipeline.py` 不行）
- 任何对 `src/common/` 的修改 → **全量重验**（所有章重跑闸门），不做影响面分析

全量重验的理由：影响面分析本身就会漏——间接依赖、行为变更、调用方假设，
三种都算不出来。而重跑闸门是脚本，成本可控，漏一次的代价是出版级事故。

好处：不维护第二份状态，两张图不会打架；公共代码只存在一份，
不会出现「Ch04 的 cleaner 和 Ch08 的 cleaner 修了不同 bug」。

## 5. 章合同

位置 `.book/contracts/chNN.json`，≤400 字，写完即产出，供下游消费。

```json
{
  "chapter": "ch03",
  "defines": [
    {"id": "C012", "zh": "提示模板", "en": "Prompt Template",
     "def": "一段可复用、带变量占位的指令文本", "aliases": ["prompt 模板"]}
  ],
  "provides": [
    {"module": "src/ch03/llm_client.py",
     "api": "LLMClient.chat(messages: list[dict], model: str) -> str"}
  ],
  "assumes": ["C001 LLM", "C004 Token"],
  "hook": "工具调用是 Prompt 之后的下一个能力边界"
}
```

下游写手的输入 = 宪法 + 本章纲 + 上游合同集合 + 上游代码签名。
**不传上游全文。** 这是上下文控制，也是一致性的来源。

## 6. 调度

```
ready(n) = 所有 requires 上游状态为 done
wave(k)  = 第 k 拓扑层上所有 ready 的节点
batch    = wave 按并发上限切分（默认 4，可配）
```

节点状态机：

```
pending → ready → writing → checking → merging → done
                     ↑         │
                     └── repair ┘   （最多 2 次）
blocked （上游 failed 时，下游全部置 blocked）
```

- **`repair` 上限 2 次。** 第 3 次转人工。连续两次修不过，问题在章纲不在写手，
  继续重试只是烧 token。
- 状态持久化 `.book/state.json`，含 `attempts` 与 `last_error`。
  **任何会话中断后，读 state.json 即可续跑。**
- 并发上限不是越高越好：并用 20 个 agent 写 20 章，等于放弃全部交叉一致性。
  同一波次必须共用同一份宪法快照。

### 6.1 阅读波次与写作波次（真实书稿跑出来的）

`waves.json` 按 `requires` 切出的波次，约束的是**读者**：读到 Ch06 时 Ch05 必须已存在。

但**写手不必等 Ch05 写完**——只要 Ch05 的合同草案（章纲里的 `provides`）已冻结，
Ch06 的写手就能照着草案写，实际签名对不齐的部分交给缝合阶段修。

所以调度是两张表：

| 表 | 依据 | 用途 |
| --- | --- | --- |
| 阅读波次 | `requires` 拓扑层 | 闸门顺序、装配顺序、读者路径 |
| 写作波次 | 篇/组划分 + 合同草案冻结 | 实际派活与并发 |

实测（《RAG 入门到实战》10 章）：阅读波次 **8**，写作波次可压到 **4**（按篇）。

**判据：关键路径 ≈ 章数时，这本书是一条流水线。** 内容确实要按顺序读，
但写作不必按顺序写。如果工期是瓶颈，唯一的出路就是这两张表分离；
如果一致性是瓶颈，就老老实实按阅读波次走。

代价：并行写作会出现签名对不齐、概念定义微差，靠缝合修。
所以 `provides` 必须写到函数签名级，光给路径等于没给。

## 7. 一致性的三重保证（非人力）

### 7.1 概念注册表 `.book/glossary.json`

```json
{"id": "C007", "zh": "薄切片", "en": "Thin Slice",
 "def": "先端到端跑通一条最窄链路，再逐步加厚",
 "first_chapter": "ch25", "aliases": ["细切片", "窄切片"]}
```

- 宪法阶段建立初版（从定位与目录中抽取）
- 写手只能用注册过的术语；造新词必须登记，不得为已有概念另起名
- `check.py` 双向查：未登记术语出现 / 同一 id 出现两种定义

### 7.2 文风指纹 `.book/style-fingerprint.json`

第一波完成后抽取，后续每章比对：

| 特征             | 偏离后果            |
| -------------- | --------------- |
| 平均句长 / 句长标准差   | 句式退化成短句堆砌或长难句   |
| 平均段长           | 违反「一段一个意思」      |
| 每千字标注密度 + 分布   | 滥用标注凑字数         |
| 每节图表数          | 退化成纯散文          |
| 代码块平均行数        | 正文贴大段代码         |
| 人称分布           | 中途改口「本文」「笔者」    |
| 开场句式命中         | 每章同一个模子         |

**阈值来源（两级）：**

1. `genres/<genre>.yaml` 给一组初值（均值 + 允许带宽），记 `source: genre-default`
2. 第一波完成后，用根节点章的中位数覆盖初值，带宽 ×1.2 放宽（样本少），
   记 `source: calibrated`

只有 1 个根节点时不做校准，直接沿用 genre 初值——单样本校准没有意义。

超阈值 → 该章进 `merging` 队列，**不阻断**其他章。人工只看报警清单。

### 7.3 波次整合（每波结束跑一次）

```
术语碰撞 → 跨章重复段落（5-gram 重叠）→ 前向依赖违规 → 指纹偏离
```

在下一波发射**之前**完成。用增量方式换回一部分串行的一致性，
成本远低于全书写完再缝合。

**整合发现的一切问题都交 agent 修**，包括事实性错误、前后矛盾、连贯性断裂，
不设人工确认环节。但必须给出权责边界与改动预算，否则缝合会退化成重写。

| 缝合 agent 可以改 | 不可以改 |
| --- | --- |
| 术语用词、定义措辞 | 章纲（`04-chapter-plans/**`） |
| 衔接句、转场、章节钩子 | 宪法（`03-style-guide.md`） |
| 与已登记事实冲突的数字 | 章节的结论与主张 |
| 重复段落的删并 | 事实账本里的 `source` 与 `date` |
| 交叉引用编号 | 依赖声明（`requires` / `references`） |

两条硬约束：

1. **事实性错误必须回源，不许自造正确值。** 缝合 agent 发现「Ch08 写 92%，
   Ch12 写 78%」，正确动作是查 `claims.jsonl` 取权威值，把错的一方改成与账本一致；
   账本里没有就补登来源，绝不能自己算一个数填进去。
2. **改动预算：单章修改超过 20% 正文，或触及结论段，打回原写手重跑。**
   缝合 agent 没有章纲的完整上下文，大改必然把文风带偏——它擅长的是缝合，
   不是重写。

工作方式：**先出 patch 清单（章节 / 位置 / 问题 / 修法 / 依据），再逐条落地**，
每波一个 commit，可整体回滚。

## 8. 闸门（全硬，5 组）

| 组   | 条目                                                             | 不过的处理        |
| --- | -------------------------------------------------------------- | ------------ |
| 结构  | 骨架段落齐全（按别名表匹配）· 汉字数 ≥ `target_words × 0.75` · 节数 ∈ [4,6] · 每节 ≥1 图或表 · 章首导图存在 · 信息密度 ≥ 下限 · `difficulty` 与章纲一致 | repair       |
| 引用  | 图产物存在 · 图 `source` 已声明 · `src/` 路径存在 · 无前向 `requires` · 交叉引用止于章级 · import 图 ⊆ 章依赖图 | repair       |
| 一致性 | 术语未登记/多定义 · 标注越界 · 禁用词命中 · 跨章重复 · 承诺未兑现（`promises.jsonl` 中仍为 `open`） | 记入缝合清单，不阻断   |
| 代码  | 每章 README 含运行命令与实测输出 · `python -m` 可执行 · 正文代码块 ≤30 行 · 密钥扫描       | repair       |
| 事实  | 正文数字必须在 `claims.jsonl` 登记 · 每条 claim 有 source+date · 术语首现章号一致    | repair       |

**统计口径：** 汉字数只计正文与表格；代码块、图注（`> 图 x-x …`）、引用块不计。
句子按 `。！？；` 切分，代码块内不计；段落按空行分隔。
口径不统一，字数闸门和文风指纹都会飘。

**S05 的例外：** 小节内的代码块与图、表等价，都算「非散文支撑物」。
只有通篇散文（既无图、无表、无代码）的小节才报警——否则纯代码小节会被反复误报，
而误报多了闸门就失效了。

**字数纪律：** 低于 `0.75 × target` 判不合格；高于 `1.25 × target` 不报错，
但要求回改**章纲**的 `target_words`——字数是纲估错的信号，不是压字能解决的。
两侧同样 ±25%，处理方式不同。

### 8.1 事实账本与溯源策略

`claims.jsonl` 存的是**数字的出处**，不是数字本身。

```json
{"id": "F023", "chapter": "ch08", "value": 92, "unit": "%",
 "claim": "混合检索相比纯向量检索的召回率提升",
 "source": "内部评测报告 / 50 页手册样本", "date": "2026-09"}
```

闸门义务按三层递进，**不做全量登记**：

| 层 | 规则 |
| --- | --- |
| ① 结构豁免 | 代码块内、行号、章号、端口、超时值、版本号、年份 → 直接跳过 |
| ② 断言识别 | 仅带单位（`%` / `倍` / `ms` / `QPS` / `万元` / `GB`）或与「提升/下降/占比/市场规模/薪酬/失败率/准确率」同段的数字，产生登记义务 |
| ③ 容差匹配 | 规范化数值（去空格、去千分位、全角转半角）+ 同段断言词，容差 ±0.5%（吸收四舍五入） |

全量登记不可取：正文九成数字是版本号与参数，一刀切会让每章产生两百条误报，
写手第一周就学会无视告警——这比不检查更糟。

维护成本集中在②的词表：内置一份通用断言词表，`book.yaml` 可按领域追加。

## 9. 图渲染管线

```yaml
figure:
  renderer: mmdc        # mmdc | browser | kroki | none
  format: svg           # 默认 svg
  htmlLabels: false     # 关键：避免 foreignObject，走原生 <text>
  theme: neutral
  width: 1600
```

渲染命令：

```bash
npx -y @mermaid-js/mermaid-cli \
  -i figures/ch04/fig-04-1-pipeline.mmd \
  -o assets/ch04/fig-04-1-pipeline.svg \
  -c mermaid.config.json -b transparent
```

选型理由（记录备查）：

- **SVG 而非 PNG**：同图 PNG 200–300 KB，SVG 20–30 KB；文本可进 git diff；
  缩放不失真；将来出 PDF 无需重做。
- **`htmlLabels: false`**：Mermaid 默认用 `<foreignObject>` 包 HTML 文字，
  Gitee 与部分编辑器不渲染，会出空白。关掉后文字变成 SVG 原生 `<text>`，
  走阅读器字体回退栈——这是跨平台兼容的真正解法，比装字体可靠。
- **mmdc 而非无头浏览器截图**：三平台命令完全一致；不需要按平台解析 exe 路径，
  不需要额外裁切。代价是首次拉 Chromium 约 200 MB，可在 CI 缓存。

校验口径：**只验语法与存在性，不做像素比对。** 源码能被 mmdc 解析、产物存在、
体积 < 200 KB、正文引用路径可达，即算通过。SVG 出问题几乎都是语法问题，
像素比对的收益不抵成本。

## 10. DAG 质量指标（blueprint 阶段产出）

| 指标     | 含义       | 阈值                          |
| ------ | -------- | --------------------------- |
| 关键路径长度 | 最短工期（波数） | > 8 → 依赖过密，考虑放宽 `requires` |
| 最大波宽   | 并发峰值     | 与并发上限严重不匹配 → 目录失衡           |
| 最大扇出   | 被依赖最多的节点 | 被 > ⅓ 章依赖 → 拆或前置            |
| 孤立节点   | 无边章      | 存在即提示该章实为独立文章               |

**这四项在确认目录时必须一起看。** 目录不只是内容结构，还是调度结构。

`spine: capstone` 时额外产出一条「项目推进曲线」：逐章标注项目推进到哪一步，
检测是否出现连续多章项目原地不动。

## 11. 参数化

一本书的全部可变部分集中在 `book.yaml`：

```yaml
title: 《XXX》
genre: practical          # practical | principle | project | interview
lang: zh-CN
audience: {who: 后端转 AI 的工程师, level: 中级, prerequisite: [Python, HTTP]}
spine: capstone           # capstone | running-example | none
scale: {chapters: 30, words_per_chapter: [5000, 7000]}
deliverables: [markdown, code, figures]
gates: hard
concurrency: 4
stack: {python: "3.12", llm: "OpenAI 兼容 + Ollama", mock: true}
```

### spine 三档

| 档                 | 含义                      | 约束                                      |
| ----------------- | ----------------------- | --------------------------------------- |
| `capstone`        | 一条贯穿项目串全书，每章都要推进它       | 强制产出「项目推进曲线」；无推进的章要么改纲要么合并              |
| `running-example` | 一个例子跨若干章复用，但不要求每章推进     | 例子需在宪法里定死，后续不得改名                        |
| `none`            | 各章独立                    | 章间 `requires` 应显著减少，否则说明其实是第一档           |

**`genre: project` 强制 `spine: capstone`**，不允许 `none`。

### genre 的四层结构

```
constitution.core.md      # 语体、事实纪律、通用反模式（所有 genre 共有）
genres/<genre>.md         # 异构段落：章节骨架、标注体系、练习形式（整段替换）
genres/<genre>.yaml       # 同构字段：字数、图表下限、代码占比、指纹初值
<book>/03-style-guide.md  # 书级 override，只写与 genre 的差异
```

合并顺序 `core → genre.md → genre.yaml → book override`，后者覆盖前者。

分层依据：genre 的差异一半是「同一件事的不同取值」（字数、图表下限、代码占比），
一半是「完全不同的段落」（骨架、标注、练习）。
**散文管不可量化的，字段管可量化的。**

**四套 genre 一次做全**（practical / principle / project / interview），
不留空壳——空壳会在使用时被临时解释，比没写更糟。

### 混合 genre

```yaml
genre: [project, practical]   # 第一个是主类型
```

混合的合并规则取决于维度性质，**不是简单叠加**：

| 维度性质 | 包含 | 合并规则 |
| --- | --- | --- |
| **排他**（一章只能有一种） | 章节骨架 · `spine` | 由主类型决定，副类型不得覆盖 |
| **可叠加** | 标注体系 · 练习形式 · 字数区间 · 图表下限 · 代码要求 · 反模式清单 · 断言词表 · 指纹初值 | 取严或取并：标注与练习取并集、字数取交集、图表取高、代码取严（runnable > snippet > none）、清单取并集 |

**排他只剩两项**，一句话记住：**只有「一章长什么样」和「有没有主线」是排他的，其余都能并。**

多一套标注词汇不构成矛盾——`project` 的书里出现【排查】读者不会困惑，
不兼容的是骨架：一章不可能同时是「阶段→验收」和「考点→追问」。

这条修正的附带好处：冲突检测从四个维度降到两个，混合 genre 的误报大幅减少。

一条硬约束：**骨架冲突不得静默处理，必须显式说明采用了谁的。**

```
! genre: [project, practical] 骨架不一致
  采用 project-8  : 阶段 → 需求 → 实现 → 验收
  忽略 practical-9: 场景 → 原理 → 动手 → 排错
  → 想换主类型，把 genre 列表顺序调过来
```

列表顺序即主类型声明，所以冲突本身不算错误——但「用了谁的、忽略了谁的」
必须打出来。读者读到第 10 章发现节奏突变时，至少能查到是这里定的。

`init_book.py` 另外要求：两套骨架不同且用户没显式写顺序（单字符串形式）
才允许通过；写成列表就必须自己排好。

另外 `genre: project` 强制 `spine: capstone`，副类型不得把它降级。

### 一次做全的风险与对策

后三套 genre 没有验证样本，容易写出「想象的模板」——条款都对，但没人照着写过。

对策：每套先出**最小可用版**（core 差异 + 骨架 + 一张字段表，约 60 行），
拿真实书稿写 2 章再补厚。第一版追求「能跑」，不追求「完备」。

## 12. 章节文件约定

闸门要判「骨架齐全」，前提是骨架可被机器识别。约定如下：

| 层级 | 用法 |
| --- | --- |
| H1 | 章标题，格式 `# ChNN <标题>`，编号必须与文件名一致 |
| H2 | **骨架段**，标题必须命中别名表 |
| H3 | 正文小节，格式 `### NN.M <标题>`，节数按 H3 计 |

骨架的识别规则声明在 `genres/<genre>.yaml` 的 `skeleton` 里，两种检测方式：

```yaml
skeleton:
  - id: header        # 头块是引用块不是标题，用键名检测
    detect: keys
    keys: [本章解决, 前置, 阅读]
  - id: mindmap
    detect: heading
    aliases: [章首导图, 本章结构]
  - id: opening
    detect: heading
    aliases: [场景开场, 开场]
  - id: body
    detect: h3_range
    min: 4
    max: 6
  - id: summary
    detect: heading
    aliases: [本章小结, 小结]
```

规则：

- 命中别名任一即算该段存在。**别名表是唯一可接受的写法**，不接受的写法一律报错
- 出现不属于任何 `id` 的 H2 → 报「未知骨架段」，不静默忽略
- 段顺序必须与 `skeleton` 声明顺序一致，乱序报错
- 缺段、重复段、段内为空，三者同级处理

好处：写手不需要理解「结构」，只需要照别名写标题；
脚本不需要理解内容，只需要数标题。两边都不会自由发挥。

## 13. 书项目目录

```
<book>/
├── book.yaml
├── 00-positioning.md
├── 01-outline.md
├── 02-toc.md
├── 03-style-guide.md          # 宪法，冻结后只读
├── 04-chapter-plans/chNN.md   # 含 front-matter 依赖声明
├── .book/
│   ├── dag.json  waves.json  state.json
│   ├── glossary.json  claims.jsonl
│   ├── style-fingerprint.json
│   └── contracts/chNN.json
├── dep-brief/chNN.md          # 自动生成的上游摘要包
├── chapters/chNN.md           # 写作区
├── src/chNN/                  # 可运行代码
├── figures/chNN/*.mmd         # 图源码（唯一真相）
├── assets/chNN/*.svg          # 渲染产物，不手改
└── final/                     # 装配产物
```

## 14. v1 范围

| 项 | 决定 |
| --- | --- |
| 验证方式 | 先拿一本 **8–12 章的小书**跑通全链路（DAG → 波次 → 缝合 → 装配） |
| genre | 四套一次做全，每套先出最小可用版约 60 行，用真书 2 章验证后补厚 |
| 增量（v1） | 结构三件套 + 节奏两件 + 资产四件 + **外围文本**（十件全收） |
| 增量（v2） | 读者模拟通读 · 混合 genre 预设组合 · 多作者协作 |
| 最终形态 | 仓库直读优先；元数据按出版标准预留（图 `source/license`、`versions.lock`、索引可后加） |

v1 的验收标准：**拿一本 10 章的书从头跑到 `final/`，全程除立项与目录确认外不需要人工介入。**

## 15. 书级产物（外围文本）

外围文本不是章节，不参与章 DAG，但有独立的依赖与生成时机。
七个产物里四个可从账本自动生成——这是维护账本的额外回报。

| 产物 | 依赖 | 时机 | 方式 |
| --- | --- | --- | --- |
| 前言 | 定位、目录、阅读路径、能力阶梯起点 | 目录锁定后、第 1 波之前 | 手写，统稿回填 |
| 结语 | 能力阶梯终点、承诺账本、项目终态 | 最后一波之后 | 手写 |
| 术语表 | `glossary.json` | 装配 | 自动 |
| 参考文献 | `claims.jsonl` 的 `source` 去重 | 装配 | 自动 |
| 版本声明 | `versions.lock` | 装配 | 自动 |
| 工具箱 | `stack` + `src/` 依赖清单 | 装配 | 半自动 |
| FAQ | 各章「常见坑」汇总 + 承诺账本 `dropped` 项 | 装配 | 半自动 |

### 前言要写两次

编辑常识，但流水线里必须显式安排：

- **初稿在开写前**：强迫说清「给谁、讲什么、不讲什么、怎么读」。
  写不出来说明定位没定好，此时返工最便宜。
- **终稿在装配时**：回填真实章数、图数、代码量、版本号。
  初稿里的「约 30 章」必须变成确定数字。

### 前言必须包含的五项（闸门）

1. 读者画像与前置知识——须与 `book.yaml` 的 `audience` 一致，不得矛盾
2. 三条阅读路径（快速 / 完整 / 复习）——须与附录的路径表一致
3. 本书不讲的——须与 `00-positioning.md` 的范围边界一致
4. **标注体系说明**——书里用了哪些【】标记、各自什么意思
5. 代码运行约定（环境、Mock 模式、三条命令跑起来）

第 4 项最容易被漏。自定义标注如果不在前言解释，读者第一次见【代价】【待确认】
只会当成装饰。

### 结语的约束

结语声称「读完你现在能做到 X」，X 必须与能力阶梯的**终点条目**逐条对应，
不得新增 ladder 里没有的能力。这是全书唯一一处允许「概括」，但概括的内容
必须可追溯到具体条目。

## 16. v1 增量规格

### 16.1 信息密度（闸门输入）

```
density = 可操作单元数 / 汉字数 × 1000
```

可操作单元，各计 1 个：

| 单元 | 计法 |
| --- | --- |
| 编号步骤组 | 连续 ≥2 步的编号列表，每组 1 个 |
| 代码块 | 每块 1 个；> 30 行的算 2 个 |
| 表格 | ≥3 行的表格，每个 1 个 |
| 图 | 每张 1 个 |
| 练习 | 每道带验收标准的练习 1 个 |

阈值按 genre：`practical` 1.2 / `principle` 0.7 / `project` 1.5 / `interview` 0.9，
可由 `book.yaml` 的 `limits.info_density_min` 覆盖。

**为什么不直接用字数：** 字数下限会诱使把一句话拆成三句。密度抓的是"每千字里
有多少东西读者能上手做"，注水无处可藏。

### 16.2 难度分级（1–5）

判据必须可操作，按「需要的先验知识 + 失败后果」定级：

| 级 | 判据 |
| --- | --- |
| 1 | 单一概念，无前置，照抄即可 |
| 2 | 两个概念组合，需理解参数含义 |
| 3 | 多组件协作，需自己判断顺序或阈值 |
| 4 | 跨章综合，或涉及有代价的方案取舍 |
| 5 | 需要外部条件（集群 / 真实数据 / 现场环境），失败代价高 |

约束：

- 首章 ≤ 2。读者还没进来，难度 4 的开局会劝退
- 连续 `difficulty_max_run`（默认 3）章 ≥4 → 报错，须插缓冲章
- 连续 3 章不升 → 只提示不阻断（可能是正常的平缓区）
- 全书曲线由 genre 的 `difficulty_curve` 决定：`ramp` / `flat` / `wave`

### 16.3 能力阶梯 `.book/ladder.jsonl`

```json
{"chapter": "ch03",
 "before": ["会调 API 拿到字符串"],
 "after":  ["会调 API 拿到字符串", "能按结构解析", "能处理重试"],
 "covers": ["C012", "C013"]}
```

校验规则（全部硬性）：

1. `after` ⊇ `before` —— 能力不倒退
2. 相邻章 `after` ⊇ 前一章 `after` —— 全局单调递增
3. 第 1 章 `before` 必须与 `audience.prerequisite` 一致
4. 末章 `after` 构成结语的能力清单，**结语不得新增 ladder 里没有的能力**
5. `covers` 里的概念必须在 `glossary.json` 登记

第 4 条是结语唯一的硬约束，也是这套东西存在的理由：
防止结语吹一堆书里没教过的能力。

### 16.4 承诺账本 `.book/promises.jsonl`

```json
{"id": "P007", "opened_in": "ch03",
 "text": "为什么大多数场景不该上微调",
 "kind": "forward", "fulfilled_in": "ch11", "status": "done"}
```

`kind` 三种：`forward`（后面会讲）/ `artifact`（后面会给代码）/ `promise`（承诺读者能做到）。

规则：

- 写手每章必须登记本章新开的所有承诺
- 正文出现「后面会」「接下来」「稍后」「下一章」「留到」等触发词，但本章
  `promises.jsonl` 没有新增记录 → 报警
- `status: open` 在统稿时非空 → **阻断装配**
- `dropped` 必须写 `reason`，并自动收进 FAQ 附录

### 16.5 阅读路径

每节（H3）标题后第一行标注：

```markdown
### 3.2 向量化

> 路径：必读
```

三值：`必读` / `选读` / `参考`。缺省视为 `必读`。

从标注生成三条路径：

| 路径 | 内容 |
| --- | --- |
| 快速 | 必读小节 + 每章小结 |
| 完整 | 全部 |
| 复习 | 必读小节 + 自查清单 + 常见坑 |

闸门：每章「必读」占比 ∈ [0.5, 0.8]。过低说明这章没有主线，过高说明标了等于没标。

### 16.6 图许可

图源码（`.mmd` / `.svg`）的 front-matter：

```
%% source: self
%% credit: 改编自 Mermaid 官方文档 https://...
%% license: CC BY 4.0
```

- `source`: `self` / `adapted` / `external`
- `self` 可省略 `credit`；`adapted` 与 `external` 必须同时有 `credit` + `license`
- 正文图注末尾追加「（改编自 X）」或「（来源：X）」
- 闸门：`adapted`/`external` 缺 `credit` → repair

### 16.7 版本锁 `versions.lock`

```yaml
updated: 2026-10
verified_on: 2026-10-29
runtime: {python: "3.12", node: "20"}
dependencies:
  langgraph: "0.2.53"
  fastapi: "0.115.0"
```

- 来源：各章 `requirements.txt` 合并去重，或 `pip freeze` 过滤
- 版本声明附录由它生成，前言引用它
- 弱校验：`src/` 里 import 的包，主版本（major.minor）必须与 lock 一致。
  只比主版本，避免补丁升级就报警

### 16.8 capstone 里程碑快照

- tag 命名 `capstone/chNN`，每 `snapshot_every` 章一个（默认 5）
- 每个 tag 必须自包含：可运行的 `src/capstone/` + README（三条命令启动）+
  `.env.example`
- `final/README.md` 给出 tag 列表与「从任意节点开始读」的说明
- 仅 `spine: capstone` 时启用

理由：读者跳到第 20 章时，需要的是那一刻能跑的代码，不是终版代码。

### 16.9 示例数据可复现

- `src/data/` 只放生成脚本，不放数据本体
- 每个脚本首行固定 `SEED = 42`（或 genre 指定值），并在开头 `random.seed(SEED)`
- `src/data/README.md` 列出：脚本 → 产物文件 → 大小 → 用途
- 单文件 > 1 MB 不进库，改为脚本生成
- 闸门：正文引用的 `data/` 路径，必须能由某个脚本生成

## 17. 待定项（已结）

本节原有七项，本轮全部落地，保留记录以便追溯。

- [x] 多作者协作：`state.json` 加锁读改写 + 章节归属 + 冲突检测，见 `scripts/state.py`
- [x] 断言词表初版：`check.py` 内置 14 个通用词，领域词由 `book.yaml` 追加；宽度待真实书稿调
- [x] 混合 genre 预设：`genres/presets.yaml` 三组，`init_book.py --preset` 选用
- [x] `state.json` / `dag.json` / `contract` 的 JSON Schema：`schemas/` 下三份
- [x] `dep-brief` 模板与缝合 patch 格式：`templates/dep-brief.md`、`templates/patch.md`
- [x] repair 保留旧稿：`.book/history/chNN/attempt-N.md` + `state.history`，可回滚
- [x] `final/` 产物清单：见 `references/07-assembly.md` §一

## 18. 实现状态（持续更新）

规格先于实现。本节如实记录脚本进度，避免"文档宣称全做、脚本只做一半"的误导。

### 脚本

| 脚本 | 职责 |
| --- | --- |
| `check.py` | 五组闸门 + 全书级 + 资产级校验 |
| `plan.py` | 编译 DAG、切波次、四项指标；落盘 `.book/dag.json` 与 `waves.json`（写盘前按 schema 自检） |
| `init_book.py` | 建骨架、渲染 book.yaml、四本账、指纹、mermaid 配置、混合 genre preset |
| `state.py` | 状态机、多作者加锁/归属/冲突、续跑报告、`--calibrate` 指纹校准、漂移检测、repair 快照与回滚 |
| `dep_brief.py` | 生成 `dep-brief/chNN.md`（只读上游合同与章纲边界，缺合同即阻断） |
| `assemble.py` | 自包含装配 `final/`：前言/附录/结语/README/LICENSE、assets 复制与路径重写、`versions.lock` 生成 |
| `schema_check.py` | 按 `schemas/*.json` 校验 book/state/dag/contract；缺 jsonschema 时降级为 info |
| `verify.py` | 一条命令跑完 plan→check→dep_brief→assemble→产物扫描→状态漂移，供 CI |
| `tests/run_tests.py` | 闸门回归台：6 个基线 + 9 个注入用例 |

### check.py 闸门

| 组 | 已落地的检查 |
| --- | --- |
| 结构 S01–S22 + P00–P05 + P11 | 字数、骨架齐全/顺序/乱序、小节数、每节支撑物、导图、标注白名单与上限、禁用词（含人称；带省略号的短语转正则）、半成品标记、规定人称、句长/段长、**连续超限段**、信息密度、difficulty 一致、阅读路径、未知 H2、难度曲线、**标注是否堆在章末**、**文风指纹比对**；前言五项；书级参数覆盖留痕 |
| 引用 R01–R07 + G01–G03 | 图产物、src 路径、前向依赖、越级引用、声明使用一致、import 图 ⊆ 章依赖图；图许可、capstone 快照（无 git 时显式标 skipped） |
| 代码 C01–C06 | 代码块行数、密钥扫描、README 运行命令、版本锁主版本（含"有 src 无 lock"提示）、示例数据 SEED、**合同契约校验** |
| 事实 F01–F03 | 断言数字登记（**带单位或同段断言词**，汉字数字归一化、单位不互顶、按显示精度记账、逐条全报）、claim 须有 source+date、**source 中的路径须存在** |
| 一致性 X01–X08 | 术语登记（含别名与半角括号）、承诺入账（触发词**或「下一章」段前向引用**，按条数比对）、ladder 单调、**跨章连续重复**、术语多定义、promises open 阻断、别名上限、**别名撞车** |

依赖账本的组在 `.book/` 缺失或为空时优雅跳过，并在输出标注（X00）。
全会级 Finding 输出带归属章号。

### genre 约束的机器消费

`check.py` 已消费 genre yaml 的 `max_lines / max_chars / count_range / max_items /
require_table / require_columns / require_parts / require_levels / require_scoring /
require_triad`，以及 `_core.yaml` 的 `person.forbidden / anti_pattern_keywords /
person.required / typography.max_paragraph_chars / consecutive_over_limit /
annotation.must_be_inline / glossary.max_aliases / forbid_synonym_swap`。
四套 genre 各有最小合规样本，`tests/fixture-ledger/` 是账本非空的通过样本。

### §16 增量的落地情况

- 已落地：信息密度(16.1)、难度曲线与首章约束(16.2)、能力阶梯单调(16.3)、
  承诺账本 open 阻断(16.4)、阅读路径标注与占比(16.5)、图许可(16.6)、
  版本锁主版本校验(16.7)、capstone 快照存在性(16.8)、示例数据 SEED(16.9)。
- **文风指纹(7.2)现已闭环**：`state.py --calibrate` 用已完成章的中位数定基准、
  1.5 倍离散度作带宽；`check.py` S20 逐章比对。未校准只给 info，校准后两项以上
  偏离才算 warn（单项多为"这章本来图少"的正常起伏）。
- 断言词表：内置 28 词（含错误率/可用性/拒答率/点击率/覆盖率等），领域词由
  `book.yaml` 追加。**事实闸门是护栏不是审计**：它拦无心之失，拦不住刻意换写法；
  真正的把关仍是每章抽一个数字回源。
- 图渲染本身（mmdc 调用）不在脚本内，按 §9 的命令手工或 CI 执行。

### 多作者与状态

`state.py` 用 `.book/state.lock`（O_CREAT|O_EXCL）串行化读改写，每次写 `rev += 1`；
`--claim` 标记归属，越权写入被拒，`--expect-rev` 做乐观并发校验；
`--set chNN repair` 自动快照到 `.book/history/chNN/attempt-N.md`，`--rollback` 回滚。
`--report` 会做**账本-磁盘漂移检测**：正文已存在但状态仍是 pending/ready/blocked 时报警，
避免续跑把写完的章重写一遍。

### 装配

`assemble.py` 把 `assets/` 复制进 `final/`，正文 `../assets/` 重写为 `assets/`，
产出 README、前言终稿、附录 A–E、结语、LICENSE；有 `src/` 而无 `versions.lock` 时
按真实 import 生成一份。装配后扫描 `final/` 内图片路径，残留 `../` 或不可达即报错，
**中英文占位（`（待补` / `TODO` / `FIXME` / `此处省略`）一律报错**——
"留占位不等于通过"这条纪律也适用于装配器自己的产物。
README 的运行命令从 `src/` 里真实存在 `__main__` 的模块推导；无代码的书不输出"怎么跑代码"。

### 仍未做（明确边界）

- v2：读者模拟通读。
- 「过密」类上限检查（连续小节全是表格、代码占比过高）未做：这类信号误报率高，
  没有第二本真书的分布做参照，先不加，避免噪音疲劳。
- 单一 genre 样本量仍为 1（四本书各一本）。genre yaml 里的阈值（如面试本
  一句话 ≤30 字）本质是"为唯一样本调的"，第二本书产出后应回归重定。
- 8 章规模冒烟见 `tests/fixture-smoke8/`：5 波、0 error；因同模板复用产生的
  28 条 X04 告警是刻意保留的（新的连续重复算法报的是"≥60 字连续"），
  用来验证重复检测在规模上有效。


### 本轮修正记录

- `schema`：混合 genre 含 `project` 时此前只匹配纯字符串，漏检数组形式；已补 `contains` 规则。
- `schema`：测试样本章数/字数下限从 5/1000 放宽到 2/200，真实书稿建议不变。
- `check.py`：H2 骨架段的 body 此前延伸到下一个 H2，把其后 H3 正文也算进"开场 ≤10 行"；已修。
- `plan.py`：此前只打印 DAG，不落盘 `.book/dag.json` / `waves.json`（§13 要求）；已补。
- `init_book.py`：此前漏生成 `style-fingerprint.json`、未带 mermaid 配置；已补。
- `tests/`：四套 genre 样本齐全；`fixture/ch02` 保留为反例。

