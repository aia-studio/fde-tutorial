+++
id = "s1-29-project-todo"
order = 29
stage = "s1"
official_group = "moderate"
title = "小项目：命令行待办"
concepts = ["project", "json persistence", "shlex", "cli parsing"]
prereq = [28]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：shlex"
url = "https://docs.python.org/3/library/shlex.html"

[[doc_refs]]
title = "Tutorial 7.2：读写文件"
url = "https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files"
+++

# 把前面几课拼起来

一个能用的待办工具需要：数据结构（列表 + 字典）、持久化（JSON 文件）、命令解析（拆分用户输入）、异常处理（文件不存在）。这四件事前面都单独学过，现在合起来。

## 数据模型

```python
import json

todos = []


def add(todos, text):
    todos.append({"text": text, "done": False})


def finish(todos, index):
    todos[index]["done"] = True


add(todos, "写作业")
add(todos, "买菜")
finish(todos, 1)

print(json.dumps(todos, ensure_ascii=False))
print(sum(1 for t in todos if not t["done"]))
```

```expect
[{"text": "写作业", "done": false}, {"text": "买菜", "done": true}]
1
```

用字典而不是元组，是因为字段还会增加（截止日期、标签）——元组一改就要动所有调用点。

## 持久化：存得住才算工具

```python
import json
from pathlib import Path

path = Path("todos.json")
todos = [{"text": "写作业", "done": False}]

path.write_text(json.dumps(todos, ensure_ascii=False), encoding="utf-8")

if path.exists():
    loaded = json.loads(path.read_text(encoding="utf-8"))
else:
    loaded = []

print(len(loaded), loaded[0]["text"])
```

```expect
1 写作业
```

读之前先判 `exists()`，否则第一次运行就崩。这就是"文件不存在"这个异常最自然的处理方式——**预期内的失败，用判断而不是捕获**。

## 命令解析：别用 split

```python
import shlex


def parse(line):
    parts = shlex.split(line)
    return parts[0], parts[1:]


print(parse("add 写作业"))
print(parse('add "两件事 一起"'))
```

```expect
('add', ['写作业'])
('add', ['两件事 一起'])
```

`line.split()` 会把带空格的参数切碎。`shlex.split` 按 shell 规则处理引号，是解析命令行文本的正确工具。

> [!tip] 真做 CLI 时用 argparse
> 这一课手写解析是为了看清原理。真实工具用 `argparse`（第 46 课），它自动生成 `--help`、处理子命令和类型转换。

```quiz
question = "读取一个可能不存在的配置文件，更合适的写法是？"
options = [
  "直接 open()，崩了再说",
  "用 try/except FileNotFoundError 包住 open()",
  "先 if path.exists() 再 open()",
  "用 os.access(path, os.R_OK) 判断"
]
answer = 1
explain = "exists() 之后再 open() 之间存在竞态（文件可能被删），而且多一次系统调用。直接 try 是 Python 的惯用法（EAFP），也更短。"
```

## 小结

- 数据结构用字典，字段可以扩展而不破坏调用方。
- 持久化先写 JSON，读之前处理"文件不存在"。
- 命令行文本用 `shlex.split`，不要用 `str.split`。
- 预期内的失败优先用判断，真正的异常用 try/except。
