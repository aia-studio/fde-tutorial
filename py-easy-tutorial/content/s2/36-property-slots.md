+++
id = "s2-36-property-slots"
order = 36
stage = "s2"
official_group = "moderate"
title = "property 与 __slots__"
concepts = ["property", "setter", "slots", "attribute control"]
prereq = [35]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：property"
url = "https://docs.python.org/3/library/functions.html#property"

[[doc_refs]]
title = "Library Reference：__slots__"
url = "https://docs.python.org/3/reference/datamodel.html#slots"
+++

# 属性访问也能定制

`obj.value` 看起来是"读一个字段"，但 Python 允许它背后是计算、是校验、是缓存。`property` 让你**先写简单属性，需要时再无痛升级**——这是 Python 对 getter/setter 的回答。

## property：读的是计算结果

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius

    @property
    def area(self):
        return 3.14159 * self.radius ** 2


c = Circle(2)
print(round(c.area, 2))

c.radius = 3
print(round(c.area, 2))
```

```expect
12.57
28.27
```

`area` 不是存的字段，是**每次访问时算出来的**。调用处写 `c.area` 而不是 `c.area()`——调用方完全不知道它是方法。将来把存储结构从 radius 换成 diameter，调用方代码一行不用改。

## setter：赋值时校验

```python
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius

    @property
    def celsius(self):
        return self._c

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._c = value


t = Temperature(25)
print(t.celsius)

try:
    t.celsius = -300
except ValueError as exc:
    print("拒收：", exc)
```

```expect
25
拒收： 低于绝对零度
```

`__init__` 里那句 `self.celsius = celsius` 也会走 setter——所以校验从第一刻就生效。真实值存在 `_c` 里，下划线开头表示"内部字段"。

> [!tip] 先写裸属性，再升级
> 不要一上来就写 property。先 `self.x = value`，等真的需要校验/计算/缓存时再加 `@property`——接口不变，调用方无感。这是 Python 和 Java 的一个重要文化差异。

## `__slots__`：关掉实例字典

```python
class Point:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


p = Point(1, 2)
print(hasattr(p, "__dict__"))

try:
    p.z = 3
except AttributeError as exc:
    print(type(exc).__name__)
```

```expect
False
AttributeError
```

普通实例把属性存在 `__dict__` 里，灵活但占内存。`__slots__` 把属性固定为几个槽位：省内存（百万级实例差别明显）、访问稍快，代价是不能再动态加属性，也不能和某些需要 `__dict__` 的机制（如某些序列化方案）混用。

```python
class Slot:
    __slots__ = ("a",)

    def __init__(self):
        self.a = 1


s = Slot()
print(s.a)
```

```expect
1
```

```quiz
question = "`@property` 最大的价值是什么？"
options = [
  "让属性变成只读",
  "调用方不需要改代码，就能从「字段」升级成「计算/校验」",
  "比方法调用快",
  "可以省掉 __init__"
]
answer = 1
explain = "property 的核心是接口稳定：调用处始终写 obj.area，实现从字段换成计算，不影响任何调用方。它是把「实现细节」藏起来的工具。"
```

## 小结

- `@property` 让方法看起来像字段，读的是计算结果。
- `@x.setter` 挂校验逻辑，`__init__` 里的赋值也会走它。
- 先写裸属性，需要时再加 property，调用方无感。
- `__slots__` 换取内存与速度，代价是失去动态属性。
