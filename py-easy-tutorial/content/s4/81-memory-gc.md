+++
id = "s4-81-memory-gc"
order = 81
stage = "s4"
official_group = "advanced"
title = "内存与垃圾回收"
concepts = ["refcount", "gc", "cycle", "__del__", "tracemalloc"]
prereq = [79]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：gc"
url = "https://docs.python.org/3/library/gc.html"

[[doc_refs]]
title = "Library Reference：sys.getrefcount"
url = "https://docs.python.org/3/library/sys.html#sys.getrefcount"
+++

# CPython 怎么回收你的对象

CPython 的回收是**两层**的：主回收是引用计数（立即、确定），循环引用交给 `gc` 模块定期处理。理解这两层，就明白"对象什么时候死"和"`__del__` 为什么不可靠"。

## 引用计数：归零即回收

```python
import sys

x = [1, 2, 3]
print(sys.getrefcount(x) >= 2)
```

```expect
True
```

`getrefcount(x)` 的值比直觉大 1（传参本身临时引用一次）。引用计数归零，对象**立即**被回收——这就是 CPython 里 `del` 之后文件句柄"看起来"自动关闭的原因。但正如第 21 课所说，这是实现细节，不能当设计。

## 循环引用：引用计数失效的地方

```python
import gc


class Node:
    def __init__(self, other=None):
        if other:
            other.partner = self
        self.partner = other


a = Node()
b = Node(a)
a.partner = b

del a, b
collected = gc.collect()
print(collected >= 0)
```

```expect
True
```

`a` 和 `b` 互相引用：即使两个名字都删了，计数仍是 1+1，引用计数永远不归零。`gc.collect()` 的循环检测器会找到这类"孤岛"并回收。返回值是本次回收的对象数（≥0）。

`gc` 平时自动运行（按分配阈值触发），无需手动调用；`gc.collect()` 在测试与排查时手动触发。

## `__del__`：能不写就不写

```python
import gc


class Resource:
    def __del__(self):
        pass


r = Resource()
weak_pool = gc.get_referrers(r)
print(isinstance(weak_pool, list))
```

```expect
True
```

`__del__` 的三宗罪：**调用时机不确定**（可能延迟到进程退出）、**循环引用里带 `__del__` 的对象曾长期无法回收**（3.4 起已修复，但仍应避免）、**异常会被静默忽略**。清理资源请用 `with`（上下文管理器），`__del__` 顶多是最后一道保险。

> [!tip] 排查内存增长
> 第 65 课的 `tracemalloc` 看分配热点；`gc.get_objects()` 能列出所有存活对象、按类型统计——程序越跑越慢/越占内存时，先用它确认是不是泄漏，再谈优化。

```quiz
question = "两个对象互相引用，名字全部删除后，它们会被回收吗？"
options = [
  "不会，引用计数永远不为零",
  "会——gc 的循环检测器负责回收不可达的引用环",
  "只有调用 gc.collect() 手动触发才会回收",
  "对象会永久占用内存直到进程退出"
]
answer = 1
explain = "引用计数处理不了循环，gc 的循环检测器会定期扫描并回收不可达的环。gc.collect() 可以立即触发一次；即使不调用，自动阈值也会处理。"
```

## 小结

- 引用计数是主回收：归零即释放，立即且确定。
- 循环引用交给 `gc` 循环检测器，自动或手动触发。
- `__del__` 时机不确定、异常被忽略——清理用 `with`。
- 内存排查：`tracemalloc` 看分配，`gc.get_objects()` 看存活。
