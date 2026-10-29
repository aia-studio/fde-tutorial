# aia-handbook · 技术书生产流水线

一套把"写一本技术书"变成**可调度的构建任务**的 SKILL。

核心思路一句话：**章是节点，依赖是边，拓扑序给波次，同波并行，跨波只传合同。**

不靠"让 agent 一章章往下写"，靠三样东西兜住质量：

1. **冻结的宪法** —— 每本书现场生成，批量写作前锁死
2. **可执行的闸门** —— `scripts/check.py`，不靠 agent 自评
3. **账本** —— 术语 / 事实 / 承诺 / 能力阶梯，跨章一致性由数据保证，不靠记忆

---

## 一、什么时候该用，什么时候不该用

| 用 | 别用 |
| --- | --- |
| 8 章以上的技术书、手册、系列教程 | 单篇文章、博客（少于 6 章直接写，开销不划算） |
| 已有零散笔记，要组织成体系 | 文档翻译、代码注释 |
| 需要"读完能动手做出来"的内容 | 纯营销文案、产品说明 |

**少于 6 章不要用这套流程。** 立项、蓝图、宪法、章纲四道前置工序的固定成本，摊不到 6 章上。

---

## 二、快速开始

```bash
# 0. 建书（会渲染 book.yaml、建目录、初始化四本账）
python scripts/init_book.py --dest ../my-book --title "AI 应用评测入门" \
    --genre practical --spine capstone --spine-name "客服工单问答助手" \
    --chapters 10 --words 4500,6000

# 混合 genre 用预设
python scripts/init_book.py --dest ../my-book --title "..." --preset principle-practical

# 1. 编依赖图，看关键路径 / 波宽 / 扇出
python scripts/plan.py --book ../my-book

# 2. 写完全书跑一次全链路（CI 入口）
python scripts/verify.py --book ../my-book
```

依赖：`pyyaml` 必需；`jsonschema` 缺失时 `schema_check.py` 降级为 info；渲染图需要 node（`npx -y @mermaid-js/mermaid-cli`）。

---

## 三、七阶段

| # | 阶段 | 产出 | 闸门 | 最常见死法 |
| --- | --- | --- | --- | --- |
| 0 | 立项 | `book.yaml` + `00-positioning.md` | G1 定位确认 | "读者是有一定基础的开发者"——说不出具体的人 |
| 1 | 蓝图 | `01-outline.md` + `02-toc.md` + `.book/dag.json` | G2 目录锁定 | 按技术点排章不管依赖，关键路径拉到 20 波 |
| 2 | 宪法 | `03-style-guide.md` + `glossary.json` | G3 宪法冻结 | 把宪法写成 500 行完整规范，写手根本读不完 |
| 3 | 章纲 | `04-chapter-plans/chNN.md` ×N | G4 章纲齐备 | 写一章发一章，依赖边错在下游已开工之后 |
| 4 | 定标 | 第一波章节（根节点） | G5 指纹校准 | 无（根节点在拓扑序上必须最先写，天然是样本） |
| 5 | 批量 | `chapters/chNN.md` + `src/` + `figures/` | G6 每章机检 | 先写正文再编代码，输出只能靠编 |
| 6 | 统稿 | `final/` | G7 全书验收 | 章序调过一次，"下一章"全部指错 |

**没有独立的"样章阶段"。** 根节点（无上游的 1–3 章）在拓扑序上必须最先写，写完自动抽取文风指纹，之后 S20 才有意义。

### 阶段路由：只 read 当前阶段的文件

| 在做 | 读这些 | 不要读 |
| --- | --- | --- |
| 阶段 0 | `references/01-intake.md` | 其它 |
| 阶段 1 | `references/02-blueprint.md` | 写作规范 |
| 阶段 2 | `references/03-constitution.md` + `genres/_core.md` + `genres/<genre>.md` | 章纲模板 |
| 阶段 3 | `references/04-chapter-plan.md` | 装配 |
| 阶段 5 | `references/05-writing.md` + `03-style-guide.md` + 本章纲 + 上游合同 | 其它章全文 |
| 阶段 6A | `references/06-review.md` | — |
| 阶段 6B | `references/07-assembly.md` | — |

**一次读完所有 references 会占满上下文，反而写不好。** 阶段 5 尤其要注意：写手拿上游的 `dep-brief/`，不拿上游全文——读全文会被带进别人的叙事节奏。

---

## 四、八条硬规则（违反即返工）

1. **不许跳过 `check.py`。** "我觉得可以了"不算过闸
2. **不许手画依赖图。** 依赖写在章纲 front-matter，由 `plan.py` 编译；手画的图必然和正文脱节
3. **不许编造运行输出。** 跑不出来就写「本章示例未验证」
4. **不许改冻结的文件。** `00`–`03` 一旦确认只读；要改先解冻、记录原因、**重跑所有已完稿章节的闸门**
5. **不许跨波传全文。** 下游只拿上游的 `contract` 与代码签名
6. **不许自评合格。** 闸门是脚本，不是判断题
7. **不许为凑字数注水。** 字数不够是内容不够，不是句子太短
8. **不许静默调和冲突。** 骨架冲突、genre 冲突、事实冲突，一律显式报出并说明采用了谁

第 4 条的第 3 小步最容易被跳过，也是"改了规范但书没跟上"的根源。

---

## 五、命令速查

```bash
python scripts/check.py --book <书目录>                  # 全部 5 组闸门
python scripts/check.py --book <书目录> --chapter ch03   # 单章（不跑全书级闸门）
python scripts/check.py --book <书目录> --gates structure,reference
python scripts/check.py --book <书目录> --json           # 机器可读，给调度器
python scripts/check.py --book <书目录> --suggest        # 生成 promises.jsonl 草稿

python scripts/plan.py --book <书目录>                   # 编译 dag.json / waves.json
python scripts/dep_brief.py --book <书目录>              # 生成上游摘要包（只含合同与签名）

python scripts/state.py --book <书目录> --init           # 初始化章节状态
python scripts/state.py --book <书目录> --report         # 下一步 + 账本磁盘漂移检测
python scripts/state.py --book <书目录> --claim ch03 --owner agent-a
python scripts/state.py --book <书目录> --set ch03 repair
python scripts/state.py --book <书目录> --rollback ch03
python scripts/state.py --book <书目录> --calibrate      # 第一波后校准文风指纹

python scripts/assemble.py --book <书目录>               # 装配自包含 final/
python scripts/verify.py --book <书目录>                 # 一条命令跑完全链路
python scripts/verify.py --self-test                     # 闸门回归台
python tests/run_tests.py                                # 6 基线 + 9 注入用例
```

退出码 1：`check.py` 有 error / `assemble.py` 有路径或占位问题 / `state.py` 冲突 / `verify.py` 任一步失败。

事实组与一致性组依赖 `.book/` 账本，账本为空时这两组**跳过并标注**，不会把"没查"误报成"通过"。

---

## 六、四本账（跨章一致性的真正来源）

| 账本 | 记什么 | 谁消费 |
| --- | --- | --- |
| `.book/glossary.json` | 术语 zh / en / def / 首现章 / 别名 | X01 X07 X08、附录 A |
| `.book/claims.jsonl` | 每个数字 + source + date + 口径 | F01 F02 F03、附录 B |
| `.book/promises.jsonl` | "后文会讲"的空头支票，必须结清 | X02 X06、装配阻断、附录 E |
| `.book/ladder.jsonl` | 每章 before/after 的能力阶梯 | X03、结语（唯一能追溯到条目） |

**维护账本的回报在装配阶段一次兑现**：没有 `glossary.json`，术语表要手工整理两天；有了它，附录 A 只是一次格式转换。

写作时的三条纪律：

- 任何数字必须进 `claims.jsonl`，**没有出处的数字不许出现在正文**
- 全书同一概念只能有一个名字，换成同义词即错误
- 每个技术选择都要讲**原因和代价**，只写成功案例不算技术写作

---

## 七、怎么选 genre

| genre | 骨架（H2 序列，另含头块与「下一章」） | 章字数 | 适合 |
| --- | --- | --- | --- |
| `practical` | 章首导图 → 场景开场 → 正文 → 小结 → 练习 → 自查清单 → 常见坑 | 5000–7000 | 动手手册，每章交付一个能力点 |
| `principle` | 概念地图 → 反直觉开场 → 正文 → 权衡表 → 失效边界 → 延伸阅读 | 6000–8000 | 原理与设计，讲机制与失效条件 |
| `project` | 阶段全景 → 现场开场 → 正文 → 阶段交付物 → 复盘 → 风险登记 | 4500–6500 | 交付驱动，**强制 `spine: capstone`** |
| `interview` | 考点地图 → 真实提问 → 分层解析 → 追问链 → 高频错误 → 自测 | 3000–5000 | 考点驱动，各章独立 |

骨架段名有别名表（`check.py` 按别名匹配 H2），**自创标题 = 直接判缺段**。「开场白」代替「场景开场」，闸门判 S02 缺段。

### 混合 genre：可以，但最多 3 个，且是"主 + 副"

```yaml
genre: [principle, practical]   # 第一个是主类型
```

**排他维度只有两项 —— 章节骨架和 spine，主类型说了算。** 其余全部可叠加：标注 / 反模式 / 断言词取并集，字数取交集，图表下限与信息密度取高，代码要求取严。

三条必须知道的边界：

1. **骨架是全书级的，不是每章级的。** 做不到"前几章原理骨架、后几章面试骨架"——S16 会把未命中别名表的 H2 判 error。想要"多方面"，用 `01-outline.md` 的**篇**（3–9 篇）来分，篇是读者问题维度，不是 genre 维度。
2. **把 `interview` 放副类型几乎没收益。** 它的价值 90% 在骨架（分层答案 + 追问链），而骨架是排他的；当副类型只并进来几个标注词。想要面试维度，在主类型骨架允许的 H3 里加固定小节，或做成附录。
3. **骨架冲突只打到 stderr，不是 error、不阻断。** 想要它真的拦住你，自己盯输出。已知缺口：`_ch_range` 在字数交集为空时返回倒挂区间而不报错（如 `principle` ∩ `interview`），所以混合时请在 `book.yaml` 显式写 `scale.words_per_chapter`。

官方预设（`--preset`）：`project-practical`、`principle-practical`、`interview-principle`。

---

## 八、写作阶段的三条铁律

1. **顺序是 代码 → 图 → 正文，不能反。** 反过来你会先写出"运行结果是 0.87"，再去找能跑出 0.87 的代码。
2. **不读上游全文。** 你拿到的是 `dep-brief/chNN.md`（合同与签名）。读全文会冲垮你自己的判断。
3. **章纲有问题就停，报告，不要自己改。** 章纲是全局调度的输入，你改一章的边界，邻章会重复、依赖图会失真。报告三行：章节 / 问题 / 影响 + 建议，由上游决定改章纲还是改书。

写完立刻产出 `.book/contracts/chNN.json`（`defines` / `provides` / `assumes` / `hook`）。下游只靠这个文件理解你写了什么，**合同写不清楚，下游一定会理解错**。

---

## 九、判断该停下来的信号

这些不是"再修一次就好"，是结构层的病，继续打补丁只会更糟：

- 同一章 `repair` 两次仍不过闸门
- 同一波次里三章以上出现同类术语冲突
- 缝合时发现某章 20% 以上的内容需要重写
- 学习目标写成了「理解 X」「掌握 X」——无法验收，也就无法写

出现任一条：回到阶段 1 改目录，或阶段 3 改章纲。

---

## 十、目录结构（一本书长什么样）

```
my-book/
├── book.yaml                 唯一契约，genre 给默认值这里只写差异
├── 00-positioning.md         定位（冻结）
├── 01-outline.md             篇级大纲（冻结）
├── 02-toc.md                 章级目录（冻结）
├── 03-style-guide.md         宪法：只写与 genre 的差异，≤200 行（冻结）
├── 04-chapter-plans/chNN.md  章纲（冻结）
├── dep-brief/chNN.md         上游摘要包，自动生成
├── chapters/chNN.md          正文
├── src/chNN/                 可运行代码
├── figures/chNN/*.mmd        图源码
├── assets/chNN/*.svg         图产物
├── .book/                    四本账 + contracts + state.json + 指纹
└── final/                    装配产物，自包含，不再手改
```

图统一出 SVG（`htmlLabels: false`，否则 Gitee 等阅读器渲染成白图），正文不嵌 Mermaid 源码。

---

## 十一、这个 SKILL 的文件

```
SKILL.md                  编排与路由（执行时看这个）
README.md                 本文件：使用方式与最佳实践（新用户先看这个）
SPEC.md                   完整设计规格（调度模型、闸门、格式约定）
references/               各阶段的操作手册（按阶段读，别一次读完）
genres/_core.{md,yaml}    跨类型宪法：语体、事实纪律、通用反模式
genres/<genre>.{md,yaml}  四套类型：practical / principle / project / interview
genres/presets.yaml       混合 genre 预设
schemas/                  book / state / dag / contract 四份契约
scripts/                   闸门、DAG、账本、装配、校验
templates/                book.yaml 注释模板、dep-brief、patch 清单
tests/                     四套 genre 样本 + 八章规模样本 + 账本非空样本
```

闸门清单与错误码见 `SPEC.md` §8 与 §18；样本预期结果见 `tests/README.md`（注意 `fixture/chapters/ch02.md` 是**刻意保留**的反例，不要"修好"它）。

---

## 十二、开工前先确认一件事

**这本书是给谁看的，读完他能做什么。**

说不清这两点，后面所有阶段都会返工。不要急着建目录、写章节，先把这一句问出来——这是阶段 0 唯一的目标。
