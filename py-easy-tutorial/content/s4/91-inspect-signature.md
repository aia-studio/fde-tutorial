+++
id = "s4-91-inspect-signature"
order = 91
stage = "s4"
official_group = "advanced"
title = "函数签名与 inspect"
concepts = ["inspect.signature", "bind", "parameter validation", "decorator transparency"]
prereq = [90]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：inspect"
url = "https://docs.python.org/3/library/inspect.html"

[[doc_refs]]
title = "Library Reference：Signature 对象"
url = "https://docs.python.org/3/library/inspect.html#inspect.Signature"
+++

# 读取并校验任何函数的签名

`inspect.signature` 把函数的参数表变成可操作的对象：名字、类型注解、默认值、kind（位置/关键字）。**验证装饰器、API 参数校验、自动生成文档**都建立在它上面。

## 读取签名

```python
import inspect


def transfer(amount: float, *, to: str, note: str = "") -> bool:
    return amount > 0


sig = inspect.signature(transfer)
print(list(sig.parameters))
print(sig.parameters["to"].kind.name)
print(sig.parameters["note"].default)
```

```expect
['amount', 'to', 'note']
KEYWORD_ONLY

```

## bind：不调用也能校验参数

```python
import inspect


def transfer(amount: float, *, to: str) -> str:
    return f"转账 {amount} 给 {to}"


sig = inspect.signature(transfer)

bound = sig.bind(50.5, to="Bob")
print(bound.arguments)

try:
    sig.bind(50.5, "Bob")
except TypeError as exc:
    print("校验失败：", exc)
```

```expect
{'amount': 50.5, 'to': 'Bob'}
校验失败： too many positional arguments
```

`bind` 把实参按签名规则匹配并校验——**缺参数、多余参数、重复赋值都在这里被抓**。这就是"参数校验装饰器"的核心：签名 bind 一遍，通过才调原函数。

## 验证装饰器：bind 的实战

```python
import functools
import inspect


def strict(fn):
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            ann = sig.parameters[name].annotation
            if ann is inspect.Parameter.empty:
                continue
            origin = getattr(ann, "__origin__", None)
            if origin is int or ann is int:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise TypeError(f"{name} 需要 int，得到 {type(value).__name__}")
        return fn(*bound.args, **bound.kwargs)

    return wrapper


@strict
def repeat(text: str, times: int = 1) -> str:
    return text * times


print(repeat("ab", 2))
try:
    repeat("ab", "2")
except TypeError as exc:
    print("拦截：", exc)
```

```expect
abab
拦截： times 需要 int，得到 str
```

注意 `"2"`（字符串）能在运行时被 `text * "2"` 接住吗？不能——会抛 TypeError，但错误信息是解释器层面的。`strict` 装饰器把错误变成**面向调用方的明确提示**。这个模式正是 pydantic / FastAPI 参数校验的简化版。

```quiz
question = "`sig.bind(*args, **kwargs)` 与直接调用函数相比，多了什么能力？"
options = [
  "bind 会执行函数并返回结果",
  "bind 只做参数匹配与校验，不执行函数体",
  "bind 可以绕过类型检查",
  "bind 会自动转换参数类型"
]
answer = 1
explain = "bind 按签名规则把实参映射成参数名→值的字典，缺参/多参/重复都会抛 TypeError。先 bind 再决定是否调用，是「验证装饰器」的实现核心。"
```

## 小结

- `signature(f)` 拿到参数名、kind、默认值、注解的完整描述。
- `bind`/`bind_partial` 做参数校验而不执行函数。
- `apply_defaults` 把默认值也补进 arguments。
- 验证装饰器 = bind 校验 + 按参数注解检查 + wraps 透传。
