+++
id = "s3-55-cli"
order = 55
stage = "s3"
official_group = "moderate"
title = "命令行接口"
concepts = ["argparse", "subcommand", "choices", "type conversion"]
prereq = [54]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：argparse"
url = "https://docs.python.org/3/library/argparse.html"

[[doc_refs]]
title = "Tutorial 4.8.4：argparse"
url = "https://docs.python.org/3/tutorial/stdlib.html#command-line-arguments"
+++

# `sys.argv` 是字符串，argparse 才是接口

`sys.argv` 给的是裸字符串列表，类型转换、必填校验、`--help` 全要自己造。`argparse` 用**声明式**定义接口，剩下的事它做。

## 位置参数与类型转换

```python
import argparse

parser = argparse.ArgumentParser(prog="todo")
parser.add_argument("command", choices=["add", "list", "done"])
parser.add_argument("text", nargs="*")

args = parser.parse_args(["add", "写作业", "买菜"])
print(args.command, args.text)
```

```expect
add ['写作业', '买菜']
```

`choices` 限定合法取值（枚举思路的命令行版）；`nargs="*"` 收零到多个参数。非法的命令会让 argparse 自己打印错误并以退出码 2 退出——不需要你写校验。

## 子命令：git 风格的接口

```python
import argparse

parser = argparse.ArgumentParser(prog="todo")
sub = parser.add_subparsers(dest="cmd", required=True)

p_add = sub.add_parser("add")
p_add.add_argument("text")

p_done = sub.add_parser("done")
p_done.add_argument("index", type=int)

args = parser.parse_args(["add", "买菜"])
print(args.cmd, args.text)

args = parser.parse_args(["done", "2"])
print(args.cmd, args.index, type(args.index).__name__)
```

```expect
add 买菜
done 2 int
```

每个子命令有**独立的参数定义**：`add` 要文本、`done` 要整数。`dest="cmd"` 把选中的子命令名存进结果。`type=int` 负责转换，转不了它自己报错。

> [!tip] 子命令是 CLI 的目录
> 工具超过三个功能就该拆子命令：`todo add`、`todo list`、`todo done 2`。每个子命令在自己的 parser 里定义参数，互不干扰——和第 19 课的包结构是同一种组织思想。

## `--help` 是白送的

```python
import argparse

parser = argparse.ArgumentParser(prog="todo", description="一个待办工具")
parser.add_argument("--version", action="version", version="todo 1.0")
parser.parse_args(["--version"])
```

```expect
todo 1.0
```

`--version`、`-h/--help` 全部自动生成，帮助文本来自你写的 `description` 和参数说明。**接口文档和接口定义在同一处**，这是声明式最大的红利。

```quiz
question = "`parser.add_argument(\"done\", type=int)` 的 `type=int` 负责？"
options = [
  "仅作文档说明，不影响运行",
  "把命令行字符串转成 int，转换失败自动报错退出",
  "限制取值范围",
  "把结果存成 int 类型的字符串"
]
answer = 1
explain = "argparse 会对每个位置参数调用 type()，失败时打印错误并以退出码 2 结束。也就是说类型校验在接口层完成，业务代码拿到的已经是转换后的值。"
```

## 小结

- `choices` 限定取值，`type` 负责转换，非法输入自动报错退出。
- 子命令让工具按功能组织，各自有独立参数。
- `--help` / `--version` 自动生成，文档与实现同源。
- 接口层的校验做完，业务代码拿到的就是干净的数据。
