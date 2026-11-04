+++
id = "s2-48-abc-protocols"
order = 48
stage = "s2"
official_group = "moderate"
title = "抽象基类与协议"
concepts = ["ABC", "abstractmethod", "runtime_checkable", "register", "interface"]
prereq = [47]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：abc"
url = "https://docs.python.org/3/library/abc.html"

[[doc_refs]]
title = "Library Reference：typing.Protocol"
url = "https://docs.python.org/3/library/typing.html#typing.Protocol"
+++

# 定义"必须实现什么"

上一课的 `Protocol` 是结构化检查；`ABC` 是**名义上的契约**——继承它就必须实现抽象方法，否则连实例化都过不去。两者服务于不同场景。

## 抽象基类：漏实现直接报错

```python
from abc import ABC, abstractmethod


class Shape(ABC):
    @abstractmethod
    def area(self): ...

    def describe(self):
        return f"面积为 {self.area():.2f}"


class Square(Shape):
    def __init__(self, side):
        self.side = side

    def area(self):
        return self.side ** 2


print(Square(3).describe())

try:
    Shape()
except TypeError:
    print("抽象类不能实例化")
```

```expect
面积为 9.00
抽象类不能实例化
```

`@abstractmethod` 在**实例化时**检查（不是导入时）：子类漏实现 `area`，`Square()` 就会抛 `TypeError`。抽象基类还能携带公共实现（`describe`），子类免费继承。

## 抽象属性与漏实现的时机

```python
from abc import ABC, abstractmethod


class Store(ABC):
    @property
    @abstractmethod
    def name(self): ...


class MemoryStore(Store):
    name = "内存存储"


print(MemoryStore().name)
```

```expect
内存存储
```

抽象属性 = `@property` + `@abstractmethod` 的组合。子类用类属性或 property 覆盖均可——**检查发生在实例化那一刻**，写代码时静态检查器也会同步标红。

## `register`：事后补票

```python
from abc import ABC


class Serializer(ABC):
    pass


class JSONSerializer:
    def dumps(self, data):
        return str(data)


Serializer.register(JSONSerializer)

print(issubclass(JSONSerializer, Serializer))
print(issubclass(list, Serializer))
```

```expect
True
False
```

`register` 把一个**没有继承关系**的类登记为子类（常用于"第三方类"）。注意它只是让 `issubclass` 通过，**不会检查任何方法**——比 `@abstractmethod` 宽松得多。

> [!tip] 怎么选
> 团队协作、接口是承诺（漏实现是 bug）→ 用 ABC。适配外部类、只关心"长得像" → 用 `typing.Protocol`。同一个项目两者混用很正常：内部契约用 ABC，对接第三方用 Protocol。

```quiz
question = "`@abstractmethod` 的检查发生在什么时机？"
options = [
  "定义抽象类时",
  "导入包含抽象类的模块时",
  "实例化子类时",
  "调用抽象方法时"
]
answer = 2
explain = "漏实现的方法集合在实例化时检查：Shape() 报 TypeError，而 Square 没实现 area 的话 Square() 也会报错。只 import 不实例化不会触发。"
```

## 小结

- `ABC` + `@abstractmethod` 是名义契约，实例化时强制检查。
- 抽象基类可以有具体实现，子类免费继承。
- `register` 事后认领第三方类，但不检查方法。
- 结构化检查（长得像就行）用 `Protocol`，强契约用 ABC。
