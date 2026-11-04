+++
id = "s3-69-concurrency-choice"
order = 69
stage = "s3"
official_group = "advanced"
title = "并发模型选型"
concepts = ["concurrency models", "io-bound", "cpu-bound", "asyncio", "threads"]
prereq = [68]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：asyncio 与线程的对比"
url = "https://docs.python.org/3/library/asyncio.html"

[[doc_refs]]
title = "Tutorial：并发执行"
url = "https://docs.python.org/3/library/concurrency.html"
+++

# 三种并发，一张决策表

串行、线程、进程、asyncio——都能"同时做多件事"，但原理与适用场景完全不同。这一课只做一件事：给出**可执行的判断依据**。

## 实测：IO 密集任务，线程 5 倍加速

```python
import time
from concurrent.futures import ThreadPoolExecutor


def io_task():
    time.sleep(0.2)
    return "done"


t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=5) as pool:
    list(pool.map(lambda _: io_task(), range(5)))
t_threads = time.perf_counter() - t0

print(t_threads < 0.9)
```

```expect
True
```

5 个各等 0.2 秒的任务，串行要 1 秒，线程并发约 0.2~0.4 秒——因为 `sleep`（等待）期间 GIL 是释放的。把 `sleep` 换成 `sum(range(10**7))`，加速立刻消失（上一课的结论）。

## 决策表

| 场景 | 模型 | 理由 |
|---|---|---|
| 爬 1000 个网页、批量调接口 | asyncio 或线程池 | 等待为主，单线程事件循环最省资源 |
| 对大文件做 CPU 计算 | multiprocessing | 绕开 GIL，真并行 |
| 同时要并发 + 共享大量状态 | 线程池 + 队列 | 进程间共享状态成本高 |
| 一个 UI、一个后台下载 | 线程 | 简单、数量少 |
| 高并发网络服务（万级连接） | asyncio | 每连接一个线程的内存不可接受 |

## 常见误用

```python
# 反例：asyncio 里跑 CPU 密集任务
import asyncio


async def main():
    # await 才让出控制权；这里没有 await，整个事件循环被卡住
    total = sum(i * i for i in range(2_000_000))
    return total


asyncio.run(main())
print("事件循环被阻塞了整整一秒")
```

```expect
事件循环被阻塞了整整一秒
```

asyncio 的并发来自"在 `await` 处切换"。没有 `await` 的 CPU 循环会**独占事件循环**，其他任务全部停摆。CPU 部分要么扔给线程池（`loop.run_in_executor`），要么换 multiprocessing。

> [!tip] 数量也是决策依据
> 并发 10 个任务：线程池最简单。并发 1 万个连接：每线程 8MB 栈就是 80GB——只有 asyncio（每任务约几 KB）可行。**量级一变，答案就变。**

```quiz
question = "服务需要同时维护 2 万个长连接（每个连接大部分时间在等数据），选哪种模型？"
options = [
  "2 万个线程",
  "2 万个进程",
  "asyncio 事件循环",
  "串行处理，一个个来"
]
answer = 2
explain = "线程栈按 MB 算，2 万个就是数十 GB 内存；进程更重。asyncio 的事件循环把等待中的任务挂起，内存以 KB 计，且唤醒调度由事件循环统一管理。"
```

## 小结

- 等待密集 → asyncio 或线程池；计算密集 → multiprocessing。
- asyncio 的并发靠 `await` 处切换，CPU 循环会独占循环。
- 数量级是关键变量：10 个任务用线程，1 万个连接用 asyncio。
- 选型的第一步永远是问：这个任务**在等什么**？
