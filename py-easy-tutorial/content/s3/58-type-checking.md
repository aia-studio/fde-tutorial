+++
id = "s3-58-type-checking"
order = 58
stage = "s3"
official_group = "moderate"
title = "类型检查实战"
concepts = ["mypy", "pyright", "strict", "type guard", "cast"]
prereq = [57]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：typing"
url = "https://docs.python.org/3/library/typing.html"

[[doc_refs]]
title = "mypy 文档"
url = "https://mypy.readthedocs.io/"
+++

# 检查器是另一个"读者"

注解本身不检查（第 46 课），检查是 mypy / pyright 的工作。这一课不装工具、不跑命令——用**眼力**读检查器的报错，把静态检查的思维方式建立起来。真实项目里只要加一条 CI 命令，这些眼力就会自动变成防线。

## 检查器抓什么

```python
def total(nums: list[int]) -> int:
    return sum(nums)


print(total([1, 2, 3]))
try:
    total("123")
except TypeError as exc:
    print("运行时：", exc)
```

```expect
6
运行时： unsupported operand type(s) for +: 'int' and 'str'
```

mypy 会报 incompatible type；而且这一次**运行时也真的炸了**——静态检查的价值是让你在运行之前就看到问题，而不是靠用户当测试员。

## Optional 的纪律

```python
def find(uid: int) -> str | None:
    return {1: "Ada"}.get(uid)


name = find(2)
try:
    print(name.upper())
except AttributeError as exc:
    print("运行时：", type(exc).__name__)
```

```expect
运行时： AttributeError
```

修法是把 None 分支写出来：

```python
def find(uid: int) -> str | None:
    return {1: "Ada"}.get(uid)


name = find(2)
if name is not None:
    print(name.upper())
else:
    print("查无此人")
```

```expect
查无此人
```

这个模式叫 **type narrowing（类型收窄）**：`is None` 判断之后，检查器知道分支里 `name` 一定是 `str`。第 10 课的"用 is 判断 None"在这里兑现了全部价值。

## cast：告诉检查器"我比你懂"

```python
from typing import cast


def load(raw: dict[str, object]) -> int:
    return cast(int, raw["count"]) + 1


print(load({"count": 0}))
```

```expect
1
```

`raw["count"]` 的静态类型是 `object`，直接加 1 会被拦。`cast(int, ...)` 是给检查器的**断言**，运行时就是一次普通表达式，零开销。它和 `assert isinstance(...)` 不同：后者是运行时验证，前者是纯声明。

> [!warn] cast 是签字画押
> cast 不会检查任何东西——类型错了检查器也信你。规则：cast 只能出现在"类型系统表达不了但你确知正确"的位置，每处 cast 都该有一行注释说明为什么安全。

## strict 模式与渐进策略

| 策略 | 做法 | 适合 |
|---|---|---|
| 宽松起步 | 默认模式，只查函数签名内的问题 | 存量代码 |
| 逐步收紧 | 对新文件开 strict（per-module 配置） | 团队渐进迁移 |
| 全面严格 | `strict = true`，未标注的函数也算错 | 新项目 |

新项目直接 `strict = true` 是最省事的路线：第一天就不欠债。

```quiz
question = "下面哪一处运行时会抛异常？"
options = [
  "total(\"123\")，total 声明接收 list[int]",
  "find(2).upper()，find 返回 str | None 且实际返回 None",
  "cast(int, raw['count']) 但 raw['count'] 是字符串",
  "以上都不会，除非运行时逻辑本身出错"
]
answer = 1
explain = "A 能跑（sum 可接收字符串），C 的 cast 是零开销声明，都只在静态检查时报错。B 中 None 上调 .upper() 是真正的 AttributeError——静态检查能提前抓到它。"
```

## 小结

- mypy/pyright 抓"参数类型与声明不符"和"None 上调属性"两类高价值问题。
- `is None` 收窄类型；`X | None` 返回值必须处理 None 分支。
- `cast` 是零开销断言，每处都要有理由。
- 新项目直接开 strict；存量项目按文件渐进。
