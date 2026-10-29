+++
id = "s3-72-contextvars"
order = 72
stage = "s3"
official_group = "advanced"
title = "contextvars 与任务上下文"
concepts = ["ContextVar", "context", "async isolation", "threading.local"]
prereq = [71]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：contextvars"
url = "https://docs.python.org/3/library/contextvars.html"

[[doc_refs]]
title = "PEP 567：上下文变量"
url = "https://peps.python.org/pep-0567/"
+++

# 每个"请求"一份上下文

Web 服务里每个请求有自己的 request-id、当前用户。全局变量会把 A 请求的数据漏给 B 请求——并发下这是事故。`contextvars` 提供的是**按任务隔离**的"全局变量"。

## 协程任务间的隔离

```python
import asyncio
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")
seen = []


async def handle(name):
    request_id.set(name)
    await asyncio.sleep(0.01)
    seen.append(request_id.get())


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(handle("req-1"))
        tg.create_task(handle("req-2"))


asyncio.run(main())
print(sorted(seen))
```

```expect
['req-1', 'req-2']
```

两个任务各自 `set` 了自己的值，互不覆盖——每个 `create_task` 运行在**自己的上下文副本**里。换成普通全局变量，后一个 `set` 会冲掉前一个。

## 与 `threading.local` 的对比

| | `threading.local` | `contextvars.ContextVar` |
|---|---|---|
| 隔离单位 | 线程 | 线程 + 协程任务 |
| asyncio 任务间 | **不隔离**（同线程共享） | 隔离 |
| 典型场景 | 线程池中的连接缓存 | 请求 ID、当前用户、trace 上下文 |

```python
import threading

local = threading.local()
local.value = "主线程"

results = []


def worker():
    results.append(getattr(local, "value", "子线程没有这个属性"))


t = threading.Thread(target=worker)
t.start()
t.join()
print(results)
```

```expect
['子线程没有这个属性']
```

`threading.local` 只按线程隔离——线程内再开协程，所有协程共享同一份，等于没隔离。**asyncio 代码里用 ContextVar**，线程代码里才用 `threading.local`。

## 实际用法：日志与链路追踪

```python
import asyncio
import logging
import sys
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="-")

logging.basicConfig(
    level=logging.INFO,
    format="%(request_id)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("app")


class RequestFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id.get()
        return True


log.addFilter(RequestFilter())


async def handler(name):
    request_id.set(name)
    log.info("处理请求")


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(handler("r1"))
        tg.create_task(handler("r2"))


asyncio.run(main())
```

```expect
r1 处理请求
r2 处理请求
```

日志自动携带当前任务的 request-id——这就是 `ContextVar` 在真实系统里的头号用途：**不用把 request-id 一层层当参数传**。

```quiz
question = "在 asyncio 服务里给每个请求隔离存储 request-id，应该用？"
options = [
  "模块级全局变量 request_id",
  "threading.local()",
  "contextvars.ContextVar()",
  "每个函数加一个 request_id 参数并逐层传递"
]
answer = 2
explain = "全局变量跨任务共享会互相覆盖；threading.local 只按线程隔离，同一线程上的所有协程共享。ContextVar 按「任务上下文」隔离，且日志框架可自动携带。"
```

## 小结

- `ContextVar.set/get` 提供任务级隔离，`create_task` 各得一份副本。
- asyncio 代码用 `ContextVar`，线程代码用 `threading.local`，别用反。
- 头号用途：日志注入请求 ID、trace 上下文，省掉逐层传参。
- 修改要在**当前任务内**做，跨任务修改没有意义。
