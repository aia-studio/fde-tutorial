+++
id = "s4-82-weakref"
order = 82
stage = "s4"
official_group = "advanced"
title = "弱引用与缓存设计"
concepts = ["weakref", "WeakValueDictionary", "cache invalidation", "finalize"]
prereq = [81]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：weakref"
url = "https://docs.python.org/3/library/weakref.html"

[[doc_refs]]
title = "Library Reference：weakref.finalize"
url = "https://docs.python.org/3/library/weakref.html#weakref.finalize"
+++

# 引用它，但不延长它的生命

弱引用指向对象，却**不增加引用计数**——对象是否存活由别人决定。这是"缓存不阻止回收"的唯一解法：缓存里的对象没人用了，就该自动消失。

## 弱引用的基本行为

```python
import weakref


class Service:
    pass


obj = Service()
ref = weakref.ref(obj)

print(ref() is obj)

del obj
print(ref() is None)
```

```expect
True
True
```

`ref()` 返回原对象，**或 None**（对象已死）。调用方每次都必须处理 None 分支——这正是弱引用的契约："我给你对象，但不保证它活着"。

## WeakValueDictionary：会自动清理的缓存

```python
import weakref


class Session:
    pass


pool = weakref.WeakValueDictionary()
session = Session()
pool["user-1"] = session

print(pool["user-1"] is session)

del session
print(len(pool))
```

```expect
True
0
```

值是弱引用：除了缓存没有任何地方引用 `Session` 时，条目自动消失。会话池、对象池、按需重建的重资源缓存，都适合这个模式。

## 弱引用不能指什么

```python
import weakref

try:
    weakref.ref([1, 2, 3])
except TypeError as exc:
    print(type(exc).__name__)
```

```expect
TypeError
```

`list`、`dict`、`str` 等**内置基础类型不支持弱引用**——它们没有给弱引用留钩子位。实践上这不是问题：给自定义类的实例建弱引用即可，或者用 `weakref.ref(obj.some_list)` 引用"持有列表的对象"。

> [!tip] weakref.finalize：不依赖 __del__ 的清理
> `finalize(obj, callback)` 注册"对象死后执行"的回调，且回调持有的是 finalize 对象而不是 obj，不会形成循环。它是 `__del__` 的安全替代，特别适合"注册表 + 对象释放时反注册"。

```quiz
question = "用弱引用实现缓存，缓存条目什么时候消失？"
options = [
  "缓存被清空时",
  "对象的所有强引用都消失时",
  "调用 gc.collect() 时立即全部消失",
  "永远不会消失"
]
answer = 1
explain = "弱引用不延长对象生命周期。当别处不再有强引用，对象被回收，弱引用条目随之失效并自动清理。gc.collect() 只是可能提前触发回收，不是条件。"
```

## 小结

- `weakref.ref(obj)()`：返回原对象或 None，每次都要处理 None。
- `WeakValueDictionary`：值消失条目自动清理，适合会话/资源池。
- 内置基础类型不支持弱引用；给自定义类用。
- 清理回调用 `weakref.finalize` 替代 `__del__`。
