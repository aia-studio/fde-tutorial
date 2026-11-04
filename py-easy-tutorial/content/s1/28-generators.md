+++
id = "s1-28-generators"
order = 28
stage = "s1"
official_group = "moderate"
title = "生成器"
concepts = ["yield", "generator", "send", "lazy evaluation", "pipeline"]
prereq = [27]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 9.9：生成器"
url = "https://docs.python.org/3/tutorial/classes.html#generators"

[[doc_refs]]
title = "Language Reference：yield 表达式"
url = "https://docs.python.org/3/reference/expressions.html#yield-expressions"
+++

# 函数可以"暂停"

普通函数 `return` 就结束了；带 `yield` 的函数每次产出后**停在原地**，下次调用 `next()` 从断点继续。状态（局部变量、执行位置）都保留着。

## 生成器就是迭代器的快捷写法

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1


print(list(countdown(3)))

gen = countdown(2)
print(next(gen), next(gen))
```

```expect
[3, 2, 1]
2 1
```

不用写 `__iter__` / `__next__`，也不用自己抛 `StopIteration`——函数返回时解释器自动处理。

## 惰性：不算完不占内存

```python
def squares(nums):
    for n in nums:
        yield n * n


print(sum(squares(range(4))))
print(list(squares(n for n in range(4) if n % 2 == 0)))
```

```expect
14
[0, 4]
```

`squares(range(10**9))` 也不会爆内存，因为它一次只算一个。这是生成器最大的价值：**用空间换时间的那一半被省掉了**。

## `send`：双向通道

```python
def echo():
    received = []
    while True:
        value = yield len(received)
        received.append(value)


g = echo()
print(next(g))
print(g.send("a"))
print(g.send("b"))
```

```expect
0
1
2
```

`yield` 不只能往外送值，还能接收值：`g.send(x)` 会把 `x` 赋给 `value`，然后继续执行到下一个 `yield`。第一次必须先 `next(g)`（或 `send(None)`），把生成器推到第一个 `yield`。

> [!why] 为什么需要 send
> 它是协程的雏形。`asyncio` 的 `await` 在底层就是这套机制的进化版——理解 `yield`/`send`，后面学 `async def` 会顺很多。

## 生成器表达式 vs 列表推导

```python
data = range(5)

gen = (n * 2 for n in data)
lst = [n * 2 for n in data]

print(type(gen).__name__, type(lst).__name__)
print(sum(gen), sum(gen))
```

```expect
generator list
20 0
```

第二次 `sum(gen)` 是 0，因为迭代器已经耗尽。**能只用一次、且数据量大**时用生成器；要反复遍历就用列表。

```quiz
question = "调用生成器函数 `countdown(3)` 时，函数体里的代码什么时候开始执行？"
options = [
  "调用时立刻执行到第一个 yield",
  "第一次 next() 时才开始执行",
  "函数返回时",
  "永远不会自动执行"
]
answer = 1
explain = "调用生成器函数只创建生成器对象，不执行函数体。第一次 next()（或 for 循环第一次取值）才真正开始执行，直到遇到第一个 yield。"
```

## 小结

- `yield` 让函数暂停并保留状态，下次 `next()` 从断点继续。
- 生成器是惰性的：不预先计算、不占整块内存。
- `send()` 可以向生成器内部传值，是协程的基础。
- 生成器只能遍历一次，需要复用时用列表。
