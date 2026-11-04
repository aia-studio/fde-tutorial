+++
id = "s4-76-attribute-interception"
order = 76
stage = "s4"
official_group = "moderate"
title = "属性拦截"
concepts = ["__getattr__", "__getattribute__", "proxy", "lazy loading"]
prereq = [75]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference：自定义属性访问"
url = "https://docs.python.org/3/reference/datamodel.html#customizing-attribute-access"

[[doc_refs]]
title = "Library Reference：object.__getattr__"
url = "https://docs.python.org/3/reference/datamodel.html#object.__getattr__"
+++

# 两个拦截器，一步之差

`__getattr__` 是**常规查找失败后**的兜底；`__getattribute__` 是**所有属性访问的必经之路**。一个温和、一个凶猛——用错后者，递归爆炸只需一行代码。

## `__getattr__`：只在找不到时触发

```python
class Config:
    def __init__(self):
        self.debug = True

    def __getattr__(self, name):
        return f"<默认值：{name}>"


c = Config()
print(c.debug)
print(c.timeout)
```

```expect
True
<默认值：timeout>
```

`c.debug` 存在于实例字典，`__getattr__` **不会被调用**；`c.timeout` 找不到，才轮到它。

## `__getattribute__`：每次都经过

```python
class Logged:
    def __init__(self):
        self.x = 1

    def __getattribute__(self, name):
        print(f"访问 {name}")
        return super().__getattribute__(name)


obj = Logged()
print(obj.x)
```

```expect
访问 x
1
```

所有访问（包括 `self.x` 这种方法内部的）都会经过。**在里面直接写 `self.x` 会无限递归**——必须用 `super().__getattribute__`。这也是它危险的原因：一个疏忽就是 `RecursionError`。

## 代理：两个拦截器的正当用途

```python
class LazyProxy:
    def __init__(self, factory):
        self._factory = factory
        self._target = None

    def _load(self):
        if self._target is None:
            self._target = self._factory()
        return self._target

    def __getattr__(self, name):
        return getattr(self._load(), name)


def heavy():
    print("（真正加载）")
    return type("Data", (), {"greet": lambda self: "你好"})()


proxy = LazyProxy(heavy)
print("代理已创建，但还没加载")
print(proxy.greet())
print(proxy.greet())
```

```expect
代理已创建，但还没加载
（真正加载）
你好
你好
```

第一次访问才真正构造目标对象——懒加载。`__getattr__` 把未知属性转发给目标，这就是**代理模式**。注意 `_factory`、`_target` 以下划线开头，避免被代理转发。

```quiz
question = "在 `__getattribute__` 里直接写 `return self.name`，会发生什么？"
options = [
  "正常返回 name 属性",
  "无限递归，最终 RecursionError",
  "返回 None",
  "抛 AttributeError"
]
answer = 1
explain = "self.name 又触发一次 __getattribute__，再访问 self.name……唯一安全的路径是 super().__getattribute__(name)。同理 __setattr__ 里要写 super().__setattr__。"
```

## 小结

- `__getattr__` = 失败兜底；`__getattribute__` = 全部必经，危险。
- `__getattribute__` 内部必须走 `super()`，否则递归。
- 正当用途：代理、懒加载、属性访问日志。
- 用 `__getattr__` 做懒加载时，内部状态名用下划线开头。
