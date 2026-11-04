# aia-handbook 操作手册（最佳实践）

> 这份手册回答三个问题：**怎么用这个 SKILL、怎么用好它、不同场景下怎么用它。**
> 阅读路径：
> - 第一次用 → 按 §1–§4 顺序读，§4 是你每天的枕边书
> - 已经在写书 → 直接查 §9（场景手册）和 §10（报错处理）
> - 想榨干它的效力 → §12 的十二条法则
>
> 配套文件：`README.md`（项目速览）、`SKILL.md`（agent 编排路由）、
> `SPEC.md`（设计规格与错误码全表）、`references/01–07`（各阶段细则）。

---

## 1. 一分钟理解这套流水线

**核心模型一句话：章是节点，依赖是边，拓扑序给波次，同波并行，跨波只传合同。**

它不是"让 agent 一章章往下写"，而是把写书变成一次**可调度的构建**：

- **章纲**（`04-chapter-plans/chNN.md`）在 front-matter 里声明 `requires` / `references`，
  `plan.py` 把它编译成 DAG，切出波次。`requires` 只允许指向更小的章号——
  环在结构上不可能出现。
- **合同**（`.book/contracts/chNN.json`）是跨波传递的唯一载体：`defines`（我定义了什么）、
  `provides`（我提供了什么代码签名）、`assumes`（我假设读者已会什么）、`hook`（给下游的钩子）。
  下游写手读 `dep-brief/chNN.md` 摘要包，**不读上游全文**。
- **质量**由三层兜底，缺一不可：
  1. **冻结的宪法**（`00`–`03` 文件，批量写作前锁死，冻结写哈希）
  2. **可执行的闸门**（`check.py` 约 60 个检查码，不靠 agent 自评）
  3. **四本账**（术语 / 事实 / 承诺 / 能力阶梯，跨章一致性由数据保证，不靠记忆）

**一条贯穿始终的原则：所有"没查"都必须显式标注，绝不报成"通过"。**
账本缺失 → X00 标注跳过；非 Python 栈 → C00 标注跳过；草案合同 → dep-brief 里标 `[draft]`。
看到 info 级"已跳过"不是噪音，是系统在对你诚实。

---

## 2. 用不用：适用判断

| 用 | 别用 |
| --- | --- |
| 8 章以上的技术书、手册、系列教程 | 单篇文章、博客（少于 6 章直接写，开销不划算） |
| 已有零散笔记，要组织成体系 | 文档翻译、代码注释 |
| 需要"读完能动手做出来"的内容 | 纯营销文案、产品说明 |

**少于 6 章不要用这套流程。** 立项、蓝图、宪法、章纲四道前置工序的固定成本摊不到 6 章上。

三个前置判断，任一答不上来就先别开项目：

1. **读者是谁**——能说出一个具体的人（职业、当前能力、痛点），不是"有一定基础的开发者"。
2. **读完能做什么**——一个可验收的动作（"能给自己的 RAG 应用搭评测集"），
   不是"理解 X""掌握 X"。写不出可验收的目标，章纲的 `deliverable` 字段就填不出来。
3. **章节之间有没有真依赖**——如果 10 章完全互相独立，DAG 退化成一条平行线，
   这套系统的调度价值就只剩闸门，可以考虑更轻的方案。

---

## 3. 快速开始：从零到 verify 全绿

```bash
# 0. 建书（渲染 book.yaml、建目录、初始化四本账与 progress.md）
python scripts/init_book.py --dest ../my-book --title "AI 应用评测入门" \
    --genre practical --spine capstone --spine-name "客服工单问答助手" \
    --chapters 10 --words 4500,6000

# 混合 genre 用预设（也可以直接写 --genre principle,practical）
python scripts/init_book.py --dest ../my-book --title "..." --preset principle-practical

# 1. 写完 00–02 和章纲后：编依赖图（同时跑 G4 章纲闸门）
python scripts/plan.py --book ../my-book

# 2. 写作期每写完一章：单章过闸
python scripts/check.py --book ../my-book --chapter ch03
python scripts/state.py --book ../my-book --set ch03 done   # 内部自动再跑一次单章闸门

# 3. 全书完成：一条命令跑全链路（plan → check → dep_brief → assemble → 产物扫描 → state）
python scripts/verify.py --book ../my-book
python scripts/verify.py --book ../my-book --exec   # 连 src 示例一起实跑（C07）
```

依赖：`pyyaml` 必需；`jsonschema` 缺失时 schema 校验降级为 info；
渲染图需要 node（`npx -y @mermaid-js/mermaid-cli`）。

**最小成功路径**：`init_book` → 填 book.yaml → 写 00-positioning → 写 01/02 →
写 03 + glossary → 写全部章纲 → `plan.py` 绿 → 按波次写章（每章 check → done）→
`stitch.py` 缝合 → `verify.py` 绿 → `final/` 就是成书。

---

## 4. 七阶段操作详解

每阶段给出：目标 / 操作步骤 / 闸门 / 最常见死法 / **完成标准（DoD）**。
**只读当前阶段的 reference 文件**——一次读完所有 references 会占满上下文，反而写不好。

### 阶段 0 · 立项（读 `references/01-intake.md`）

- **产出**：`book.yaml` + `00-positioning.md`
- **操作**：用 `init_book.py` 建骨架后，逐字段填 `book.yaml`（见 §7）；写定位文档，
  核心是两句话——给谁看、读完能做什么。
- **闸门**：G1 定位确认（人工确认点）。
- **死法**：读者画像写成"有一定基础的开发者"；前置知识（`audience.prerequisite`）
  写太多——写进前置的内容正文不再解释，写多了等于把读者挡在门外。
- **DoD**：能用一句话说出"读者读完第 N 章后能做出 X"，且 X 可被验收。

### 阶段 1 · 蓝图（读 `references/02-blueprint.md`）

- **产出**：`01-outline.md`（篇级大纲，3–9 篇）+ `02-toc.md`（章级目录）+ `.book/dag.json`
- **操作**：先分篇（篇是**读者问题维度**，不是技术点维度，更不是 genre 维度），
  再排章。capstone 书给每章标 `project_stage`，`plan.py` 会自动产出
  `.book/project-curve.json` 项目推进曲线；章纲没写 `project_stage` 时脚本会显式打印"已跳过"。
- **闸门**：G2 目录锁定（人工确认点）。
- **死法**：按技术点排章不管依赖，关键路径拉到 20 波——章序一错，
  后面所有"上一章我们做过"全部返工。
- **DoD**：`plan.py` 跑通无 problems；关键路径长度可接受（10 章书 4–6 波是健康区间）。

### 阶段 2 · 宪法（读 `references/03-constitution.md` + `genres/_core.md` + `genres/<genre>.md`）

- **产出**：`03-style-guide.md`（≤200 行，**只写与 genre 的差异**）+ `glossary.json` 初值
- **操作**：genre 已经给了默认宪法（`_core` + 体裁层），你的 style-guide 只写"这本书不一样
  的地方"。写完立刻冻结：

  ```bash
  python scripts/state.py --book ../my-book --freeze constitution
  python scripts/state.py --book ../my-book --freeze positioning   # 建议 00–03 全冻
  ```

  冻结会写哈希进 `state.json`；之后文件被改，`--report` 的 drift 检测会发现。
- **闸门**：G3 宪法冻结。
- **死法**：把宪法写成 500 行完整规范，写手根本读不完——宪法的读者是写作 agent，
  它的上下文比你的耐心贵。
- **DoD**：`03-style-guide.md` ≤200 行且每条都是"与 genre 的差异"；
  `--freeze-report` 显示全部已冻结、哈希一致。

### 阶段 3 · 章纲（读 `references/04-chapter-plan.md`）

**这是全流程错误代价最大的环节，也是"写一章发一章"死法的唯一防线。**

- **产出**：`04-chapter-plans/chNN.md` × N，**一次写全**
- **操作**：每章纲 front-matter 必填 genre 声明的 `plan_required_fields`
  （通常含 `chapter` / `title` / `deliverable` / `requires` / `references` /
  `target_words` / `difficulty`，capstone 书加 `project_stage`）；
  正文必须写「## 与相邻章的边界」段（下游 dep-brief 的边界依据从这里来）。
- **闸门**：**G4 章纲闸门（机器闸）**——`plan.py` 与 `check.py` 共享同一份校验口径：
  章纲数 == `scale.chapters`、必填字段齐全、字段类型/取值合法（difficulty 1–5、
  target_words 正整数）、边界段存在且非空。缺 front-matter 的章纲不再被静默跳过，
  会直接报出来。
- **死法**：写一章发一章，依赖边错在下游已开工之后。
- **DoD**：`plan.py` 退出码 0，`dag.json` / `waves.json` / `writing-waves.json` 落盘。

### 阶段 4 · 定标（并入第一波，无独立阶段）

**没有独立的"样章阶段"。** 根节点（无上游的 1–3 章）在拓扑序上必须最先写，
写完自动承担定标职责：

```bash
python scripts/state.py --book ../my-book --calibrate   # 抽取文风指纹
```

校准后 S20 文风指纹闸门才有意义（此前它无基准可查）。第一波章节会被后续所有波次
当作"这本书的写法"参照，所以**第一波值得投入全书 30% 的打磨时间**。

### 阶段 5 · 批量写作（读 `references/05-writing.md` + `03-style-guide.md` + 本章纲 + 上游合同）

**三条铁律**：

1. **顺序是 代码 → 图 → 正文，不能反。** 反过来你会先写出"运行结果是 0.87"，
   再去找能跑出 0.87 的代码——这就是"编造运行输出"的死法。
2. **不读上游全文。** 你拿的是 `dep-brief/chNN.md`（合同与签名）。
   读全文会被带进别人的叙事节奏，还会撞 X04 重复闸门。
3. **章纲有问题就停、报告、不要自己改。** 章纲是全局调度的输入；你改一章的边界，
   邻章会重复、依赖图会失真。报告三行：章节 / 问题 / 影响 + 建议，由上游决定改章纲还是改书。

**每章的操作循环**：

```bash
python scripts/dep_brief.py --book ../my-book --chapter ch05   # 拿上游摘要包
# …写代码、跑代码、画图、写正文（章节文件开头必须写 front-matter，至少含
#   difficulty 且与章纲一致——S14 依赖它）…
python scripts/check.py --book ../my-book --chapter ch05       # 单章过闸
# …修到 error=0…
# 产出 .book/contracts/ch05.json（defines / provides / assumes / hook）
python scripts/state.py --book ../my-book --set ch05 done      # 内部自动复跑单章闸门
```

- 合同写不清楚，下游一定会理解错——**写完章立刻产合同**，它是下游唯一的信息源。
- `--set done` 有 error 会被拒绝；`--force` 必须配 `--error "原因"` 且留痕在 state.json。
  不要用 --force 当习惯，它是给"闸门误报待修"留的逃生门。
- 状态迁移有合法性校验（`pending → ready → writing → checking → merging → done`，
  另有 `repair` / `failed`），非法跳转会被拒，同样可 `--force` 留痕。

### 阶段 6A · 波次缝合（读 `references/06-review.md`）

每波写完做缝合，**不要攒到全书最后**：

```bash
python scripts/stitch.py --book ../my-book --wave 3            # 生成缝合清单骨架
python scripts/stitch.py --book ../my-book --wave 3 --out patches/wave-3.md
python scripts/stitch.py --budget --before chapters/ch08.md --after /tmp/ch08.new.md
```

- 清单骨架由 `check.py --json` 的 findings 自动转换——**缝合清单不是从空白开始写**。
- **20% 改动预算有度量**：缝合改动超过单章 20% 直接打回重写。
  缝合退化成重写是这类流水线最常见的死法，预算是唯一防线。
- 缝合 agent 只动术语、衔接、重复；**事实必须回源到 claims.jsonl**，不许在缝合时新编数字。
- 草案合同与终稿合同的签名比对：`dep_brief.py --check-signatures`（C08）。
  签名不符意味着要动代码而不是动文字。

### 阶段 6B · 统稿装配（读 `references/07-assembly.md`）

```bash
python scripts/assemble.py --book ../my-book   # 产出自包含 final/
```

- 装配是**硬阻断**：`promises.jsonl` 还有 `status: open` 就拒绝产出 final/
  （结清为 `kept`，或标 `dropped` 并写 `reason`）。
- 装配自动完成：承诺账 → 附录 E、术语账 → 附录 A、claims → 附录 B 参考文献、
  `src/` import 解析 → `versions.lock`、FAQ 按骨架段 id 收集（pitfalls / mistakes /
  risks / boundary / retro）、mmd 图源渲染为 SVG。
- 前言/结语的 P01–P05 是**关键词存在性提示**（warn 级），P06 是 info 级一致性提示——
  它们不是硬闸门，**别把"P01 过了"当"前言写好了"**，前言仍然要人读一遍。
- 章序调过之后必查：X10（术语首现章）、X02/X06（承诺指向）、ladder 阶梯——
  章序是全书最贵的全局变量。

**G7 全书验收**：`verify.py --strict`（warn 也算失败）+ `--exec`（实跑代码示例）。
交付前用这个组合，平时迭代用默认即可。

---

## 5. 四本账的维护纪律

| 账本 | 记什么 | 何时记 | 谁消费 |
| --- | --- | --- | --- |
| `.book/glossary.json` | 术语 zh / en / def / first_chapter / aliases | 宪法阶段定初值；写作中新增术语**当场**登记 | X01 X07 X08 X09 X10、附录 A |
| `.book/claims.jsonl` | 每个数字 + source + date + `scope`（口径） | 正文写进任何数字**之前** | F01 F02 F03 F04、附录 B |
| `.book/promises.jsonl` | "后文会讲"的空头支票，状态 `open / kept / dropped` | 写到前向引用时登记（或 `check.py --suggest` 起草稿）；兑现时结清 | X02 X06、装配阻断、附录 E |
| `.book/ladder.jsonl` | 每章 before/after 的能力阶梯 | 每章写完 | X03、结语 |

三条纪律（违反任一，账本就从资产变成负债）：

1. **没有出处的数字不许出现在正文。** 断言词表（`claims.assertion_words`，
   按书补充领域词）会驱动事实闸门识别"这句话里有数字"；识别出的数字必须在
   claims 里找到容差匹配（`tolerance` 默认 0.005，按显示精度记账）。
2. **全书同一概念只能有一个名字。** 别名（aliases）可以登记，但只作为读者的搜索入口；
   X09 会发现"本章用了别名却一次没用正名"的行文并告警。
3. **死账要清。** F04 查"登记了却从没在正文出现"的死 claim，X10 查"登记的首现章
   与全书正文对不上"的腐化术语——附录 B/A 直接消费账本，账腐化 = 附录说谎。

**维护账本的回报在装配阶段一次兑现**：没有 glossary.json，术语表要手工整理两天；
有了它，附录 A 只是一次格式转换。

---

## 6. genre 选择、混合与扩展

### 6.1 四种体裁怎么选

| genre | 骨架（H2 序列） | 章字数 | 一句话判断 |
| --- | --- | --- | --- |
| `practical` | 章首导图 → 场景开场 → 正文 → 小结 → 练习 → 自查清单 → 常见坑 | 5000–7000 | 每章交付一个能力点的动手手册 |
| `principle` | 概念地图 → 反直觉开场 → 正文 → 权衡表 → 失效边界 → 延伸阅读 | 6000–8000 | 讲机制、权衡与失效条件的原理书 |
| `project` | 阶段全景 → 现场开场 → 正文 → 阶段交付物 → 复盘 → 风险登记 | 4500–6500 | 交付驱动；**强制 `spine: capstone`**（P12 硬闸） |
| `interview` | 考点地图 → 真实提问 → 分层解析 → 追问链 → 高频错误 → 自测 | 3000–5000 | 考点驱动、各章独立；**spine_constraint: none** |

骨架段名有**别名表**（check.py 按别名匹配 H2）：自创标题 = 直接判 S02 缺段。
「开场白」代替不了「场景开场」。拿不准某段的合法标题，查 `genres/<genre>.yaml`
的 `skeleton` 段。

**选择决策**：

- 读者的问题是"怎么做" → practical；"为什么" → principle；"给我做出来" → project；
  "怎么考" → interview。
- 选不出来时问自己：这本书的章节能不能用同一个 H2 序列写完？能 → 单 genre；
  不能 → 多半是你的书其实是两本，或者该用"篇"来分层（见 6.3）。

### 6.2 混合 genre：可以，最多 3 个，"主 + 副"

```yaml
genre: [principle, practical]   # 第一个是主类型
```

- **排他维度只有两项：章节骨架和 spine，主类型说了算。** 副类型的 spine_constraint
  不生效时会收到 P12 的 info 显式说明（不静默调和）。
- 其余全部可叠加：标注 / 反模式 / 断言词取并集，字数取交集，图表下限与信息密度取高，
  代码要求取严，章纲必填字段取并集。
- 官方预设（`--preset`）：`project-practical`、`principle-practical`、`interview-principle`。

### 6.3 三条必须知道的边界

1. **骨架是全书级的，不是每章级的。** 做不到"前 5 章原理骨架、后 5 章实战骨架"——
   S16 会把未命中别名表的 H2 判 error。想要"前原理后实战"：选主类型骨架（如
   practical），把副体裁内容放进该骨架允许的 **H3 固定小节**（如每章末尾的
   「原理补注」）；**篇**（`01-outline.md`）用来分读者问题维度。
   不要在 genre 列表上反复试错，也不要试图让 S16 放行另一套 H2。
2. **把 interview 放副类型几乎没收益。** 它的价值 90% 在骨架（分层答案 + 追问链），
   而骨架是排他的；当副类型只并进来几个标注词。想要面试维度，用 H3 固定小节或做成附录。
3. **字数交集可能倒挂。** 已知缺口：`principle`(6000–8000) ∩ `interview`(3000–5000)
   交集为空时返回倒挂区间而不报错。**混合时务必在 book.yaml 显式写
   `scale.words_per_chapter`。**

### 6.4 新增第五种体裁

不用改 `check.py`：可用体裁由 `genres/*.yaml` **自动发现**（schema_check 动态校验，
book.yaml 写未知 genre 会直接被拒）。最小步骤（复制最接近的现有体裁改，
别从空文件开始）见 `genres/README.md`，核心是两份文件：

- `genres/<name>.yaml`：骨架 / 阈值 / 章纲必填字段 / 曲线 / 标注白名单
- `genres/<name>.md`：段落怎么写、标注含义表、反模式

yaml 缺关键字段不会被闸门发现（等于空壳体裁），以 `genres/README.md` 的必填清单为准。

### 6.5 兼容边界（诚实清单）

| 边界 | 现状 | 怎么绕 |
| --- | --- | --- |
| 语言 | `lang` 只支持 `zh-CN` / `zh-TW`；字数、句读、禁用词、断言词全中文特化 | 英文书会直接报 B01；有真实需求再做语种分层 |
| 代码栈 | R07 import 图、C04 版本锁按 Python 特化 | `book.yaml stack.language` 声明 go/node/rust 后这些检查显式跳过并标 C00，不会静默不查 |
| 外围文本 | 附录 D 用途说明、附录 E FAQ 段曾按 RAG/practical 硬编码 | 已下沉：`tool_purposes` 在 book.yaml 覆盖；FAQ 按 genre 骨架 id 收集 |
| 闸门强度 | `gates: hard` 默认；`soft` 只出报告（error 降级 warn，退出码不带 1） | soft 用于评审/试跑；**不要拿 soft 的结果当验收通过** |

---

## 7. book.yaml 配置参考

原则：**genre 给默认值，这里只写差异。写进来的每个字段都要有理由。**

| 字段 | 说明 | 填不好会怎样 |
| --- | --- | --- |
| `title` / `author` / `license` / `updated` | 版本声明附录与版权页从这里取 | 附录出现"待填" |
| `genre` | 单类型或 `[主, 副]`（≤3） | 未知 genre 被 schema/动态校验直接拒 |
| `lang` | `zh-CN` / `zh-TW`（B01 硬闸） | 写 `en` 直接报 B01 |
| `audience.who / level / prerequisite` | 读者画像与前置知识 | 前置写多 = 把读者挡在门外；P06 会拿 who 的原串核对前言 |
| `spine` / `spine_name` | `capstone`（贯穿项目，每章推进）/ `running-example`（例子复用）/ `none` | genre 含 project 而 spine≠capstone → P12 error |
| `scale.chapters` | 章数 | 与章纲文件数不符 → G4 error |
| `scale.words_per_chapter` | `[下限, 上限]`，闸门允许 0.75×下限 ~ 1.25×上限；中文按汉字计 | 混合 genre 不写这个可能撞上倒挂区间（§6.3-3） |
| `deliverables` | `[markdown, code, figures]` 等 | 决定交付物类闸门是否启用 |
| `gates` | `hard`（默认，error 阻断）/ `soft`（只出报告） | soft 的"全绿"不等于验收通过 |
| `concurrency` | 并行写手上限 | 写作波次按它切组 |
| `output.target / prepare_print` | `repo` 等；prepare_print=true 预留出版资产但不出 PDF | — |
| `figure.*` | renderer `mmdc`、format `svg`、**`htmlLabels: false`**（否则 Gitee 等渲染成白图）、theme、width | 正文不嵌 Mermaid 源码；图源在 figures/，产物在 assets/ |
| `limits.*` | `max_core_terms` / `info_density_min`（每千汉字最少可操作单元数，防凑字数）/ `difficulty_max_run`（连续高难度上限）/ `code_block_max_lines` / `snapshot_every`（capstone 每 N 章打快照 tag） | 阈值本质是经验值，为一本书调过；第二本书出来前别乱改 |
| `claims.assertion_words / tolerance` | 领域断言词表（与内置表合并）、数字容差 | 断言词太少 → 事实闸门漏识别；太多 → 误报疲劳 |
| `stack.language` | 代码栈；非 `python` 时 R07/C04 显式跳过并标 C00 | 不写或写错 = Python 特化检查对你的 Go 书乱报或漏报 |
| `tool_purposes` | 附录 D 工具箱用途说明，书级覆盖 genre 层 | 换主题不改这里 → 附录 D 说的是别人家的话 |

完整注释模板：`templates/book/book.yaml`；schema：`schemas/book.schema.json`。

---

## 8. 命令完全参考

### check.py —— 闸门执行器

```bash
python scripts/check.py --book <书目录>                  # 全部 5 组闸门（结构/引用/代码/事实/一致性）
python scripts/check.py --book <书目录> --chapter ch03   # 单章模式（不跑全书级闸门）
python scripts/check.py --book <书目录> --gates structure,reference  # 指定组；拼错组名直接报错
python scripts/check.py --book <书目录> --json           # 机器可读（调度器/stitch.py 消费）
python scripts/check.py --book <书目录> --suggest        # 从正文前向引用生成 promises.jsonl 草稿
python scripts/check.py --book <书目录> --exec           # 实跑 src README 命令并比对实测输出（C07）
```

退出码：有 error → 1。`--exec` 是可选闸门：20s 超时、剔除凭证类环境变量、
cwd 限定 `src/`；src README 没声明可执行命令时显式标 skipped。
**事实组与一致性组依赖账本；账本为空时这两组跳过并标 X00，不会把"没查"报成"通过"。**

### plan.py —— DAG 编译器 + G4 章纲闸门

```bash
python scripts/plan.py --book <书目录>            # 编译 DAG + G4 闸门 + 写作波次 + 项目曲线
python scripts/plan.py --book <书目录> --json     # 机器可读（verify.py 消费）
```

落盘：`.book/dag.json`、`.book/waves.json`（阅读波次）、`.book/writing-waves.json`
（写作波次，见 §9-K）、`.book/project-curve.json`（capstone）。
G4 不合格（章纲缺字段 / 章数不符 / 无 front-matter）→ 退出码 1。

### dep_brief.py —— 上游摘要包

```bash
python scripts/dep_brief.py --book ../my-book --chapter ch05   # 生成/查看 ch05 的上游摘要
python scripts/dep_brief.py --book ../my-book                  # 全书生成；上游未写完的标 skipped（不再全局失败）
python scripts/dep_brief.py --book ../my-book --strict         # 只认终稿合同（拒收草案）
python scripts/dep_brief.py --book ../my-book --check-signatures  # 草案 vs 终稿签名比对（C08）
```

摘要包只有合同与签名，**没有上游全文**——这是设计，不是缺失。
章纲 `provides` 的签名可作草案级合同（标 `[draft]`），写作波次靠它先行。

### state.py —— 状态机与协作

```bash
python scripts/state.py --book <书目录> --init           # 初始化章节状态
python scripts/state.py --book <书目录> --report         # 下一步建议 + 账本磁盘漂移检测
python scripts/state.py --book <书目录> --report --basis writing   # 按写作波次判 ready
python scripts/state.py --book <书目录> --claim ch03 --owner agent-a   # 多作者认领（加锁）
python scripts/state.py --book <书目录> --set ch03 writing
python scripts/state.py --book <书目录> --set ch03 done  # 自动跑单章闸门，error 即拒
python scripts/state.py --book <书目录> --set ch03 done --force --error "S20 基准误报，已人工复核"
python scripts/state.py --book <书目录> --rollback ch03  # 回滚到上一状态
python scripts/state.py --book <书目录> --calibrate      # 第一波后校准文风指纹
python scripts/state.py --book <书目录> --phase 3-chapter-plan       # 推进阶段
python scripts/state.py --book <书目录> --freeze constitution        # 冻结（写哈希）
python scripts/state.py --book <书目录> --unfreeze constitution --reason "改了两条定义"  # 解冻：记原因 + 列出需重跑闸门的已完稿章节
python scripts/state.py --book <书目录> --freeze-report  # 冻结状态与哈希一致性
```

状态机：`pending → ready → writing → checking → merging → done`，旁路 `repair` / `failed`。
非法迁移被拒（`--force` 留痕可越过）。解冻记录自动追加到 `progress.md`。

### stitch.py —— 波次缝合

```bash
python scripts/stitch.py --book <书目录> --wave 3                 # 从 check --json 生成缝合清单骨架
python scripts/stitch.py --book <书目录> --wave 3 --out patches/wave-3.md
python scripts/stitch.py --book <书目录> --json                   # 机器可读
python scripts/stitch.py --budget --before chapters/ch08.md --after /tmp/ch08.new.md  # 改动预算度量（默认 20%）
python scripts/stitch.py --budget --before A --after B --limit 15 # 自定义预算
```

### assemble.py / verify.py / 测试台

```bash
python scripts/assemble.py --book <书目录>       # 装配自包含 final/（open 承诺硬阻断）
python scripts/verify.py --book <书目录>         # plan → check → dep_brief → assemble → 产物扫描 → state
python scripts/verify.py --book <书目录> --strict   # warn 也算失败
python scripts/verify.py --book <书目录> --exec     # 连 src 示例一起实跑
python scripts/verify.py --self-test             # 闸门回归台
python tests/run_tests.py                        # 6 基线 + 29 注入（交付级验证）
```

verify.py 任何一步失败都继续跑完（否则只能看到一个错），最后按退出码聚合。

---

## 9. 场景手册

### 场景 A：单人写第一本书（推荐路径）

1. 先用 §2 的三个前置判断卡住自己半天——**立项阶段省的小时，会在章纲阶段以天计还回来**。
2. `init_book.py` 建骨架；填 book.yaml 时**只填有理由的字段**，其余留给 genre 默认。
3. 00–03 一次写完，立刻 `--freeze` 全部四个文件。
4. 章纲一次写全，`plan.py` 绿之前不动正文一个字。
5. 根节点章节（第一波）当样章打磨：写完 `--calibrate`。
6. 之后每章严格走 §4-阶段 5 的循环；每波结束跑 `stitch.py`。
7. 每周跑一次 `verify.py`（不带 --strict），把 warn 当 backlog 清。
8. 交付前：`verify.py --strict --exec`。

### 场景 B：多 agent / 多作者并行

- `state.py --claim chNN --owner <名字>` 先认领再动手；`--report` 看全局。
- 同波章节并行写是安全的：**跨波只传合同，同波之间无依赖边**（有边就不会同波）。
- 并行期约定：账本文件（glossary/claims/promises/ladder）的写入在**章末统一合并**，
  写作中各自记在章尾草稿区——四本账是共享可变状态，并行直写必然冲突。
- 每章 `--set done` 自带闸门，不存在"他先交了烂稿堵我下游"——done 有 error 置不上。

### 场景 C：长周期项目（跨天/跨周续跑）

- 每天开工：`state.py --report`（含账本磁盘漂移检测）+ `progress.md` 看流水。
- 每天收工：把进行中的章置 `writing`/`checking`，别留在脑子里。
- 换机器/换会话：`--report` 的 next steps 就是续跑入口；不需要回忆"上次写到哪"。
- 冻结文件被动过：`--report` 的 drift 与 `--freeze-report` 会指出来——
  先确认是无意改动（恢复）还是有意演进（走场景 H 流程）。

### 场景 D：已有半成品书稿迁入

1. 别急着套闸门——先写 book.yaml 与 00–02，把现有章节**映射**成章纲
   （每章补 front-matter 与「与相邻章的边界」）。
2. 用 `gates: soft` 跑第一轮全量 check，拿到完整的差距清单（soft 只出报告不阻断）。
3. 按差距清单的**组**决定迁移顺序：先结构（S 组，骨架段名对齐别名表），
   再账本（补 glossary/claims），最后一致性（X 组）。
4. 差距清零后切回 `gates: hard`，从此按正常流程走。

### 场景 E：capstone 项目书（spine = capstone）

- 章纲必须写 `project_stage`；`plan.py` 产出 project-curve.json 后要**人眼看一眼**：
  连续 ≥3 章"原地不动"会触发 S24 提示——读者看不到推进感是 capstone 书的死法。
- `limits.snapshot_every`（默认 5）控制每几章打一个可运行快照 tag，
  读者可从任意节点开始——**快照能不能跑通用 `--exec` 验证**。
- import 图 ⊆ 章依赖图（R07）：ch08 的代码不许 import ch09 的模块；
  跨章复用走 rule of two（出现两次就下沉公共层）。
- 建议 `--preset project-practical`：project 定骨架与 spine，practical 补练习与常见坑段。

### 场景 F：interview 面试书

- 各章独立 → DAG 接近平行，调度价值主要在闸门与账本。
- `spine: none`（interview 的 spine_constraint，P12 会执行）；difficulty_curve 为 flat——
  章间难度跳跃会收到 S19 提示。
- 字数口径 3000–5000，别拿 practical 的手感写。
- 高价值账本用法：claims 记"这个考点在各家公司的出现频率"（有出处才许写）。

### 场景 G：非 Python 技术栈

- `book.yaml stack.language: go`（或 node/rust/…）：R07/C04 等 Python 特化检查
  显式跳过并标 C00。
- **跳过 ≠ 豁免**：版本锁定与依赖卫生要靠书自己的宪法补一条（写进 03-style-guide.md），
  并在 claims 账本里记关键版本号。
- `--exec` 与语言无关（跑的是 src README 声明的命令），Go 书照常用。

### 场景 H：修改冻结文件（规范演进）

唯一合法流程：

```bash
python scripts/state.py --book ../my-book --unfreeze constitution --reason "术语表改了两条定义"
# …修改 03-style-guide.md…
python scripts/state.py --book ../my-book --freeze constitution
python scripts/check.py --book ../my-book --chapter chNN   # 对 --unfreeze 列出的每章重跑
```

- `--unfreeze` 会**自动列出需要重跑闸门的已完稿章节**——这个清单就是返工范围，
  别凭印象圈定。
- 硬规则第 4 条的第三小步（重跑已完稿章节闸门）最容易被跳过，
  也是"改了规范但书没跟上"的根源。
- 解冻记录自动追加到 `progress.md`，审计可追溯。

### 场景 I：中途要改章纲（结构性调整）

1. 先改章纲，再动正文——**顺序不能反**。
2. 涉及依赖边变化：`plan.py` 重编，看波次是否重排；受影响章节
  `state.py --set chNN repair`（或 `--rollback`）。
3. 章序调整（插入/删除/换序）后必查三样：X10（术语首现章）、
   X02/X06（承诺指向）、ladder 阶梯顺序——章序是全书最贵的全局变量。
4. 章纲改完重跑 G4：`plan.py` 绿 = 调度输入重新可信。

### 场景 J：闸门报错的处理套路

1. **先看级别与组**：error 阻断、warn 提示、info 告知（含"已跳过"标注）。
2. **每个 finding 都带修复建议**（最后一段），先按建议修；不认的时候去
   `SPEC.md` §18 查该码的判定逻辑，别猜。
3. **同类错误 ≥3 处 → 不是写作问题，是上游问题**：同一波多章 X01 → 宪法术语表没定够；
   多章 S02 → 章纲骨架段名没对齐别名表；多章 F01 → claims 记账流程没人遵守。
   回到阶段 2/3 修源头，不要在正文里逐个糊。
4. **repair 两次仍不过 → 停**。这是章纲的问题，不是写手的问题（见 §11）。
5. 确认是闸门误报：`--force --error "原因"` 留痕越过，并把案例补进
   `tests/`（注入用例的形式），让误报修掉后有回归保护。

### 场景 K：用写作波次压周期（SPEC §6.1）

阅读波次（`waves.json`）要求上游全部 `done` 才 ready，是**验收序**；
写作波次（`writing-waves.json`）只要求**上游合同草案先行**，是**派活序**：

```bash
python scripts/plan.py  --book ../my-book                       # 产出 writing-waves.json
python scripts/state.py --book ../my-book --report --basis writing
python scripts/dep_brief.py --book ../my-book --chapter ch08    # 缺终稿合同时自动用章纲 provides 草案（标 [draft]）
```

- 按写作波次派活，实测 10 章书从 8 波压到 4 波。
- 草案合同有代价：终稿合同出来后必须 `dep_brief.py --check-signatures`（C08），
  签名不符说明下游按旧草案写了——**动代码不动文字**。
- 写作波次只改派活，不改验收：闸门与装配永远按阅读波次的口径。
- 验收序仍然严格（dep_brief --strict 只认终稿），所以压波压的是等待，不是质量。

---

## 10. 闸门报错速查（按组）

完整错误码表见 `SPEC.md` §18；这里是"看到后先想什么"。

| 组 | 码段 | 第一眼检查 |
| --- | --- | --- |
| 结构 S | S01 字数 / S02 骨架段 / S14 难度 / S16 H2 白名单 / S19 难度曲线 / S20 文风指纹 / S24 项目推进 | 段标题是否在别名表里（S02/S16 九成是这个）；S20 在第一波前没基准是正常的 |
| 引用 R | R01–R08 图与文件引用 / R07 import 图 / R08 图源比产物新 | 图路径、图源改过没重渲（R08：重跑 mmdc） |
| 代码 C | C02 密钥（正文代码块 + src/）/ C03 README / C04 版本锁 / C06 合同契约 / C07 实测输出 / C08 签名漂移 | C02 先想"这是真密钥还是占位符"（占位符豁免）；C07 先本地复跑该命令 |
| 事实 F | F01 未登记 / F02 缺出处 / F03 容差不匹配 / F04 死 claim | F01/F03：正文数字与账本口径（scope）是否一致；F04：删死账或补回正文 |
| 一致性 X | X01 未登记术语 / X02 承诺未入账 / X03 阶梯倒退 / X04 跨章重复 / X06 承诺未结清 / X08 别名撞车 / X09 别名代正名 / X10 首现章腐化 | X04：正当复用加 `> 复用 ChNN 案例` 声明；X10 多在章序调整后出现 |
| 外围 P | P01–P06 前言结语提示 / P11 / P12 spine 约束 | P01–P06 是提示不是验收；P12：spine 与主类型约束不符要改 book.yaml 或调 genre 顺序 |
| 全局 | B01 语言不支持 / C00 栈检查跳过 / G4 章纲 / X00 账本缺失跳过 | 带"跳过/标注"的 info 不是错误，是诚实声明——但你得知道它没查 |

---

## 11. 该停下来的信号

这些不是"再修一次就好"，是结构层的病，继续打补丁只会更糟：

- 同一章 `repair` 两次仍不过闸门
- 同一波次里三章以上出现同类术语冲突
- 缝合时发现某章 20% 以上的内容需要重写
- 学习目标写成了「理解 X」「掌握 X」——无法验收，也就无法写

出现任一条：回阶段 1 改目录，或阶段 3 改章纲。**流水线的止损纪律比任何单章质量都重要。**

---

## 12. 发挥最大效力的十二条法则

1. **把固定成本花在章纲上。** 章纲是全流程唯一"一次写全"的环节，也是错误代价
   最大的环节；在章纲上多花一天，胜过在缝合上多花一周。
2. **让 verify.py 进 CI。** 闸门的价值与运行频率成正比；`--exec` 至少每周跑一次，
   交付前必跑（它默认不开，记得加参数）。
3. **账本当场记，不要批量补。** 补账的漏记率远高于当场记；claims 的黄金法则是
   "数字进正文之前先进账本"。
4. **info 级输出要读。** "已跳过""草案合同""副类型约束未生效"——系统把诚实写在
   info 里，忽略 info 等于自己关掉一半护栏。
5. **第一波当全书投资。** 根节点章节定文风、定深度、定节奏；S20 指纹、下游合同、
   写手信心全部从这里来。
6. **缝合每波做，预算硬执行。** 攒到全书最后的缝合必然超 20% 预算，
   那时打回=重写一章。
7. **--force 是逃生门不是门。** 每次 --force 都配 --error 留痕，并问自己
   "这是闸门误报还是我想偷懒"；前者补测试，后者回去修。
8. **soft 模式只用做差距评估。** 迁移、评审、试跑用 soft；验收永远 hard + strict。
9. **冲突显式化，别静默调和。** 骨架冲突、genre 冲突、事实冲突一律摆到台面上
   （硬规则第 8 条）——系统会帮你报（P12、X08），你要做的是不捂盖子。
10. **改冻结文件走流程，改章纲先停正文。** 顺序感是这套系统最大的隐性收益。
11. **章序调整后跑 X10/X02/X06/ladder 四连。** 一分钟的事，省的是读者来信。
12. **把误报变成测试。** 每次确认误报后补一个注入用例——闸门会随你的书一起变聪明，
    这是这套系统"越用越准"的唯一机制。

---

## 附录 A · 一本书的目录结构

```
my-book/
├── book.yaml                 唯一契约，genre 给默认值这里只写差异
├── 00-positioning.md         定位（冻结）
├── 01-outline.md             篇级大纲（冻结）
├── 02-toc.md                 章级目录（冻结）
├── 03-style-guide.md         宪法：只写与 genre 的差异，≤200 行（冻结）
├── 04-chapter-plans/chNN.md  章纲（冻结）
├── progress.md               阶段与解冻流水（init_book.py 生成）
├── dep-brief/chNN.md         上游摘要包，自动生成
├── chapters/chNN.md          正文（开头必须带 front-matter）
├── src/chNN/                 可运行代码（含 README 声明运行命令）
├── figures/chNN/*.mmd        图源码
├── assets/chNN/*.svg         图产物
├── .book/                    四本账 + contracts + state.json + 指纹 + dag/waves
└── final/                    装配产物，自包含，不再手改
```

图统一出 SVG（`htmlLabels: false`，否则 Gitee 等阅读器渲染成白图），正文不嵌 Mermaid 源码。

## 附录 B · 八条硬规则（违反即返工）

1. **不许跳过 `check.py`。** "我觉得可以了"不算过闸
2. **不许手画依赖图。** 依赖写在章纲 front-matter，由 `plan.py` 编译
3. **不许编造运行输出。** 跑不出来就写「本章示例未验证」
4. **不许改冻结的文件。** 要改先解冻、记录原因、重跑所有已完稿章节的闸门
5. **不许跨波传全文。** 下游只拿上游的 contract 与代码签名
6. **不许自评合格。** 闸门是脚本，不是判断题
7. **不许为凑字数注水。** 字数不够是内容不够，不是句子太短
8. **不许静默调和冲突。** 一律显式报出并说明采用了谁
