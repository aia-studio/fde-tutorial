+++
id = "s3-70-asyncio-basics"
order = 70
stage = "s3"
official_group = "advanced"
title = "asyncio 基础"
concepts = ["async def", "await", "event loop", "gather", "create_task"]
prereq = [69]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：asyncio"
url = "https://docs.python.org/3/library/asyncio.html"

[[doc_refs]]
title = "Library Reference：协程与任务"
url = "https://docs.python.org/3/library/asyncio-task.html"
+++

# `async def` 定义的是"可暂停的函数"

`async def` 声明协程：调用它**不执行函数体**，返回一个协程对象；`await` 才驱动它，并在 `await` 处把控制权交还事件循环。三个概念 chained：事件循环调度任务，任务包裹协程，`await` 是切换点。

## 顺序执行 vs 并发执行

```python
import asyncio


async def worker(name, delay):
    await asyncio.sleep(delay)
    return f"{name} 完成"


async def sequential():
    a = await worker("A", 0.1)
    b = await worker("B", 0.1)
    return [a, b]


async def concurrent():
    return await asyncio.gather(worker("A", 0.1), worker("B", 0.1))


print(asyncio.run(sequential()))
print(asyncio.run(concurrent()))
```

```expect
['A 完成', 'B 完成']
['A 完成', 'B 完成']
```

两者结果相同，耗时不同：顺序版 0.2 秒，并发版 0.1 秒。`await asyncio.gather(...)` 同时启动多个任务，等**全部**完成。

## 事件顺序：任务在 await 处切换

```python
import asyncio

events = []


async def worker(name):
    for i in range(2):
        await asyncio.sleep(0.01)
        events.append(f"{name}{i}")


async def main():
    await asyncio.gather(worker("A"), worker("B"))


asyncio.run(main())
print(events)
```

```expect
['A0', 'B0', 'A1', 'B1']
```

执行轨迹：A 跑到 `await` 让出 → B 跑到 `await` 让出 → A 恢复 → B 恢复。这就是**协作式调度**：谁不 `await`，谁就独占循环（第 69 课的反例）。

## `create_task`：立刻开始跑

```python
import asyncio

results = []


async def background():
    await asyncio.sleep(0.02)
    results.append("后台任务")


async def main():
    task = asyncio.create_task(background())
    results.append("主流程先做事")
    await task
    print(results)


asyncio.run(main())
```

```expect
['主流程先做事', '后台任务']
```

`gather` 是"等一批"，`create_task` 是"现在就启动，稍后再等"。后台任务在 `create_task` 的下一行**已经开始执行**，主流程可以先干别的再 `await task` 收结果。

> [!warn] 别忘了 await 你的任务
> `create_task` 之后从不 `await`，任务可能没跑完程序就结束了，而且没有异常报告。要么 `await task`，要么把它放进 `gather`——"发了任务不收"是最常见的 asyncio bug。

```quiz
question = "调用 `worker(\"A\", 0.1)`（协程函数）时，函数体里的代码何时开始执行？"
options = [
  "立刻执行到第一个 await",
  "完全不执行——只有被 await 或包装成 Task 后才开始",
  "在事件循环启动时执行",
  "由解释器后台线程执行"
]
answer = 1
explain = "协程对象是「暂停的函数」。直接调用只创建对象；gather/create_task/await 才把它交给事件循环驱动。这也是为什么忘了 await 会有 coroutine was never awaited 警告。"
```

## 小结

- `async def` 创建协程对象，`await` 驱动它并在该点切换。
- `gather` 并发等一批；`create_task` 立即启动、稍后收结果。
- 调度是协作式的：切换单点只有 `await`。
- 任务必须被 await，否则不执行且异常无声丢失。
