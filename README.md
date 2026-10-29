# fde-tutorial

FDE（Forward Deployed Engineer）相关的教程与工具集。

## aia-handbook · 技术书创作 SKILL

把「写一本技术书」当成一次构建调度：**章是节点，依赖是边，拓扑序给波次，同波次并行，跨波只传合同。**

### 它解决什么

- 8 章以上的技术书、手册、系列教程，需要体系化且前后一致
- 已有零散笔记，要组织成书
- 要「读完能动手做出来」，不是概念罗列

少于 6 章不建议用这套流程，开销不划算。

### 快速开始

```bash
# 1. 生成一本书的项目骨架
python aia-handbook/scripts/init_book.py --dest ../my-book \
  --title "AI 应用评测入门" --genre practical --spine capstone \
  --spine-name 客服工单助手 --chapters 10 --words 4500,6000

# 2. 填 00-positioning.md → 写 02-toc.md 与 04-chapter-plans/
# 3. 编译依赖图（落盘 .book/dag.json / waves.json）
python aia-handbook/scripts/plan.py --book ../my-book

# 4. 生成上游摘要包（写手只读合同，不读上游全文）
python aia-handbook/scripts/dep_brief.py --book ../my-book

# 5. 写章 → 过闸门
python aia-handbook/scripts/check.py --book ../my-book --chapter ch01

# 6. 装配成书（自包含 final/）
python aia-handbook/scripts/assemble.py --book ../my-book
```

多作者协作时用 `state.py` 认领章节、看下一步、回滚旧稿：

```bash
python aia-handbook/scripts/state.py --book ../my-book --init
python aia-handbook/scripts/state.py --book ../my-book --report
python aia-handbook/scripts/state.py --book ../my-book --claim ch03 --owner agent-a
```

### 七个阶段

0 立项 → 1 蓝图 → 2 宪法 → 3 章纲 → 4 定标 → 5 批量 → 6 统稿 / 装配

### 目录

| 路径 | 内容 |
| --- | --- |
| `aia-handbook/SKILL.md` | 编排与路由（先读这个） |
| `aia-handbook/SPEC.md` | 完整设计规格，§18 是实现状态 |
| `aia-handbook/references/` | 各阶段操作手册 01–07 |
| `aia-handbook/genres/` | 四套体裁 + 混合预设 |
| `aia-handbook/scripts/` | check / plan / init_book / state / assemble / dep_brief / schema_check / verify |
| `aia-handbook/tests/` | 四套体裁样本 + 八章规模样本 + 账本非空样本 |

### 自测

```bash
# 一次跑完：6 个基线 + 9 个违规注入
python aia-handbook/tests/run_tests.py

# 或校验单本
python aia-handbook/scripts/verify.py --book aia-handbook/tests/fixture-principle
```

预期 `0 error / 0 warn`。`tests/fixture` 是刻意保留的反例，预期 `8 error / 2 warn`。
注入用例会故意造违规（删 claim、承诺挂 open、阶梯倒退…），断言每个错误码真能抓到——
这是「闸门查过」与「闸门没误报」的区别。

## 示例书

`books/` 下有四本用 RAG 主题写成的示例书，覆盖四种体裁，均已跑到 `final/`：

| 目录 | 体裁 | 书名 | 规模 |
| --- | --- | --- | --- |
| `books/rag-practical/` | practical | RAG 实战：从零搭一个带引用的问答服务 | 8 章 · 17,753 字 · 30 段代码 |
| `books/rag-principle/` | principle | RAG 的原理与边界 | 8 章 · 17,035 字 |
| `books/rag-project/` | project | RAG 交付实录：一个客服问答系统的八个阶段 | 8 章 · 16,636 字 · 21 段代码 |
| `books/rag-interview/` | interview | RAG 面试通关：八个高频考点 | 8 章 · 11,380 字 |

四本均 `0 error`；practical / principle / project 各有 1 条 S20（ch01 与其余章的
文风指纹偏离——定标章是单独一轮写的，这是真实信号，没有为了让闸门全绿去补内容）。
详见 [books/README.md](books/README.md)。

## License

见 [LICENSE](LICENSE)。
