+++
id = "s2-40-decorators"
order = 40
stage = "s2"
official_group = "moderate"
title = "装饰器基础"
concepts = ["decorator", "wraps", "higher-order function", "wrapper"]
prereq = [39]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：functools.wraps"
url = "https://docs.python.org/3/library/functools.html#functools.wraps"

[[doc_refs]]
title = "PEP 318：函数装饰器"
url = "https://peps.python.org/pep-0318/"
+++

# @ 语法只是函数调用的糖

`@deco` 上面一行等价于 `func = deco(func)`。装饰器接收一个函数，**返回一个新函数**（通常是包装了原函数的 wrapper）。就这么简单——复杂的是保持原函数的"身份"。

## 最小装饰器

```python
import functools


def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print("->", fn.__name__)
        result = fn(*args, **kwargs)
        print("<-", fn.__name__)
        return result

    return wrapper


@timed
def work(n):
    return n * 2


print(work(21))
print(work.__name__)
```

```expect
-> work
<- work
42
work
```

`wrapper` 用 `*args, **kwargs` 透传所有参数，所以它能包住任何签名的函数。装饰后的 `work` 其实是 `wrapper`——但因为 `@functools.wraps(fn)`，名字、docstring 都还是原函数的。

## 忘了 wraps 会怎样

```python
def bad(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


@bad
def work():
    return 1


print(work.__name__)
print(work.__doc__)
```

```expect
wrapper
None
```

函数名变成 `wrapper`，docstring 丢失。测试框架、文档生成器、日志器全都会被误导。**写装饰器必加 `functools.wraps`，没有例外。**

## 装饰器在导入时执行

```python
_registry = []


def register(fn):
    _registry.append(fn.__name__)
    return fn


@register
def handler_a():
    pass


@register
def handler_b():
    pass


print(_registry)
```

```expect
['handler_a', 'handler_b']
```

装饰发生在**函数定义时**（模块导入时），不是调用时。这个"定义期执行"的特性正是注册表模式的基础——第 89 课的插件系统全靠它。

> [!tip] 什么时候用装饰器
> 横切逻辑（计时、缓存、重试、权限检查）适合装饰器：每个函数都要、又不属于函数本职。让装饰器**委托给原函数**而不是自己实现业务——装饰器做包装，函数做事情。

```quiz
question = "`@deco` 上面一行等价于哪句代码？"
options = [
  "deco()",
  "func = deco(func)",
  "deco(func())",
  "func.__wrapped__ = deco"
]
answer = 1
explain = "装饰器语法只是函数调用的糖：把紧随其后的函数对象传给装饰器，再把返回值绑定回原名。所以装饰器必须返回可调用对象（或函数本身）。"
```

```exercise
id = "s2-40-ex1"
title = "写一个 @shout 装饰器"
prompt = "实现 `@shout`：被装饰的函数返回的字符串要变成**大写**，并在末尾加 `!`。要求保留原函数的 `__name__`。"
starter = """
import functools


def shout(fn):
    # 在这里包装
    pass


@shout
def hi(name):
    return "hi " + name
"""
solution = '''
import functools


def shout(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs).upper() + "!"
    return wrapper


@shout
def hi(name):
    return "hi " + name
'''
tests = [
  "assert hi('ada') == 'HI ADA!', '应该是大写并加感叹号'",
  "assert hi('bob') == 'HI BOB!', '参数要透传给原函数'",
  "assert hi.__name__ == 'hi', '必须用 functools.wraps 保留函数名'"
]
hints = [
  "wrapper 里拿到 fn 的返回值后再加工，最后 return。",
  "包装函数要接收并透传 *args, **kwargs。",
  "在 def wrapper 上面加 @functools.wraps(fn)。",
]
xp = 10
```

## 小结

- `@deco` ≡ `func = deco(func)`，装饰发生在定义时。
- wrapper 用 `*args, **kwargs` 透传，返回原函数的结果。
- **必加 `@functools.wraps(fn)`**，否则函数身份（名字、文档）丢失。
- 横切逻辑才用装饰器；装饰器做包装，函数做事情。
