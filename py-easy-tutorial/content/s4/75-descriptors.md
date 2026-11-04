+++
id = "s4-75-descriptors"
order = 75
stage = "s4"
official_group = "moderate"
title = "描述符协议"
concepts = ["descriptor", "__get__", "__set__", "__set_name__", "binding"]
prereq = [74]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "HOWTO：描述符指南"
url = "https://docs.python.org/3/howto/descriptor.html"

[[doc_refs]]
title = "Language Reference：实现描述符"
url = "https://docs.python.org/3/reference/datamodel.html#implementing-descriptors"
+++

# `self` 的魔法从哪来

上一课留了一个问题：方法为什么能自动拿到 `self`。答案是**描述符**——函数对象实现了 `__get__`。`property`、`classmethod`、`staticmethod`、`__slots__`，全部建立在同一个协议上。理解描述符，Python 的属性系统就"透明"了。

## 数据描述符与非数据描述符

```python
class Ten:
    def __get__(self, obj, objtype=None):
        return 10


class A:
    x = Ten()


a = A()
print(a.x)
```

```expect
10
```

实现了 `__get__` 的类是描述符；**再实现 `__set__`** 就是数据描述符（否则是非数据描述符）。这个区分决定优先级：数据描述符 > 实例字典 > 非数据描述符 > `__getattr__`。

## 方法绑定：`__get__` 在起作用

```python
import types


def add(self, other):
    return self.value + other


class Box:
    def __init__(self, value):
        self.value = value

    add = add


b = Box(10)
print(b.add(5))
print(type(b.add).__name__)
```

```expect
15
method
```

把函数赋给类属性后，通过实例访问它，拿到的是**绑定方法**——`function.__get__(instance, owner)` 返回一个把实例绑进去的 method 对象。这就是 `self` 的全部来源：不是语法，是描述符。

## `__set_name__`：描述符知道自己的名字

```python
class Positive:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        if value <= 0:
            raise ValueError(f"{self.name} 必须为正数")
        obj.__dict__[self.name] = value


class Order:
    qty = Positive()
    price = Positive()

    def __init__(self, qty, price):
        self.qty = qty
        self.price = price


order = Order(2, 10)
print(order.qty, order.price)

try:
    order.qty = -1
except ValueError as exc:
    print("拒收：", exc)
```

```expect
2 10
拒收： qty 必须为正数
```

这个 `Positive` 是**可复用的校验字段**——`property` 每个属性要写一份，描述符写一次到处用。`__set_name__` 在类创建时把属性名传进来，描述符因此知道自己保管的是哪个键。

> [!why] 这就是 ORM 字段的原理
> `Column("qty")` 这类 ORM 字段、`pydantic` 的字段校验，核心都是 `__set_name__` + `__set__`。理解描述符后，这些框架不再是魔法。

```quiz
question = "实例属性、非数据描述符、数据描述符、`__getattr__` 的查找优先级是？"
options = [
  "实例属性 > 数据描述符 > 非数据描述符 > __getattr__",
  "数据描述符 > 实例属性 > 非数据描述符 > __getattr__",
  "非数据描述符 > 数据描述符 > 实例属性 > __getattr__",
  "四者优先级相同，按定义顺序"
]
answer = 1
explain = "数据描述符最高（它可能校验/缓存，必须拦在实例字典之前），其次实例字典，再非数据描述符，最后才是 __getattr__ 兜底。property 是数据描述符，函数是非数据描述符。"
```

## 小结

- 有 `__get__` 是描述符；再加 `__set__` 是数据描述符。
- 方法绑定 = 函数的 `__get__` 返回 method，`self` 由此而来。
- 数据描述符优先于实例字典，所以能拦截赋值。
- `__set_name__` 让描述符知道属性名，从而可复用（校验字段、ORM 列）。
