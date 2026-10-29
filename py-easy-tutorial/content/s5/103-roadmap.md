+++
id = "s5-103-roadmap"
order = 103
stage = "s5"
official_group = "general"
title = "学习路线图"
concepts = ["next steps", "web", "data", "automation", "roadmap"]
prereq = []
standalone = true
requires_python = "3.15"
allow_network = false
xp = 10

[[doc_refs]]
title = "Python Docs 首页"
url = "https://docs.python.org/3/"

[[doc_refs]]
title = "PEP Index"
url = "https://peps.python.org/"
+++

# 103 课之后走哪条路

本教程覆盖的是**语言本体与标准库**——它们是所有方向的地基。往下选方向时，先问自己要解决什么问题，再按问题选工具链。

## 四条常见路线

| 方向 | 典型问题 | 在本教程里的基础 | 下一步要补 |
|---|---|---|---|
| Web 后端 | 收请求、存数据、返回响应 | 44 结构化数据、54 日志、55 CLI、73 分层 | 一个框架 + ORM + 部署 |
| 数据处理 | 清洗、统计、可视化 | 24 结构化数据、44 collections、64–66 性能 | 数值与表格库、绘图 |
| 自动化/运维 | 批量文件、调外部命令、定时 | 21 文件、23 路径、56 子进程、54 日志 | 调度工具、模板 |
| CPython 本身 | 解释器怎么实现 | 69 字节码、74–78 对象模型、96 C API | CPython 源码与开发指南 |

## 每条路的第一周做什么

```python
# Web：把第 73 课的待办工具变成 HTTP 服务（标准库先行，再换框架）
from http.server import BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


print("handler 已定义——真实项目在此接入框架路由")
```

```python
# 数据：标准库的 statistics 起步，感受"够用"与"不够用"的分界
from statistics import mean, median

data = [2, 4, 4, 4, 5, 5, 7, 9]
print(mean(data), median(data))
```

> [!tip] 检验学习的唯一标准
> 挑一个**自己真实需要**的小工具做出来：报名脚本、账本、日志分析都行。做它的过程中遇到的每个问题，都能在本教程的 103 课里找到对应的讲解位置——找不到就是教程的欠账，欢迎指出。

## 三条通用建议

1. **读优秀代码比写更多**：标准库源码（`pathlib`、`dataclasses`）是最好的 Python 教材——结构清晰、有测试、有文档。
2. **用工具武装自己**：ruff/black 管风格、mypy/pyright 管类型、pytest 管行为——三件套配进 CI，从此不欠债。
3. **回到官方文档**：本教程每课的 `doc_refs` 都指向官方原文。习惯"看一手资料"，是脱离教程的标志。

```quiz
question = "学完本教程后，判断「该不该学一个新框架」的最好依据是？"
options = [
  "它是不是最流行",
  "你要解决的问题是否真的需要它，以及它的抽象是否匹配你的场景",
  "它的语法是否像 Python",
  "教程里有没有教"
]
answer = 1
explain = "框架是问题的解。先明确问题（要解决什么、量级多大、约束是什么），再看候选框架的抽象是否贴合——否则学到的是框架，不是解决问题的能力。"
```

## 小结

- 语言本体（103 课）是所有方向的地基，方向由"要解决的问题"决定。
- 四条路线的基础都在本教程内：Web、数据、自动化、CPython 本身。
- 做一个真实的小工具，是检验学习的唯一标准。
- 工具三件套（ruff / mypy / pytest）配进 CI，从此不欠债。
