+++
id = "s4-83-bytecode"
order = 83
stage = "s4"
official_group = "advanced"
title = "字节码与执行模型"
concepts = ["bytecode", "dis", "co_consts", "constant folding", "LOAD_FAST"]
prereq = [82]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：dis"
url = "https://docs.python.org/3/library/dis.html"

[[doc_refs]]
title = "PEP 659：自适应解释器"
url = "https://peps.python.org/pep-0659/"
+++

# Python 不是"解释字符串"

源码先编译成**字节码**（bytecode），再由虚拟机逐条执行。`dis` 模块把字节码摊开——看一眼 `a + b` 变成了什么，性能直觉（第 64 课）就从"听说"变成"看见"。

## 一行加法的字节码

```python
import dis


def add(a, b):
    return a + b


instructions = list(dis.get_instructions(add))
print([i.opname for i in instructions])
```

```expect
['RESUME', 'LOAD_FAST_BORROW_LOAD_FAST_BORROW', 'BINARY_OP', 'RETURN_VALUE']
```

四条指令：把两个局部变量压栈、执行二元运算、返回栈顶。`LOAD_FAST` 是局部变量的专用指令——直接按槽位取，比查字典的全局变量（`LOAD_GLOBAL`）快。这就是第 16 课"赋值即局部"的性能解释。

## 常量折叠在编译期完成

```python
import dis


def f():
    return 1 + 2


print([i.opname for i in dis.get_instructions(f)][1:])
```

```expect
['LOAD_SMALL_INT', 'RETURN_VALUE']
```

`1 + 2` 在**编译期**就算成 3，运行时连常量表都不用查——直接一条 `LOAD_SMALL_INT`（小整数内嵌在指令的操作数里）。所以「写成 1+2 还是 3」对性能毫无差别——可读性说了算。

## 从字符串编译

```python
import dis

code = compile("x = 1\ny = x + 1", "<demo>", "exec")
print([i.opname for i in dis.get_instructions(code)][:4])
```

```expect
['RESUME', 'LOAD_SMALL_INT', 'STORE_NAME', 'LOAD_NAME']
```

模块级代码用 `STORE_NAME` / `LOAD_NAME`（名字空间是字典）；函数内用 `STORE_FAST` / `LOAD_FAST`（槽位数组）。同一个赋值，两层世界。

> [!tip] 这层知识什么时候有用
> 排查"为什么这个函数慢"时，字节码能证明结构差异（全局查找 vs 局部槽位）；读 `dis` 也是理解第 67 课 GIL 的前提——GIL 锁的正是"逐条执行字节码"这件事本身。日常写代码不需要它，调试性能和读 CPython 源码时需要。

```quiz
question = "`def f(): return 1 + 2` 的字节码里，有加法指令吗？"
options = [
  "有，BINARY_OP",
  "没有——常量折叠在编译期就算出 3，运行时只加载常量",
  "有，但只在第一次调用时执行",
  "取决于优化等级"
]
answer = 1
explain = "1 和 2 都是常量，CPython 在编译期完成求值（常量折叠），co_consts 里直接存了 3。这也是为什么「1+2 写不写成 3」不影响运行时性能。"
```

## 小结

- 源码 → 字节码 → 虚拟机逐条执行；`dis` 是字节码的透视镜。
- 局部变量 `LOAD_FAST`（槽位）比全局 `LOAD_GLOBAL`（字典）快。
- 常量折叠在编译期完成，字面量算式无运行时成本。
- GIL 锁的是字节码执行本身——理解并发绕不开这一层。
