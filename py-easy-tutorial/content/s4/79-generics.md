+++
id = "s4-79-generics"
order = 79
stage = "s4"
official_group = "advanced"
title = "泛型与型变"
concepts = ["generic class", "covariance", "contravariance", "Self", "bounds"]
prereq = [78]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "PEP 695：泛型语法"
url = "https://peps.python.org/pep-0695/"

[[doc_refs]]
title = "Library Reference：typing"
url = "https://docs.python.org/3/library/typing.html"
+++

# 容器的类型怎么"传下去"

`list[int]` 里的 `int` 是怎么生效的？泛型类自己声明类型参数，静态检查器据此追踪"放进去了什么、拿出来是什么"。这一课讲泛型类与**型变**——注解体系里最理论、也最容易写错的一段。

## 泛型类：PEP 695 语法

```python
class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()


s = Stack[int]()
s.push(1)
s.push("不是整数")
print(s.pop(), type(s.pop()).__name__)
```

```expect
不是整数 int
```

注意：运行时照常执行（"不是整数"也被塞进去），类型错误只被静态检查器报告。`Stack[int]()` 在运行时做的事是"标记"，真正的价值在 mypy/pyright 的输出里。

## 约束与有界类型

```python
class Comparable[T]:
    def __lt__(self, other: "Comparable[T]") -> bool: ...
    def __gt__(self, other: "Comparable[T]") -> bool: ...


def largest[T: Comparable](items: list[T]) -> T:
    return max(items)


print(largest([3, 1, 2]))
```

```expect
3
```

`T: Comparable` 是**有界类型变量**：要求 T 支持比较运算，`max` 才合法。没有界的话，检查器无法保证 `max` 能工作。

## 型变：容器之间的关系

```text
协变（covariant）  ：产出方。list[Dog] 可以当作 list[Animal] 用吗？→ 不可变序列可以。
逆变（contravariant）：消费方。接收 Animal 的函数，能接收 Dog 吗？→ 可以。
不变（invariant）  ：可读可写。list 是不变的——写入会破坏类型安全。
```

```python
class Animal: ...
class Dog(Animal): ...


def feed(animals: list[Animal]) -> None: ...
dogs: list[Dog] = [Dog()]

# mypy 会报错：list 是不变的，list[Dog] 不能当 list[Animal] 传
# 修正：把参数声明为「只读序列」
from collections.abc import Sequence

def feed_2(animals: Sequence[Animal]) -> None: ...
feed_2(dogs)
print("Sequence 是协变的，传 list[Dog] 合法")
```

```expect
Sequence 是协变的，传 list[Dog] 合法
```

规则一句话：**只读的容器可以协变（用 `Sequence`），可写的容器是不变的（`list`），函数参数是逆变的。** 声明接口时选对容器，类型系统才不会逼你到处 cast。

```quiz
question = "`def feed(animals: list[Animal])` 不能接收 `list[Dog]` 的根本原因是？"
options = [
  "Dog 和 Animal 不兼容",
  "list 可写：函数里可能 append 一只 Cat，破坏调用方的 list[Dog] 约定",
  "list 的实现不支持继承",
  "这是 mypy 的保守设计，与类型安全无关"
]
answer = 1
explain = "如果允许，函数内 animals.append(Cat()) 是合法的（Cat 也是 Animal），但调用方手里的 list[Dog] 里从此混入了 Cat。所以可写容器必须是「不变」的；只读场景用 Sequence（协变）即可。"
```

## 小结

- `class Stack[T]` 声明类型参数；静态检查追踪元素类型，运行时不拦截。
- `T: Bound` 要求类型变量具备某种能力（如可比较）。
- 只读容器协变（`Sequence`）、可写容器不变（`list`）、参数逆变。
- 容器选型（list vs Sequence）本身就是类型设计的一部分。
