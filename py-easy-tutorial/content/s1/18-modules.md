+++
id = "s1-18-modules"
order = 18
stage = "s1"
official_group = "beginner"
title = "模块与 `__main__`"
concepts = ["module", "import", "sys.modules", "__main__", "namespace"]
prereq = [17]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 6：模块"
url = "https://docs.python.org/3/tutorial/modules.html"

[[doc_refs]]
title = "Language Reference §5：导入系统"
url = "https://docs.python.org/3/reference/import.html"
+++

# 一个文件就是一个模块

`import` 做的事比看起来多：找文件、执行模块顶层代码、把结果缓存进 `sys.modules`、把名字绑到当前命名空间。理解这四步，"为什么改完代码没生效"和"为什么循环导入会炸"就都有答案了。

## 脚本运行时，`__name__` 是 `__main__`

```python
print(__name__)
print(__name__ == "__main__")
```

```expect
__main__
True
```

被 `import` 时，`__name__` 是模块名。所以那句 `if __name__ == "__main__":` 只是在问：**我是被直接运行，还是被导入？**

## 导入会执行模块顶层代码

```python
import math
import sys

print("math" in sys.modules)
print(math.sqrt(16))
print(math.__name__)
```

```expect
True
4.0
math
```

`sys.modules` 是导入缓存。同一个模块无论 `import` 多少次，顶层代码只执行一次，之后直接拿缓存里的对象。

```python
import math

first = id(math)
import math as again

print(first == id(again))
```

```expect
True
```

两次导入拿到的是同一个对象。这也是"模块级状态"能共享的原因——所有引用指向同一个模块实例。

> [!warn] 缓存也意味着：改完模块要重启
> 交互式环境里改了 `mymodule.py` 再 `import`，拿到的还是旧的。要用 `importlib.reload()`，但更省事的做法是重启解释器。

## 名字空间：模块就是一层命名空间

```python
import json

print(json.dumps({"a": 1}))
print(sorted(name for name in dir(json) if name in {"dump", "dumps", "load", "loads"}))
```

```expect
{"a": 1}
['dump', 'dumps', 'load', 'loads']
```

`dir(json)` 列出模块的公开名字。这也是为什么标准库模块名要短、函数名要具体——它们全在一个平面命名空间里。

`from ... import ...` 会把名字直接搬进当前命名空间，省前缀但容易撞名：

```python
from math import sqrt

print(sqrt(9))
```

```expect
3.0
```

写库代码时优先 `import math` 再 `math.sqrt`，读的人一眼知道来源；写脚本时 `from` 更省事。

```quiz
question = "直接运行 `python script.py` 时，`script.py` 里的 `__name__` 是什么？"
options = ["script", "__main__", "__init__", "None"]
answer = 1
explain = "被直接执行的模块，解释器会把 __name__ 设为 '__main__'；被导入时才是模块名。这就是 if __name__ == '__main__' 能区分入口与库的原因。"
```

## 小结

- 一个 `.py` 文件就是一个模块，模块名默认是文件名。
- 导入 = 查找 + 执行顶层代码 + 存入 `sys.modules` + 绑定名字。
- 同一模块多次导入只会执行一次，拿到同一个对象。
- `__name__ == "__main__"` 用来区分"入口"与"被导入"。
