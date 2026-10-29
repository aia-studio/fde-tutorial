+++
id = "s1-17-closures"
order = 17
stage = "s1"
official_group = "beginner"
title = "闭包与晚绑定"
concepts = ["closure", "cell", "late binding", "factory function"]
prereq = [16]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python FAQ：闭包"
url = "https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result"

[[doc_refs]]
title = "Language Reference：函数定义"
url = "https://docs.python.org/3/reference/compound_stmts.html#function-definitions"
+++

# 函数记着自己的出生地

闭包 = **函数 + 它引用的外层变量**。内层函数不只是代码，它还带着一层"环境"。理解这一点，`lambda` 在循环里为什么全返回同一个值就迎刃而解了。

## 工厂函数：用闭包造函数

```python
def make_multiplier(factor):
    def multiply(n):
        return n * factor

    return multiply


double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5), triple(5))
```

```expect
10 15
```

`multiply` 用完 `factor` 之后，`make_multiplier` 已经返回了，但 `factor` 没有消失——它被存进了闭包单元（cell），跟着 `multiply` 一起活下去。

```python
def outer():
    x = 42

    def inner():
        return x

    return inner


f = outer()
print(f.__closure__[0].cell_contents)
```

```expect
42
```

`__closure__` 是内部结构，平时不用碰；但看一眼能确认"值确实被记住了"。

## 晚绑定：lambda 在循环里的经典坑

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])
```

```expect
[2, 2, 2]
```

三个函数都返回 2。它们**没有各自保存 i 的值**，只保存了"变量 i 所在的那个作用域"。循环结束时 `i` 是 2，于是三个函数调用时读到的都是 2。

这是**晚绑定**（late binding）：闭包捕获的是变量，不是值。

修法是把当前值绑定到参数默认值上——默认值在定义时求值：

```python
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])
```

```expect
[0, 1, 2]
```

另一个修法是再套一层函数：

```python
def make(i):
    return lambda: i


funcs = [make(i) for i in range(3)]
print([f() for f in funcs])
```

```expect
[0, 1, 2]
```

> [!warn] 这个坑不止出现在循环里
> 任何"延迟执行 + 可变外层变量"的组合都会中招：事件回调、延迟任务、生成器表达式。判断方法很简单——**函数体里读的那个名字，是不是之后还会变？**

```quiz
question = "`funcs = [lambda: i for i in range(3)]` 之后 `[f() for f in funcs]` 得到什么？"
options = ["[0, 1, 2]", "[2, 2, 2]", "[0, 0, 0]", "报错"]
answer = 1
explain = "三个 lambda 共用同一个外层变量 i，调用时才读取它的值。循环结束后 i 是 2，所以三个都返回 2。用 `lambda i=i: i` 把当前值固化成默认参数即可解决。"
```

```exercise
id = "s1-17-ex1"
title = "写一个计数器工厂"
prompt = "实现 `make_counter(start=0)`：返回一个函数，每次调用返回递增后的值（第一次调用返回 start+1）。"
starter = """
def make_counter(start=0):
    # 返回一个计数器函数
    pass
"""
solution = """
def make_counter(start=0):
    count = start

    def step():
        nonlocal count
        count += 1
        return count

    return step
"""
tests = [
  "c = make_counter(); assert c() == 1 and c() == 2, '默认从 0 开始递增'",
  "d = make_counter(10); assert d() == 11, '从 start 开始递增'",
  "c2 = make_counter(); assert c2() == 1, '两个计数器互不影响'"
]
hints = [
  "在外层函数里放一个变量保存当前值。",
  "内层函数要修改外层变量，必须声明 nonlocal。",
  "结构：`count = start` → `def step(): nonlocal count; count += 1; return count` → `return step`。"
]
xp = 10
```

## 小结

- 闭包捕获的是**变量**，不是值；变量活在 cell 里，函数返回后仍然存在。
- 循环里创建函数会共享同一个变量，导致晚绑定。
- 修法一：`lambda i=i: i` 用默认参数固化；修法二：再套一层工厂函数。
- 改外层变量要 `nonlocal`，否则会变成新的局部变量。
