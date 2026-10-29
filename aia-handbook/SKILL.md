---
name: tech-book-writer
description: 用 agent 流水线把技术主题写成一本结构化的书（Markdown 书稿 + 可运行代码 + 图表源码）。当用户要写技术书、写手册、写系列教程、把一个主题组织成 8 章以上的体系化长文，或已有零散内容需要成书时使用。关键词：写书、技术书、手册、系列教程、电子书、book、handbook、成书。
---

# 技术书生产流水线

把写书当成一次构建调度：**章是节点，依赖是边，拓扑序给波次，同波并行，跨波只传合同。**

不靠"让 agent 一章章写"，靠三样东西兜住质量：
1. **冻结的宪法**（每本书现场生成，批量前锁死）
2. **可执行的闸门**（`scripts/check.py`，不靠 agent 自评）
3. **账本**（术语 / 事实 / 承诺，跨章一致性由数据保证，不靠记忆）

## 何时用 / 何时不用

| 用 | 不用 |
| --- | --- |
| 8 章以上的技术书、手册、系列教程 | 单篇文章、博客 |
| 已有零散笔记，要组织成体系 | 文档翻译、代码注释 |
| 需要"读完能动手做出来"的内容 | 纯营销文案、产品说明 |

少于 6 章不要用这套流程，直接用写作能力写，开销不划算。

## 七阶段

| # | 阶段 | 产出 | 闸门 |
| --- | --- | --- | --- |
| 0 | 立项 | `book.yaml` + `00-positioning.md` | G1 定位确认 |
| 1 | 蓝图 | `01-outline.md` + `02-toc.md` + `.book/dag.json` | G2 目录锁定 |
| 2 | 宪法 | `03-style-guide.md` + `glossary.json` | G3 宪法冻结 |
| 3 | 章纲 | `04-chapter-plans/chNN.md` ×N | G4 章纲齐备 |
| 4 | 定标 | 第一波章节（根节点） | G5 指纹校准 |
| 5 | 批量 | `chapters/chNN.md` + `src/` + `figures/` | G6 每章机检 |
| 6 | 统稿 | `final/` | G7 全书验收 |

**没有独立的"样章阶段"。** 根节点（无上游的 1–3 章）在拓扑序上必须最先写，
它们天然就是定标样本——写完全书自动抽取文风指纹。

## 阶段路由（只读当前阶段需要的文件）

| 在做 | 读这些 | 不要读 |
| --- | --- | --- |
| 阶段 0 | `references/01-intake.md` | 其它 |
| 阶段 1 | `references/02-blueprint.md` | 写作规范 |
| 阶段 2 | `references/03-constitution.md` + `genres/_core.md` + `genres/<genre>.md` | 章纲模板 |
| 阶段 3 | `references/04-chapter-plan.md` | 装配 |
| 阶段 5 | `references/05-writing.md` + `03-style-guide.md` + 本章纲 + 上游合同 | 其它章全文 |
| 阶段 6A | `references/06-review.md` | — |
| 阶段 6B（装配） | `references/07-assembly.md` | — |

**阶段 4（定标）不单独读文件。** 根节点章（无上游的 1–3 章）在拓扑序上最先写，
写完自动承担定标作用，指纹校准见 `03-constitution.md` §四。

**一次读完所有 references 会占满上下文，反而写不好。** 按阶段取用。

## 硬规则（违反即返工）

1. **不许跳过 `check.py`。** 任何章节进入下游前必须过闸门，"我觉得可以了"不算
2. **不许手画依赖图。** 依赖写在章纲 front-matter，由脚本编译；手画的图必然和正文脱节
3. **不许编造运行输出。** 跑不出来就写「本章示例未验证」，不许伪造终端输出
4. **不许改冻结的文件。** `00`–`03` 一旦确认只读；要改先解冻并记录原因
5. **不许跨波传全文。** 下游只拿上游的 `contract` 与代码签名，传全文会冲垮一致性
6. **不许自评合格。** 闸门是脚本，不是判断题
7. **不许为凑字数注水。** 字数低于下限要补实质内容，高于上限要改章纲的 `target_words`
8. **不许静默调和冲突。** 骨架冲突、genre 冲突、事实冲突，一律显式报出并说明采用了谁

## 命令速查

```bash
# 校验一本书（默认跑全部 5 组：结构 / 引用 / 代码 / 事实 / 一致性）
python scripts/check.py --book <书目录>

# 只查某一章（单章模式不跑全书级闸门）
python scripts/check.py --book <书目录> --chapter ch03

# 只跑指定组（逗号分隔）
python scripts/check.py --book <书目录> --gates structure,reference

# 机器可读输出（给调度器消费）
python scripts/check.py --book <书目录> --json

# 编译依赖图，落盘 .book/dag.json 与 waves.json
python scripts/plan.py --book <书目录>

# 生成上游摘要包（只含合同与签名，不含上游全文）
python scripts/dep_brief.py --book <书目录>

# 初始化章节状态 / 看下一步 / 认领一章（多作者）
python scripts/state.py --book <书目录> --init
python scripts/state.py --book <书目录> --report
python scripts/state.py --book <书目录> --claim ch03 --owner agent-a

# 第一波写完后校准文风指纹（之后 S20 才有意义）
python scripts/state.py --book <书目录> --calibrate

# 装配成书（自包含 final/，assets 一起复制，顺带生成 versions.lock）
python scripts/assemble.py --book <书目录>

# 一条命令跑完全链路（CI 入口）
python scripts/verify.py --book <书目录>
python scripts/verify.py --self-test        # 闸门回归台
```

五组闸门见 SPEC §8。其中事实组 / 一致性组依赖 `.book/` 账本；账本不存在或为空时
这两组会跳过并在输出里标注，不会把"没查"误报成"通过"。

`state.py` 的所有写操作都过 `.book/state.lock`，越权改别人的章会被拒；
`--expect-rev` 可做乐观并发校验。`repair` 会自动留旧稿，`--rollback` 可回滚。
`--report` 同时做账本与磁盘的漂移检测——正文写完但状态还是 pending 会直接说出来。

文风指纹不是摆设：`--calibrate` 用已完成章的中位数定基准，`check.py` 的 S20
逐章比对，两项以上偏离才告警。

退出码：`check.py` 有 error、`assemble.py` 有路径/占位问题、`state.py` 冲突、
`verify.py` 任一步失败时返回 1。

## 这个 skill 的文件

```
SKILL.md                  本文件：编排与路由
README.md                 使用方式与最佳实践（新用户先看这个）
SPEC.md                   完整设计规格（调度模型、闸门、格式约定）
references/               各阶段的操作手册
genres/_core.{md,yaml}    跨类型宪法：语体、事实纪律、通用反模式
genres/<genre>.{md,yaml}  四套类型：practical / principle / project / interview
genres/presets.yaml       混合 genre 预设（project-practical 等）
schemas/                  book / state / dag / contract 四份契约
scripts/check.py          闸门执行器（5 组 + 全书级 + 资产级，见 SPEC §18）
scripts/plan.py           DAG 编译与波次，落盘 dag.json / waves.json
scripts/dep_brief.py      生成上游摘要包（只读合同，不读全文）
scripts/init_book.py      生成书项目骨架（含指纹、mermaid、preset）
scripts/state.py          状态机与多作者协作（加锁、归属、续跑、回滚、指纹校准）
scripts/assemble.py       自包含装配 final/（含 versions.lock 生成）
scripts/schema_check.py   按 schemas/*.json 校验 book/state/dag/contract
scripts/verify.py         一条命令跑完全链路，供 CI
templates/book/book.yaml  带注释的项目模板
templates/dep-brief.md    上游摘要包模板
templates/patch.md        缝合清单模板
mermaid.config.json       渲染默认配置（htmlLabels=false）
tests/                    四套 genre 样本 + 八章规模样本 + 账本非空样本（见 tests/README.md）
tests/run_tests.py        闸门回归台：基线数量 + 违规注入
```

## 开工前先确认一件事

**这本书是给谁看的，读完他能做什么。**

说不清这两点，后面所有阶段都会返工。不要急着建目录、写章节，
先把这一句问出来——这是阶段 0 唯一的目标。
