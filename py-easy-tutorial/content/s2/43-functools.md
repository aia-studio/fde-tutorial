+++
id = "s2-43-functools"
order = 43
stage = "s2"
official_group = "moderate"
title = "functools"
concepts = ["lru_cache", "partial", "singledispatch", "reduce", "wraps"]
prereq = [41]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：functools"
url = "https://docs.python.org/3/library/functools.html"

[[doc_refs]]
title = "Library Reference：lru_cache"
url = "https://docs.python.org/3/library/functools.html#functools.lru_cache"
+++

# 函数层面的工具箱

functools 的工具都围绕一个主题：**把函数当值来操作**——缓存它、固定参数、按类型分发、折叠序列。

## `lru_cache`：一行加缓存

```python
from functools import lru_cache

calls = []


@lru_cache(maxsize=None)
def fib(n):
    calls.append(n)
    return n if n < 2 else fib(n - 1) + fib(n - 2)


print(fib(30))
print(sorted(calls) == list(range(31)))
```

```expect
832040
True
```

没有缓存时 `fib(30)` 会递归上百万次；加上 `@lru_cache`，每个 n 只算一次（31 次调用，所以 `calls` 正好是 0..30）。这个数量级差别就是缓存的全部意义。

> [!warn] 缓存的前提是"纯函数"
> 同样的参数必须返回同样的结果。参数里带可变对象、或函数有副作用，缓存会给出**过期数据**。`maxsize=None` 适合参数空间小的递归；参数空间大用 `@lru_cache(maxsize=1024)` 防内存失控。

## `partial`：固定一部分参数

```python
from functools import partial


def power(base, exp):
    return base ** exp


square = partial(power, exp=2)
cube = partial(power, exp=3)

print(square(9), cube(3), square(base=4))
```

```expect
81 27 16
```

`partial(power, exp=2)` 返回一个**预填了关键字参数**的新函数。比 `lambda x: power(x, 2)` 好：不用写参数转发，`repr` 里还能看到绑定的值。

```python
from functools import partial


def power(base, exp):
    return base ** exp


two_to = partial(power, 2)
print(two_to(5), two_to(8))
```

```expect
32 256
```

按位置预填就固定了 `base=2`。注意 `square(3, 3)` 这种写法会报错——`exp` 已经被关键字占住，再传第二个位置参数就是"多重赋值"。

## `singledispatch`：按类型分发

```python
from functools import singledispatch


@singledispatch
def render(x):
    return f"默认：{type(x).__name__}"


@render.register
def _(x: int):
    return f"整数 {x}"


@render.register
def _(x: str):
    return f"字符串 {x}"


print(render(7))
print(render("hi"))
print(render(1.5))
```

```expect
整数 7
字符串 hi
默认：float
```

不用 `isinstance` 链就能按类型分支，新类型注册一个函数即可。比一长串 `isinstance` 更好扩展，也把每种类型的处理放在了各自的位置上。

## `reduce`：慎用但要知道

```python
from functools import reduce
from operator import mul

print(reduce(mul, [1, 2, 3, 4]))
print(reduce(mul, [], 1))
```

```expect
24
1
```

`reduce` 把序列折叠成一个值，第三个参数是初始值（空序列时必需）。多数场景 `sum` / `max` / `any` / `all` 更可读——reduce 留给真正"两两合并"的场合。

```quiz
question = "`@lru_cache` 装饰的函数，什么样的函数不适合？"
options = [
  "参数是元组的函数",
  "有副作用或返回值依赖外部状态的函数",
  "递归函数",
  "参数超过两个的函数"
]
answer = 1
explain = "缓存的前提是相同参数必有相同结果。读文件、查数据库、依赖随机数/时间/全局变量的函数被缓存后会返回过期数据。"
```

## 小结

- `lru_cache` 一行加缓存，只适合纯函数；递归加速立竿见影。
- `partial` 预填参数，比 lambda 转发更清楚。
- `singledispatch` 按类型分发，替代 isinstance 链。
- `reduce` 折叠序列，日常优先 sum/max/any/all。
