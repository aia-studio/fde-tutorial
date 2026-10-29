+++
id = "s0-01-install-repl"
order = 1
stage = "s0"
official_group = "beginner"
title = "安装、解释器与运行方式"
concepts = ["interpreter", "repl", "script", "runpy", "__main__"]
prereq = []
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Using Python：命令行与环境"
url = "https://docs.python.org/3/using/index.html"

[[doc_refs]]
title = "Tutorial 第 2 章：使用解释器"
url = "https://docs.python.org/3/tutorial/interpreter.html"
+++

# 三条路，一个解释器

同样一份代码，可以三种方式跑起来：交互式（REPL）、脚本、模块。这三种方式执行的是同一个解释器、同一套语义，差别只在**入口**和**名字空间**。先把这件事弄清楚，后面所有“为什么这里能跑、那里跑不了”的问题都会消失。

## 先确认你在跑哪个解释器

机器上装多个 Python 是常态。写代码之前，先让解释器自报家门——这不是仪式，是排错的第一步。

```python
import sys

print("major =", sys.version_info.major)
print("可运行本教程：", sys.version_info >= (3, 15))
```

```expect
major = 3
可运行本教程： True
```

这里故意没有打印完整版本号：完整版本号会随机器变化，而 `sys.version_info` 的比较在任何 3.x 上都稳定。**测试里依赖会变的东西，是脆弱的开始。**

## `__name__` 是理解运行方式的关键

同一个文件，直接运行时 `__name__` 是 `“__main__”`；被 `import` 时，它是模块名。Python 就是靠这一个变量区分“入口”和“被引用”的。

```python
print("__name__ 的值是:", __name__)
```

```expect
__name__ 的值是: __main__
```

所以那句看起来很怪的 `if __name__ == “__main__”:` 其实只是在问一句：**我现在是被直接运行，还是被别的文件导入？** 只有被直接运行时，才执行测试代码或命令行入口。

## 三种运行方式对照

| 方式 | 命令 | `__name__` | 典型用途 |
|---|---|---|---|
| 交互式 | `python` | `__main__` | 试一行代码、验证表达式 |
| 脚本 | `python main.py` | `__main__` | 完整程序 |
| 模块 | `python -m package.module` | `__main__` | 让包内相对导入正常工作 |

`-m` 这一行值得单独记住：它让 Python 先建立包上下文再执行模块，所以**包内部的相对导入只有 `-m` 才能跑通**。用 `python package/module.py` 跑同一个文件，`from . import x` 会直接报 `ImportError`。

> [!why] 为什么 `-m` 能解决相对导入
> 直接跑文件时，`sys.path[0]` 是那个文件所在的目录，包结构对解释器不存在；`-m` 则先把当前目录放进 `sys.path`，再按模块名逐级导入，父包因此可见。

## 常用开关

- `-i`：脚本跑完后进入交互式，变量全部保留，调试神器
- `-c “...”`：直接执行一段字符串，适合一行验证
- `-X utf8`：强制 UTF-8 模式（3.15 默认已是 UTF-8，老代码里还会见到）
- `--version` / `-VV`：`-VV` 会连编译器和构建信息一起打印

```quiz
question = "在包 `app/` 里执行 `python app/main.py`，文件中有 `from . import config`，会发生什么？"
options = [
  "正常运行，Python 会自动识别包结构",
  "报 ImportError：attempted relative import with no known parent package",
  "报 SyntaxError，相对导入语法不合法",
  "会跳过这行导入，继续执行"
]
answer = 1
explain = "直接运行文件时，该文件被当作顶层脚本，`__package__` 为空，解释器不知道父包是谁，相对导入无从解析。改用 `python -m app.main` 即可。"
```

## 本页代码块可以直接改

下面这块是给你练手的：把 `3, 15` 改成一个更大的版本号，看看结果怎么变。按 `Ctrl+Enter`（macOS 上是 `Cmd+Enter`）运行。

```python
import sys

required = (3, 15)
print("当前满足要求：", sys.version_info[:2] >= required)
```

> [!tip] 改代码比读代码有用
> 每改一次，你都在验证一个关于语言的假设。看到不符合预期的结果时，先别怀疑环境——先怀疑自己的假设。

## 小结

- 三种运行方式共用同一个解释器，差别在入口和 `__name__`。
- `if __name__ == “__main__”:` 是在判断“我是不是入口”。
- 包内相对导入要用 `-m` 运行，否则父包不可见。
- 排错第一步永远是：确认当前解释器是谁、版本是多少。
