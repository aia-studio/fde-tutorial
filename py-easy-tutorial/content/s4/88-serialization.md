+++
id = "s4-88-serialization"
order = 88
stage = "s4"
official_group = "advanced"
title = "序列化与拷贝"
concepts = ["pickle", "deepcopy", "__reduce__", "shallow vs deep"]
prereq = [87]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：copy"
url = "https://docs.python.org/3/library/copy.html"

[[doc_refs]]
title = "Library Reference：pickle"
url = "https://docs.python.org/3/library/pickle.html"
+++

# 对象如何"变成数据"再变回来

序列化（pickle/JSON）和拷贝（copy/deepcopy）本质是同一件事：**把对象图变成可传输/可复制的形态**。理解 `__reduce__` 这层协议，两者就通了。

## 深浅拷贝的分界线

```python
import copy

grid = [[1, 2], [3, 4]]

shallow = copy.copy(grid)
shallow[0].append(9)
print(grid)

deep = copy.deepcopy(grid)
deep[1].append(9)
print(grid)
```

```expect
[[1, 2, 9], [3, 4]]
[[1, 2, 9], [3, 4]]
```

浅拷贝只复制外层——内层列表仍是同一个对象，`append` 穿透。`deepcopy` 递归复制整棵对象图，两层完全独立。第 53 课陷阱合集的完整原理在这里。

## `deepcopy` 的两个配套参数

```python
import copy

class Config:
    def __init__(self, data):
        self.data = data

    def __deepcopy__(self, memo):
        # memo 记录"已复制的对象"，防止循环引用死循环
        new = Config(copy.deepcopy(self.data, memo))
        memo[id(self)] = new
        return new


cfg = Config({"a": [1]})
cfg.data["a"].append(2)
clone = copy.deepcopy(cfg)
print(clone.data)
```

```expect
{'a': [1, 2]}
```

`memo` 字典以 `id()` 为键记录"谁已复制"，循环引用靠它防止无限递归。自定义 `__deepcopy__` 时必须把新对象写进 memo。

## `pickle` 的协议层：`__reduce__`

```python
import pickle

class Versioned:
    def __init__(self, value):
        self.value = value

    def __reduce__(self):
        return (Versioned, (self.value,))  # (可调用对象, 参数元组)


original = Versioned(42)
restored = pickle.loads(pickle.dumps(original))
print(restored.value, restored.value == original.value)
```

```expect
42 True
```

`__reduce__` 回答"怎么重建这个对象"：返回 `(类, 构造参数)`。绝大多数类不需要手写——pickle 默认按 `__dict__` 处理。需要手写的场合：带打开资源、带全局状态、或想控制序列化格式的类。

> [!danger] pickle 的安全红线（重复第 59 课）
> `pickle.loads` 会执行对象图里的构造代码，**加载来路不明的 pickle = 执行任意代码**。第 59 课演示过攻击形态。跨信任边界传数据用 JSON；pickle 只用于自己的进程/机器之间。

```quiz
question = "`copy.copy` 与 `copy.deepcopy` 对嵌套列表 `[[1], [2]]` 的区别是？"
options = [
  "完全相同",
  "copy 只复制外层，内层列表仍与原对象共享；deepcopy 递归复制全部",
  "copy 更快所以内层也复制了",
  "deepcopy 不支持列表"
]
answer = 1
explain = "copy 是一层浅拷贝：新外层容器，内层引用不变，改内层会穿透。deepcopy 用 memo 递归复制整棵对象图，且能处理循环引用。"
```

## 小结

- 浅拷贝只复制外层，深拷贝递归复制并防循环（memo）。
- 自定义拷贝/序列化都基于 `__reduce__` 类协议。
- pickle 默认按 `__dict__` 重建，特殊类才手写 `__reduce__`。
- 安全红线：不加载来路不明的 pickle。
