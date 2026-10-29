+++
id = "s2-46-typing-basics"
order = 46
stage = "s2"
official_group = "moderate"
title = "类型注解入门"
concepts = ["type hints", "annotations", "static typing", "list[int]"]
prereq = [44]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：typing"
url = "https://docs.python.org/3/library/typing.html"

[[doc_refs]]
title = "PEP 585：内置泛型"
url = "https://peps.python.org/pep-0585/"
+++

# 注解是写给"人 + 工具"的

类型注解**不影响运行**——写错了解释器照样执行。它服务的是两个"读者"：读代码的人（签名即文档），和静态检查器（mypy/pyright，在你运行之前抓 bug）。理解这一点，才不会期待注解去做它不做的事。

## 给函数加注解

```python
def total(nums: list[int], start: int = 0) -> int:
    return sum(nums, start)


print(total([1, 2], 10))
```

```expect
13
```

`list[int]` 是 3.9+ 的内置泛型写法，不用再从 typing 导入 `List`。参数在冒号后、返回值在 `->` 后。

## 注解是运行时可见的元数据

```python
def total(nums: list[int], start: int = 0) -> int:
    return sum(nums, start)


print(total.__annotations__)
```

```expect
{'nums': list[int], 'start': <class 'int'>, 'return': <class 'int'>}
```

注解存在 `__annotations__` 里，运行时可读——文档生成器、框架参数校验都靠它。但**解释器不做任何检查**：

```python
def double(x: int) -> int:
    return x * 2


print(double("ab"))
```

```expect
abab
```

`"ab" * 2` 合法，所以照常执行。注解不拦截，拦截是 mypy/pyright 在**编辑器和 CI 里**做的事。这个分工决定了两件事：类型标注是增量工程（可以逐步加），以及**运行时安全永远靠测试**。

## 变量与常见类型

```python
name: str = "Ada"
scores: dict[str, int] = {"math": 90}
maybe: int | None = None

print(name, scores["math"], maybe)
```

```expect
Ada 90 None
```

`int | None`（3.10+）表示"可能是 None"，读作"可空"。这是注解里最常见、也最有用的一种——它明确回答了"这个函数会不会返回 None"，无数 `AttributeError: NoneType` 都源于这里没写清楚。

> [!tip] 渐进式标注
> 不必一口气标全项目。顺序建议：公开 API → 复杂函数签名 → 内部实现。每标一个文件跑一次 `mypy --strict`（或 pyright），抓出的问题通常就是真 bug。

```quiz
question = "把参数标成 `x: int` 后传入字符串，运行时会发生什么？"
options = [
  "立即抛 TypeError",
  "静默通过，直到某个操作不兼容才报错",
  "自动转换成 int",
  "警告但不执行"
]
answer = 1
explain = "注解不做运行时检查，“x: int” 只是元数据。静态检查器会在编辑器里标红，但真正拦截错误需要把 mypy/pyright 加进 CI。"
```

## 小结

- 注解是元数据，运行时不检查、不转换、不拦截。
- 现代写法：`list[int]`、`dict[str, int]`、`int | None`。
- `X | None` 是最有价值的注解——它回答"会不会是 None"。
- 静态检查靠 mypy/pyright，运行时安全靠测试。
