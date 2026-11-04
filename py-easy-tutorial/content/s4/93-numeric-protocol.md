+++
id = "s4-93-numeric-protocol"
order = 93
stage = "s4"
official_group = "advanced"
title = "数值与运算符协议"
concepts = ["__radd__", "__iadd__", "__index__", "NotImplemented", "reflected"]
prereq = [91]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：模拟数字类型"
url = "https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types"

[[doc_refs]]
title = "PEP 3141：数字类型层次"
url = "https://peps.python.org/pep-3141/"
+++

# 3 + obj 时，Python 问谁

第 37 课实现了 `__add__`；这一课补全数值协议的另一半：**反射运算**（`__radd__`）、**原地运算**（`__iadd__`）和 `__index__`。三者合起来，自定义类才能无缝参与所有内置运算。

## 反射运算：`10 + obj`

```python
class Vector:
    def __init__(self, x):
        self.x = x

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Vector(self.x + other)
        if isinstance(other, Vector):
            return Vector(self.x + other.x)
        return NotImplemented

    __radd__ = __add__

    def __repr__(self):
        return f"Vector({self.x})"


print(Vector(1) + Vector(2))
print(Vector(1) + 10)
print(10 + Vector(1))
```

```expect
Vector(3)
Vector(11)
Vector(11)
```

第三行：`int.__add__` 不认识 Vector，返回 `NotImplemented` → Python 试 `Vector.__radd__(10)` → 成功。把 `__radd__ = __add__`（加法满足交换律时）是标准快捷写法。

## `__iadd__`：原地修改的运算

```python
class Accumulator:
    def __init__(self):
        self.total = 0

    def __iadd__(self, other):
        self.total += other
        return self


acc = Accumulator()
acc += 5
acc += 3
print(acc.total)
```

```expect
8
```

`acc += 5` 优先找 `__iadd__`（原地），没有则退回 `__add__` 再重新绑定。**可变类实现 `__iadd__` 要返回 self**；不可变类（如 tuple）只实现 `__add__`，`+=` 自动变成"新对象重新绑定"。

## `__index__`：当对象需要"当整数用"

```python
class Quantity:
    def __init__(self, n):
        self.n = n

    def __index__(self):
        return self.n


q = Quantity(1)
print([10, 20, 30][q])
print(["a", "b", "c"][q:])
```

```expect
20
['b', 'c']
```

切片、下标、`range`、`hex()` 都要求**真正的 int**。`__index__` 是对象"声明自己是整数语义"的方式——它比 `__int__` 更严格：`__int__` 允许有损转换（3.9 → 3），`__index__` 必须无损（q 必须能用同一个整数还原）。

> [!tip] NotImplemented 的完整流程
> `a + b` 的完整尝试顺序：`type(a).__add__(a, b)` → `type(b).__radd__(b, a)` → 都 NotImplemented 才抛 TypeError。两步都是为了让「左侧不认识，右侧认识」的混合运算能工作——`10 + Vector(1)` 就是靠第二步。

```quiz
question = "`10 + Vector(1)` 的求值顺序是？"
options = [
  "Vector.__radd__ 先执行，int.__add__ 不会执行",
  "先试 int.__add__，返回 NotImplemented 后再试 Vector.__radd__",
  "直接抛 TypeError",
  "由解释器自动转换 10 为 Vector"
]
answer = 1
explain = "完整顺序：左侧 __add__ →（若 NotImplemented）→ 右侧 __radd__ →（若仍 NotImplemented）→ TypeError。反射方法给「右操作数自己知道怎么算」的场景留了机会。"
```

## 小结

- `__radd__` 等反射方法处理"数值在左、对象在右"的混合运算。
- 可变类实现 `__iadd__` 返回 self；不可变类只用 `__add__`。
- `__index__` 让对象在需要 int 的位置（下标、切片）无损使用。
- 加法等交换运算可直接 `__radd__ = __add__`。
