+++
id = "s2-41-decorators-advanced"
order = 41
stage = "s2"
official_group = "moderate"
title = "装饰器进阶"
concepts = ["decorator factory", "registration", "class decorator", "stacking"]
prereq = [40]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：functools"
url = "https://docs.python.org/3/library/functools.html"

[[doc_refs]]
title = "HOWTO：装饰器入门"
url = "https://docs.python.org/3/howto/descriptor.html#functions-and-methods"
+++

# 三层结构：带参数的装饰器

`@repeat(3)` 比基础版多一层：`repeat(3)` 先执行，返回真正的装饰器。理解"装饰器可以是**返回装饰器的函数**"，这条语法就通了。

## 带参数的装饰器

```python
import functools


def repeat(times):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return [fn(*args, **kwargs) for _ in range(times)]

        return wrapper

    return deco


@repeat(3)
def beep(i):
    return f"beep {i}"


print(beep(1))
```

```expect
['beep 1', 'beep 1', 'beep 1']
```

读法：`@repeat(3)` → 先调 `repeat(3)` 得到 `deco` → 再 `beep = deco(beep)`。三层各司其职：`times` 存参数、`deco` 收函数、`wrapper` 干活。

## 注册表：装饰器的另一面

```python
_registry = {}


def register(name):
    def deco(fn):
        _registry[name] = fn
        return fn

    return deco


@register("greet")
def greet():
    return "hi"


@register("bye")
def bye():
    return "bye"


print(sorted(_registry))
print(_registry["bye"]())
```

```expect
['bye', 'greet']
bye
```

注意 `deco` **返回的是原函数**，没有包装——这类装饰器不做行为改造，只做"登记"。命令路由、插件发现、测试收集全是这个模式的变体。

## 叠加顺序：从下往上

```python
def add_a(fn):
    def wrapper():
        return "A" + fn()
    return wrapper


def add_b(fn):
    def wrapper():
        return "B" + fn()
    return wrapper


def base():
    return "C"


print(add_a(add_b(base))())
```

```expect
ABC
```

对应的装饰器写法是从下往上套：

```python
def add_a(fn):
    def wrapper():
        return "A" + fn()

    return wrapper


def add_b(fn):
    def wrapper():
        return "B" + fn()

    return wrapper


@add_a
@add_b
def base():
    return "C"


print(base())
```

```expect
ABC
```

`@add_a` 在上表示"最外层"，所以执行顺序是 add_a(add_b(base))。想清楚这个，就不会被多层装饰器绕晕。

```quiz
question = "带参装饰器 `@repeat(3)` 的调用顺序是？"
options = [
  "repeat 和 deco 同时收到参数与函数",
  "先调 repeat(3) 返回装饰器，再用它包装函数",
  "只调用 repeat 一次，直接完成包装",
  "repeat 会被调用三次"
]
answer = 1
explain = "带参装饰器是「装饰器工厂」：第一层收参数，第二层收函数，第三层是实际执行体。三层各司其职，忘了哪一层都会包错。"
```

## 小结

- 带参装饰器 = 装饰器工厂，三层结构：参数 → 函数 → wrapper。
- 注册类装饰器返回**原函数**，只登记不包装。
- 多个装饰器从下往上叠加，最上面的最外层执行。
- functools.wraps 每一层 wrapper 都要加。
