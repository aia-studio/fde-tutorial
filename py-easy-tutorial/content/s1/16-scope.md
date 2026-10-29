+++
id = "s1-16-scope"
order = 16
stage = "s1"
official_group = "beginner"
title = "作用域与名字查找"
concepts = ["scope", "LEGB", "global", "nonlocal", "UnboundLocalError"]
prereq = [15]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference §4.2：命名与绑定"
url = "https://docs.python.org/3/reference/executionmodel.html#binding-of-names"

[[doc_refs]]
title = "Python FAQ：Python 的作用域规则"
url = "https://docs.python.org/3/faq/programming.html#what-are-the-rules-for-local-and-global-variables-in-python"
+++

# 名字在哪里生效

Python 查一个名字时按 **LEGB** 顺序找：Local（函数内）→ Enclosing（外层函数）→ Global（模块）→ Builtin（内置）。找不到就 `NameError`。这条规则不难，难的是**赋值会让名字变成局部的**。

## 局部遮蔽全局

```python
x = "global"


def show():
    x = "local"
    return x


print(show())
print(x)
```

```expect
local
global
```

函数内的 `x = "local"` 创建了一个新的局部名字，和外面的 `x` 没有关系。这是好事——函数不会意外污染全局。

## 但读取外层的值是可以的

```python
x = "global"


def read():
    return x


print(read())
```

```expect
global
```

只读不赋值时，找不到局部名字就往上找，所以能读到全局的 `x`。

## `global`：确实要改全局

```python
count = 0


def bump():
    global count
    count += 1


bump()
bump()
print(count)
```

```expect
2
```

去掉 `global` 会怎样？`count += 1` 既是读也是写，Python 看到赋值就认定 `count` 是局部的，于是读取时抛出 `UnboundLocalError`：

```python
total = 0


def broken():
    try:
        total += 1
    except UnboundLocalError as exc:
        return type(exc).__name__


print(broken())
```

```expect
UnboundLocalError
```

> [!why] 为什么要这样设计
> 编译期就能确定每个名字属于哪个作用域，局部变量可以放在固定槽位里（`LOAD_FAST`），比每次查字典快得多。代价就是这个"赋值即局部"的规则。

## `nonlocal`：改外层函数的值

```python
def counter():
    n = 0

    def inc():
        nonlocal n
        n += 1
        return n

    return inc


c = counter()
print(c(), c(), c())
```

```expect
1 2 3
```

`nonlocal` 指向**最近的外层函数作用域**，不跨越到全局。它和闭包是配套的，下一课会看到 `nonlocal` 正是闭包保持状态的机制。

```quiz
question = "函数内执行 `count += 1` 但没有声明 global，会发生什么？"
options = [
  "修改全局 count",
  "抛 UnboundLocalError，因为赋值让 count 变成局部名字",
  "创建局部 count，全局不变",
  "语法错误"
]
answer = 1
explain = "`+=` 含赋值语义，编译期就把 count 判定为局部变量；执行到读取那一步时局部还没绑定，于是 UnboundLocalError。要改全局必须写 global，要新建局部则不该读它的旧值。"
```

## 小结

- 查找顺序 LEGB：局部 → 外层函数 → 全局 → 内置。
- **只要在函数里赋值，这个名字就是局部的**，除非声明 `global` / `nonlocal`。
- `UnboundLocalError` 几乎总是"忘了写 global"或"变量名打错"。
- `nonlocal` 只穿透到最近的外层函数，不触及全局。
