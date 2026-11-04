+++
id = "s0-02-docs-map"
order = 2
stage = "s0"
official_group = "beginner"
title = "文档地图与查资料的方法"
concepts = ["docs", "docstring", "dir", "inspect", "help"]
prereq = [1]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python 文档首页"
url = "https://docs.python.org/3/"

[[doc_refs]]
title = "内置函数帮助：help()"
url = "https://docs.python.org/3/library/functions.html#help"
+++

# 先学会查，再学会背

Python 的标准库有两百多个模块、上千个函数。没有任何人靠记忆写代码——大家都是在**确切知道自己要找什么**的前提下，几秒钟内查到。这一课只讲一件事：文档在哪里，以及怎么用最短路径拿到它。

## 文档就在对象身上

你不需要打开浏览器就能看到一个函数是干什么的。每个函数、类、模块都带一个 `__doc__` 字符串。

```python
def greet(name):
    """把名字拼成问候语。"""
    return "hi " + name


print(greet.__doc__)
print(type(greet.__doc__).__name__)
```

```expect
把名字拼成问候语。
str
```

标准库函数同理——第一行通常就是一句话定义：

```python
print(len.__doc__.strip().splitlines()[0])
```

```expect
Return the number of items in a container.
```

> [!tip] 这也是写注释的理由
> 你写的 docstring 不只是给人看的，它会被 `help()`、IDE 提示、`inspect.getdoc()` 直接读走。一行话把"做什么"说清楚，比三行注释讲"怎么做"更有用。

## `dir()` 告诉你有什么，`inspect` 告诉你长什么样

记不住某个类型有哪些方法时，先列出来再筛：

```python
methods = [name for name in dir(str) if name.startswith("split")]
print(methods)
```

```expect
['split', 'splitlines']
```

想知道一个函数要什么参数：

```python
import inspect


def greet(name):
    """把名字拼成问候语。"""
    return "hi " + name


print(inspect.signature(greet))
print(inspect.signature(dict.get))
```

```expect
(name)
(self, key, default=None, /)
```

第二行里的 `/` 是**位置参数分隔符**：它左边的参数只能用位置传，不能写成 `key=...`。这个符号在标准库里到处都是，看不懂就很容易写出 `d.get(key="a")` 然后报错。

## 三份文档各管一段

| 文档 | 回答什么问题 | 什么时候用 |
|---|---|---|
| Tutorial | 这是什么、怎么开始 | 第一次接触某个主题 |
| Library Reference | 这个模块/函数的确切行为 | 查参数、返回值、异常 |
| Language Reference | 语法和语义的正式定义 | 想搞清楚"为什么这样" |

大多数人只翻第一份，遇到细节就猜——这是 bug 的主要来源之一。**参数默认值、异常类型、边界条件，只在 Reference 里写得准。**

```quiz
question = "想知道 `list.sort()` 在元素不可比较时会抛什么异常，最该查哪份文档？"
options = [
  "Tutorial 里关于列表的章节",
  "Library Reference 里 list.sort 的条目",
  "Language Reference 的表达式章节",
  "搜索引擎第一条结果"
]
answer = 1
explain = "异常类型、参数默认值、稳定性保证这类精确行为，只在 Library Reference 里写。Tutorial 讲用法，Language Reference 讲语法语义。"
```

## 小结

- `obj.__doc__` 和 `help(obj)` 是最快的入口，不用联网。
- `dir(obj)` 列出成员，`inspect.signature(f)` 给出参数表，注意 `/` 和 `*` 的含义。
- Tutorial 讲入门、Library 讲行为、Language Reference 讲语义，别拿错。
- 查文档的能力，比记住 API 更耐用。
