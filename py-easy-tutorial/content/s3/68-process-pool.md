+++
id = "s3-68-process-pool"
order = 68
stage = "s3"
official_group = "advanced"
title = "多进程与线程池"
concepts = ["ProcessPoolExecutor", "ThreadPoolExecutor", "pickling", "map"]
prereq = [67]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：concurrent.futures"
url = "https://docs.python.org/3/library/concurrent.futures.html"

[[doc_refs]]
title = "Library Reference：multiprocessing"
url = "https://docs.python.org/3/library/multiprocessing.html"
+++

# 高层接口：提交任务，拿结果

`concurrent.futures` 把线程池和进程池统一成同一个接口：`Executor.submit` / `map` / `as_completed`。切换线程与进程只需换一个类名——这是它最大的价值。

## ThreadPoolExecutor：线程池

```python
from concurrent.futures import ThreadPoolExecutor


def fetch(n):
    return n * n


with ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(fetch, [1, 2, 3, 4]))

print(results)
```

```expect
[1, 4, 9, 16]
```

`pool.map` 保持输入顺序返回结果；`with` 结束时等待全部任务完成。IO 密集任务（并发请求、批量下载）用线程池。

## ProcessPoolExecutor：绕开 GIL

```python
from concurrent.futures import ProcessPoolExecutor


def square(n):
    return n * n


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as pool:
        print(list(pool.map(square, [1, 2, 3])))
```

```expect
[1, 4, 9]
```

进程池里每个 worker 是独立解释器，没有 GIL 限制，CPU 密集任务真正并行。注意 `if __name__ == "__main__"`：Windows 上子进程用 spawn 方式启动，**会重新导入主模块**——没有这个守卫会无限递归。

> [!warn] 进程池的隐藏成本：序列化
> 参数与返回值都要 pickle（第 74 课）：传大对象慢、返回不可 pickle 的对象（如打开的文件句柄）直接报错。所以进程池的任务应该是"传小参数、返回小结果"，重数据放进程内准备。

## 逐个完成：as_completed

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def fetch(n):
    time.sleep(0.1 * (5 - n))
    return n


with ThreadPoolExecutor(max_workers=3) as pool:
    futures = [pool.submit(fetch, n) for n in range(5)]
    done_order = [f.result() for f in as_completed(futures)]

print("完成顺序与提交顺序不同：", done_order != [0, 1, 2, 3, 4])
print(sorted(done_order))
```

> 这块没有预期输出：完成顺序取决于每个任务的耗时与池大小，每次运行可能不同。
> 能确定的只有两件事——五个任务**全部完成**，且完成顺序**不等于**提交顺序。

`as_completed` 按**完成顺序**（不是提交顺序）给出结果。本例 `max_workers=3`：先启动的 0、1、2 各需 0.5/0.4/0.3 秒，最先完成的是 2；它们腾出工人后 3、4 才上场——所以顺序是 2,1,0,4,3。「谁先好先用谁」配合 `submit` 使用。

```quiz
question = "用 ProcessPoolExecutor 时，为什么任务函数必须能被 pickle？"
options = [
  "pickle 让函数运行更快",
  "参数与返回值要通过序列化在父子进程间传递",
  "pickle 提供内存共享",
  "不 pickle 会被杀进程"
]
answer = 1
explain = "每个 worker 是独立进程，调用参数要发过去、返回值要发回来，通道就是 pickle。不可序列化的对象（打开的文件、socket）会直接报错。"
```

## 小结

- `Executor.map` 保持顺序，`submit + as_completed` 按完成顺序。
- 线程池管 IO 并行，进程池管 CPU 并行（绕开 GIL）。
- 进程池的代价是 pickle：传小参数、返回小结果。
- Windows 下进程池入口必须有 `if __name__ == "__main__"` 守卫。
