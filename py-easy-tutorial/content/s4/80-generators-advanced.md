+++
id = "s4-80-generators-advanced"
order = 80
stage = "s4"
official_group = "advanced"
title = "生成器进阶"
concepts = ["state machine", "send", "throw", "close", "yield from"]
prereq = [79]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：生成器方法"
url = "https://docs.python.org/3/reference/expressions.html#generator-methods"

[[doc_refs]]
title = "PEP 342：通过生成器实现协程"
url = "https://peps.python.org/pep-0342/"
+++

# 生成器是有状态的对象

`yield` 之后生成器**暂停但不死**——它记着局部变量和执行位置。这让它天然是"状态机"：每次 `send` 推动状态前进。理解了这一点，`async def` 只是把这套机制包装得更顺手。

## send：推动状态机

```python
def state_machine():
    state = "开始"
    while True:
        received = yield state
        if received == "go":
            state = "运行"
        elif received == "stop":
            break


sm = state_machine()
print(next(sm))
print(sm.send("go"))

try:
    sm.send("stop")
except StopIteration:
    print("结束")
```

```expect
开始
运行
结束
```

`send("go")` 把值送进 `received` 并推进到下一个 `yield`。`break` 触发生成器结束，调用方收到 `StopIteration`——状态机走完了一生。

## close 与 finally：清理一定执行

```python
def resource():
    print("打开资源")
    try:
        yield 1
        yield 2
    finally:
        print("释放资源")


g = resource()
print(next(g))
g.close()
```

```expect
打开资源
1
释放资源
```

`close()` 在生成器内部暂停点抛 `GeneratorExit`，`finally` 因此执行。**持有资源的生成器必须保证能被安全 close**——这也是为什么清理逻辑要放在 `try/finally` 里而不是 yield 之后。

## `yield from`：委托子生成器

```python
def inner():
    yield 1
    yield 2


def outer():
    yield 0
    yield from inner()
    yield 3


print(list(outer()))
```

```expect
[0, 1, 2, 3]
```

`yield from` 把控制权完整交给子生成器：子生成器的值逐个产出，`send`/`throw` 也直接透传。它在语义上等价于"展开子生成器的所有 yield"，是构建**生成器流水线**的积木。

> [!tip] 从 yield 到 async 的演进
> 3.4 时代 `@asyncio.coroutine` 就是用 `yield from` 实现协程；3.5 引入 `async/await` 语法糖。所以看到旧代码里的 `yield from`，大脑里可以自动翻译成 `await`——语义几乎一致。

```quiz
question = "对暂停中的生成器调用 `close()`，内部会发生什么？"
options = [
  "什么都不做，生成器保持暂停",
  "在暂停点抛出 GeneratorExit，finally 得以执行",
  "从第一行重新开始执行",
  "立即终止进程"
]
answer = 1
explain = "close() 在当前 yield 处注入 GeneratorExit 异常，触发 try/finally 的清理路径。这就是「持有资源的生成器要能被安全关闭」的实现机制。"
```

## 小结

- `send` 推动状态机：暂停点收值、继续执行到下一个 yield。
- `close()` 注入 GeneratorExit，`finally` 负责清理。
- `yield from` 委托子生成器，值与控制权都透传。
- `yield from` 是 `await` 的前身，旧协程代码可照此理解。
