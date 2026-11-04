+++
id = "s5-98-pep-guide"
order = 98
stage = "s5"
official_group = "general"
title = "PEP 导读与索引"
concepts = ["PEP", "PEP 8", "PEP 20", "PEP 484", "PEP 695"]
prereq = []
standalone = true
requires_python = "3.15"
allow_network = false
xp = 10

[[doc_refs]]
title = "PEP Index（全部 PEP）"
url = "https://peps.python.org/"

[[doc_refs]]
title = "PEP 1：PEP 的目的与流程"
url = "https://peps.python.org/pep-0001/"
+++

# 语言演进的议会记录

PEP（Python Enhancement Proposal）是这门语言的立法档案：**每一个语法、每一个标准库决定都有对应的 PEP**。读 PEP 的能力 = 预知语言走向的能力。这一课教怎么读，并给出必读清单。

## 一篇 PEP 的结构

```text
PEP 695 – Type Parameter Syntax
├── PEP 头部    编号、作者、状态（Draft/Accepted/Final）、版本目标
├── Abstract    一段话说清提案是什么
├── Motivation  现状哪里疼（读它能看到设计者的痛点）
├── Specification  精确的语法/语义（逐条读，这里没有模糊空间）
├── Rejected Ideas  被否掉的方案与理由（最值得读的部分）
└── Copyright
```

**Rejected Ideas 是精华**：它解释了"为什么不是那样设计"——比正面论述更能建立设计直觉。比如 PEP 655 被拒的 dict 语法变体，直接说明了 `Required[]` 的取舍。

## 必读 PEP 清单

| PEP | 主题 | 在课程里的位置 |
|---|---|---|
| PEP 8 | 风格指南 | 第 60 课的设计模式、本课推荐先读 |
| PEP 20 | The Zen of Python | 第 101 课逐条解读 |
| PEP 484 | 类型注解规范 | 第 46、47 课的注解体系 |
| PEP 585 / 586 | 内置泛型、字面量类型 | `list[int]`、`Literal` |
| PEP 634 | 结构化模式匹配 | 第 11 课的 `match` |
| PEP 649 / 749 | 延迟注解求值 | 第 90 课运行时行为 |
| PEP 654 | 异常组与 `except*` | 第 85 课 |
| PEP 695 | 泛型语法 | 第 79 课 |
| PEP 750 | t-string | 第 20 课格式化 |

> [!tip] 读 PEP 的姿势
> 先读 Abstract 判断相关性 → Motivation 看痛点 → Specification 逐条读 → **Rejected Ideas 一定读**。Status 列（Draft/Final）决定它是"提议"还是"既成事实"——引用 Draft 的 PEP 时要注明。

## PEP 8 的三条最高频规则

```python
# 1. 命名：类 PascalCase，函数/变量 snake_case，常量 UPPER_CASE
class HttpRequest:
    DEFAULT_TIMEOUT = 30

# 2. 导入分组：标准库 / 第三方 / 本地，组间空一行
# 3. 行长 79（工具配置常放宽到 88/100），续行悬挂缩进
```

完整规则上百条，但**用 ruff/black 自动化之后，人只需要记住这三条**。风格检查交给工具，是人就该把时间花在设计和命名上。

```quiz
question = "读一篇 PEP 时，最值得细读的部分是？"
options = [
  "Abstract，因为它最短",
  "Specification，因为最精确",
  "Rejected Ideas，它解释了为什么不是别的方案",
  "Copyright"
]
answer = 2
explain = "被否决的方案 + 否决理由，是设计取舍的浓缩记录。理解了「为什么不做 A」，才真正理解「为什么选 B」。"
```

## 小结

- PEP 是语言的立法档案：每个决定都有编号、有理由、有状态。
- 阅读顺序：Abstract → Motivation → Specification → Rejected Ideas。
- 风格规则交给 ruff/black 自动执行，人管设计和命名。
- 必读清单：PEP 8 / 20 / 484 / 634 / 654 / 695，按需查原文。
