+++
id = "s3-73-capstone-cli"
order = 73
stage = "s3"
official_group = "advanced"
title = "综合项目：可测试的 CLI 工具"
concepts = ["capstone", "layering", "argparse", "unittest", "integration"]
prereq = [72]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 4.8：更多控制流工具（综合运用）"
url = "https://docs.python.org/3/tutorial/controlflow.html"

[[doc_refs]]
title = "Library Reference：argparse"
url = "https://docs.python.org/3/library/argparse.html"
+++

# S1–S3 的毕业考

一个"能拿得出手"的小工具要同时做到：**逻辑可测试**（纯函数）、**接口可扩展**（argparse 子命令）、**状态可持久**（JSON 文件）、**失败可定位**（异常与日志）。这一课把 15–72 课的零件装成一个整体。

## 核心逻辑 + 测试（同一块里自包含）

```python
import json
import io
import unittest
from pathlib import Path


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, todos: list[dict]) -> None:
    path.write_text(json.dumps(todos, ensure_ascii=False), encoding="utf-8")


def add(todos: list[dict], text: str) -> dict:
    todo = {"text": text, "done": False}
    todos.append(todo)
    return todo


def finish(todos: list[dict], index: int) -> bool:
    if 0 <= index < len(todos):
        todos[index]["done"] = True
        return True
    return False


class TestCore(unittest.TestCase):
    def test_add_returns_todo(self):
        todos = []
        todo = add(todos, "写作业")
        self.assertEqual(todos, [{"text": "写作业", "done": False}])
        self.assertIs(todos[0], todo)

    def test_finish_out_of_range_is_safe(self):
        self.assertFalse(finish([], 5))

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "data.json"
            todos = load(store)
            add(todos, "买菜")
            save(store, todos)
            self.assertEqual(load(store)[0]["text"], "买菜")


import tempfile

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCore)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(result.wasSuccessful(), result.testsRun)
```

```expect
True 3
```

分层在代码里的体现：`add` / `finish` 只操作列表、**不碰文件**——所以测试不需要文件；`load` / `save` 只做读写——所以它们可以单独测。**逻辑与 IO 分层，是"可测试"的全部秘密。**

## 接口层：argparse 接收，分发到核心

```python
import argparse


def add(todos: list[dict], text: str) -> dict:
    todo = {"text": text, "done": False}
    todos.append(todo)
    return todo


def finish(todos: list[dict], index: int) -> bool:
    if 0 <= index < len(todos):
        todos[index]["done"] = True
        return True
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")

    p_add = sub.add_parser("add")
    p_add.add_argument("text")

    p_done = sub.add_parser("done")
    p_done.add_argument("index", type=int)
    return parser


def run(args, todos: list[dict]) -> str:
    if args.cmd == "list":
        return "\n".join(
            f"{'x' if t['done'] else ' '} {i} {t['text']}" for i, t in enumerate(todos)
        )
    if args.cmd == "add":
        add(todos, args.text)
        return "已添加"
    if args.cmd == "done":
        return "已完成" if finish(todos, args.index) else "编号不存在"
    return "未知命令"


parser = build_parser()
todos = []
print(run(parser.parse_args(["add", "买菜"]), todos))
print(run(parser.parse_args(["list"]), todos))
```

```expect
已添加
  0 买菜
```

`run(args, todos)` 是纯函数：输入解析结果和状态，返回输出。它不打印、不读文件——真实项目里让它返回字符串列表，由最外层负责打印。**每一层都可以单独替换**：换 GUI 就换接口层，换数据库就换 load/save。

> [!tip] 从这里到真实项目还差三步
> 1. 把 `load/save` 换成数据库（第 24 课的 JSON 已够教学用）；
> 2. 加 `logging`（第 54 课）代替 print 调试；
> 3. 用第 61–63 课的流程打包发布。课程后半段的综合项目（第 84 课）会把这三步做全。

```quiz
question = "「逻辑与 IO 分层」在测试上最大的好处是？"
options = [
  "测试跑得更快",
  "纯函数不需要真实文件/网络就能测试所有分支，包括错误路径",
  "可以少写测试",
  "测试可以直接调用私有方法"
]
answer = 1
explain = "add/finish 只操作内存列表，边界条件（空列表、越界）全部可以在内存里构造，测试因此又快又稳定。IO 层单独留出薄薄的一层，用少量集成测试覆盖。"
```

## 小结

- 分层：核心逻辑（纯函数）→ 存储层（load/save）→ 接口层（argparse）。
- 每层独立可测：逻辑用单测覆盖全分支，IO 留薄层。
- argparse 子命令即接口文档；`run(args, state)` 返回结果而不是直接打印。
- 15–72 课的所有零件在这一课合体，第 84 课是它的加强版。
