+++
id = "s4-78-mro"
order = 78
stage = "s4"
official_group = "advanced"
title = "MRO 与多继承"
concepts = ["MRO", "C3", "diamond", "cooperative super", "mixin"]
prereq = [77]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：MRO"
url = "https://docs.python.org/3/howto/mro.html"

[[doc_refs]]
title = "Language Reference：确定方法解析顺序"
url = "https://docs.python.org/3/reference/datamodel.html#determining-the-method-resolution-order"
+++

# 多继承不是"从左到右找"

多个父类都有同名方法时，查找顺序由 **C3 线性化**决定，它保证：子类先于父类、父类保持声明顺序、同一类只出现一次。`__mro__` 把这个顺序摆在明面上。

## 菱形继承：只有一个 `__init__` 生效

```python
class Base:
    def __init__(self):
        print("Base 初始化")

class Left(Base):
    def __init__(self):
        print("Left 初始化")
        super().__init__()

class Right(Base):
    def __init__(self):
        print("Right 初始化")
        super().__init__()

class Child(Left, Right):
    def __init__(self):
        print("Child 初始化")
        super().__init__()


child = Child()
print([c.__name__ for c in Child.__mro__])
```

```expect
Child 初始化
Left 初始化
Right 初始化
Base 初始化
['Child', 'Left', 'Right', 'Base', 'object']
```

每个类**恰好初始化一次**——即使菱形结构里 Base 出现两条路径。这就是协作式 `super()` 的价值：它不是"调用父类"，而是"调用 MRO 里的下一个"。

## MRO 就是查找顺序

```python
class A:
    def hello(self):
        return "A"

class B(A):
    def hello(self):
        return "B"

class C(A):
    pass

class D(B, C):
    pass


print([c.__name__ for c in D.__mro__])
print(D().hello())
```

```expect
['D', 'B', 'C', 'A', 'object']
B
```

`D(B, C)`：B 在前，所以 `hello` 用 B 的。C3 保证顺序既满足子类优先、又满足你写下的声明顺序。

## 不可能的结构：C3 拒绝

```python
class X:
    pass

try:
    class Y(object, X):
        pass
except TypeError as exc:
    print("C3 拒绝：", "consistent" in str(exc))
```

```expect
C3 拒绝： True
```

`object` 本来就是 X 的基类，声明 `class Y(X, object)` 要求 object 排在 X 前面，与继承关系矛盾——C3 直接拒绝，**坏结构在定义时就被拦住**，不会等到运行中才乱。

> [!tip] Mixin 是多继承的正当用法
> 小而正交的功能类（如 `JSONMixin`、`ReprMixin`），通过协作式 `super()` 叠加到主类上。判断标准：Mixin 自己**不该被独立实例化**，只作为"能力插件"存在。MRO 里Mixin 位置放最后。

```quiz
question = "`super().__init__()` 的准确含义是？"
options = [
  "调用父类的 __init__",
  "调用 MRO 中当前类的下一个类的 __init__",
  "调用 object 的 __init__",
  "调用第一个基类的 __init__"
]
answer = 1
explain = "super() 依据「发起调用的类的 MRO」找下一个类，在菱形结构中这可能不是你字面上的父类。正因如此，每个 __init__ 都用 super()，链上每个类才恰好初始化一次。"
```

## 小结

- `__mro__` 是方法与属性的查找顺序，C3 计算并拒绝矛盾结构。
- 菱形继承下每个类只初始化一次——前提是全链都用 `super()`。
- 混写 `Base.__init__` 和 `super()` 会破坏链条（重复初始化）。
- 多继承的正当用法是 Mixin：小、正交、不独立实例化。
