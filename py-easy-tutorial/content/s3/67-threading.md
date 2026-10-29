+++
id = "s3-67-threading"
order = 67
stage = "s3"
official_group = "advanced"
title = "线程与 GIL"
concepts = ["threading", "GIL", "lock", "race condition", "queue"]
prereq = [66]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：threading"
url = "https://docs.python.org/3/library/threading.html"

[[doc_refs]]
title = "Library Reference：queue"
url = "https://docs.python.org/3/library/queue.html"
+++

# 线程适合等，不适合算

Python 线程的两句话结论：**等 IO 时有用**（GIL 会在等待时释放），**跑 CPU 密集计算时无效**（GIL 保证同一时刻只有一个线程执行字节码）。但即使无效，**共享状态不加锁**照样出竞态——两件事要分开理解。

## 竞态：没有锁的计数器

```python
import threading

counter = 0


def worker(n):
    global counter
    for _ in range(n):
        counter += 1


threads = [threading.Thread(target=worker, args=(10000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter, "（期望 40000，实际几乎必然更小）")
```

这块**故意没有预期输出**：结果每次都不同，且几乎一定小于 40000。`counter += 1` 是"读、加、写"三步，线程会在中途被切换——这就是**竞态条件**。第 3 课讲的名字绑定在这里变成了并发问题。

## Lock：把三步变成一步

```python
import threading

counter = 0
lock = threading.Lock()


def worker(n):
    global counter
    for _ in range(n):
        with lock:
            counter += 1


threads = [threading.Thread(target=worker, args=(10000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)
```

```expect
40000
```

`with lock:` 保证同一时刻只有一个线程在临界区里。锁的代价是串行化——临界区越小，并发度越高。

## GIL：CPU 密集任务线程不加速

```python
import threading
import time


def cpu_task():
    return sum(i * i for i in range(200000))


t0 = time.perf_counter()
threads = [threading.Thread(target=cpu_task) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
t_threads = time.perf_counter() - t0

t0 = time.perf_counter()
cpu_task()
cpu_task()
t_serial = time.perf_counter() - t0

print(f"两个线程 {t_threads:.3f}s，串行两次 {t_serial:.3f}s——差距与抖动同量级")
```

这块同样没有预期输出。跑几次你会发现线程版**并不更快**：GIL 让字节码执行串行化。所以线程的适用场景是 IO 密集（网络请求、文件读写），CPU 密集要换 `multiprocessing`（下一课）。

> [!tip] 线程间传递数据用 queue.Queue
> 共享变量 + 锁容易写错。`queue.Queue` 自带锁，"生产者放、消费者取"是线程协作的标准姿势，第 68 课的线程池就是它的封装。

```quiz
question = "一个纯 CPU 计算（如对 1 亿个数求和）想加速，应该？"
options = [
  "开 8 个线程，GIL 会自动并行",
  "用 multiprocessing 分给多个进程，或用内置的向量化工具",
  "加 threading.Lock 保护计算",
  "把函数改成 async"
]
answer = 1
explain = "GIL 使同一时刻只有一个线程执行字节码，CPU 密集任务多线程不加速（free-threading 构建除外）。绕开方式：多进程（无 GIL）或把循环下沉到 numpy 这类 C 扩展。"
```

## 小结

- `counter += 1` 是三步操作，多线程下必然竞态；临界区用 `with lock:`。
- GIL：同一时刻一个线程执行字节码——线程加速不了 CPU 密集任务。
- 线程的用武之地是 IO 等待；CPU 并行用 multiprocessing。
- 线程间通信用 `queue.Queue`，少用共享变量加锁。
