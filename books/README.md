# books/ · 四本 RAG 示例书

同一个主题（RAG），四种体裁，用来验证 `aia-handbook` 在不同骨架下的真实产出。
每本 8 章，都从阶段 0 跑到 `final/`，不是模板占位。

| 目录 | 书名 | 体裁 | 读者 | 章数 | 字数 | 图 | 代码 | 闸门 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rag-practical/` | RAG 实战：从零搭一个带引用的问答服务 | practical | 后端转 AI、没做过检索 | 8 | 17,753 | 14 | 30 段 | 0 error / 1 warn |
| `rag-principle/` | RAG 的原理与边界 | principle | 架构师、技术负责人 | 8 | 17,035 | 15 | 8 段伪码 | 0 error / 1 warn |
| `rag-project/` | RAG 交付实录：一个客服问答系统的八个阶段 | project | FDE、交付工程师 | 8 | 16,636 | 15 | 21 段 | 0 error / 1 warn |
| `rag-interview/` | RAG 面试通关：八个高频考点 | interview | 准备 AI 应用岗面试 | 8 | 11,380 | 8 | 0 | 0 error / 0 warn |

`rag-practical` 的 3 条 warn 是 X04 跨章重复：Ch05 刻意复用了 Ch03 的同一个客户失败案例，
属于连贯性设计，检测器按 5-gram 判重会报，不阻断。

## 怎么读

- 源稿：`<book>/chapters/chNN.md`，章节 front-matter 带依赖声明。
- 成书：`<book>/final/README.md`，含前言、正文、附录 A–E、结语与自包含 `assets/`。
- 章纲：`<book>/04-chapter-plans/chNN.md`，写手任务书。
- 上游摘要：`<book>/dep-brief/chNN.md`，只含合同与签名，不含上游全文。

## 重新构建一本

```bash
python aia-handbook/scripts/plan.py     --book books/rag-practical
python aia-handbook/scripts/dep_brief.py --book books/rag-practical
python aia-handbook/scripts/check.py    --book books/rag-practical
python aia-handbook/scripts/assemble.py --book books/rag-practical
```

`assemble.py` 会把 `assets/` 复制进 `final/`，并把正文里的 `../assets/` 重写为 `assets/`，
所以 `final/` 可以整包拷走，不会裂图。

## 四本的差异在哪

- **practical** 每章一个可交付能力，代码能跑，附实测输出。
- **principle** 不写完整实现，每章必有「权衡表（代价 / 适用条件）+ 失效边界 + 延伸阅读」。
- **project** 每节按「决策 → 实施 → 验证」组织，每阶段有交付物、验收人、风险登记、复盘。
- **interview** 每个考点给三档答案、三层追问、常见错误与限时自测，不写代码。
