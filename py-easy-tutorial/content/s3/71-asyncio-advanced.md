+++
id = "s3-71-asyncio-advanced"
order = 71
stage = "s3"
official_group = "advanced"
title = "asyncio 进阶"
concepts = ["wait_for", "TaskGroup", "timeout", "Semaphore", "cancellation"]
prereq = [70]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：asyncio.TaskGroup"
url = "https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup"

[[doc_refs]]
title = "Library Reference：asyncio 同步原语"
url = "https://docs.python.org/3/library/asyncio-sync.html"
+++

# 超时、限流与结构化并发

真实的异步程序要回答三个问题：任务卡死了怎么办（超时）、一万个请求怎么限流（信号量）、一批任务里一个失败怎么办（TaskGroup）。

## `wait_for`：给任务上一道保险

```python
import asyncio


async def slow():
    await asyncio.sleep(5)
    return "永远等不到"


async def main():
    try:
        await asyncio.wait_for(slow(), timeout=0.1)
    except TimeoutError:
        print("0.1 秒没跑完，取消")


asyncio.run(main())
```

```expect
0.1 秒没跑完，取消
```

`wait_for` 超时会**取消**内部任务（抛 `CancelledError` 进去），不只是"不等了"。所以被等待的协程应当正确响应取消——用 `try/finally` 清理。

## `TaskGroup`：结构化并发

```python
import asyncio


async def one():
    await asyncio.sleep(0.01)
    return 1


async def main():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(one())
        t2 = tg.create_task(asyncio.sleep(0.01, result=2))
    print(t1.result(), t2.result())


asyncio.run(main())
```

```expect
1 2
```

`async with TaskGroup` 保证：离开代码块时**所有子任务都已完成**；任何一个抛异常，其余任务被自动取消，异常打包成 `ExceptionGroup` 抛出。这是"结构化并发"——任务的生命周期不会逃出代码块。

## `Semaphore`：限制并发数

```python
import asyncio

results = []


async def worker(sem, index):
    async with sem:
        await asyncio.sleep(0.01)
        results.append(index)


async def main():
    sem = asyncio.Semaphore(2)  # 同时最多 2 个
    async with asyncio.TaskGroup() as tg:
        for i in range(5):
            tg.create_task(worker(sem, i))


asyncio.run(main())
print(len(results))
```

```expect
5
```

打一万URL但只允许 50 个并发——`Semaphore(50)` 包住请求就行。不加限流的并发请求会瞬间打挂对方服务器（或自己的 fd 上限）。

> [!tip] 超时分层
> 单个请求用 `wait_for(timeout=...)`；整批任务外层再套一层 `wait_for`。两层超时的组合能同时表达"单个卡死"和"整体太慢"两种故障。

```quiz
question = "`TaskGroup` 中一个任务抛异常，会发生什么？"
options = [
  "只有该任务失败，其余继续",
  "其余任务被取消，异常打包成 ExceptionGroup 向上抛",
  "所有任务的结果变成 None",
  "异常被 TaskGroup 吞掉"
]
answer = 1
explain = "这是结构化并发的核心：一个失败代表整组失败，TaskGroup 取消其余任务并把所有异常聚合抛出。compare gather(return_exceptions=True) 则是「各自收异常继续跑」，语义不同按需选择。"
```

## 小结

- `wait_for` 超时即取消，被等协程要用 try/finally 清理。
- `TaskGroup`：成组创建任务、全部等完、一败俱败（异常聚合）。
- `Semaphore` 限并发数，批量请求必配。
- 超时要分层：单任务一层，整批一层。
