+++
id = "s1-15-functions"
order = 15
stage = "s1"
official_group = "beginner"
title = "函数与参数"
concepts = ["function", "default argument", "args", "kwargs", "keyword-only"]
prereq = [14]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 4.8：定义函数"
url = "https://docs.python.org/3/tutorial/controlflow.html#defining-functions"

[[doc_refs]]
title = "Tutorial 4.9：参数组合"
url = "https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions"
+++

# 参数的四种形态

Python 的函数签名能表达的信息比多数语言多：位置参数、默认值、可变位置、可变关键字、仅关键字参数。代价是有一套容易踩的规则，尤其是**默认参数只求值一次**这条。

## 默认参数与关键字传参

```python
def greet(name, greeting="你好"):
    return f"{greeting}，{name}"


print(greet("Ada"))
print(greet("Ada", greeting="hi"))
print(greet(greeting="hi", name="Bob"))
```

```expect
你好，Ada
hi，Ada
hi，Bob
```

关键字传参让调用处自解释。参数一多，这个习惯能省掉大量查签名的时间。

## `*args` 与 `**kwargs`

```python
def show(*args, **kwargs):
    print(args)
    print(sorted(kwargs.items()))


show(1, 2, a=3, b=4)
```

```expect
(1, 2)
[('a', 3), ('b', 4)]
```

`args` 是位置参数打包成的元组，`kwargs` 是关键字参数打包成的字典。名字可以改，`*` 和 `**` 才是语法。

## 那个著名的默认参数陷阱

```python
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket


print(add_item("a"))
print(add_item("b"))
```

```expect
['a']
['a', 'b']
```

第二次调用没有传 `bucket`，却拿到了上次的列表。原因是**默认值在函数定义时求值一次**，之后每次调用都复用同一个对象。

正确写法是用 `None` 当哨兵：

```python
def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket


print(add_item("a"))
print(add_item("b"))
```

```expect
['a']
['b']
```

> [!warn] 这条规则对所有可变默认值都成立
> `def f(x, cache={})`、`def f(x, seen=set())` 都是同一个坑。只有不可变默认值（数字、字符串、元组、`None`）才安全。

## 仅关键字参数

`*` 单独出现时，表示"后面的参数只能用关键字传"：

```python
def area(width, height, *, unit="cm"):
    return f"{width * height} {unit}²"


print(area(3, 4))
print(area(3, 4, unit="m"))
```

```expect
12 cm²
12 m²
```

这对**布尔开关**特别有用：`open(path, "w", True)` 看不出 True 是什么，`sorted(data, reverse=True)` 一眼就懂。

```quiz
question = "下面哪个默认值是安全的？"
options = [
  "def f(x, cache={})",
  "def f(x, seen=set())",
  "def f(x, items=[])",
  "def f(x, tag=None)"
]
answer = 3
explain = "只有不可变默认值安全。字典、集合、列表在函数定义时创建一次，所有调用共享同一个对象，会互相污染。"
```

```exercise
id = "s1-15-ex1"
title = "把数值夹在区间里"
prompt = "实现 `clamp(value, low=0, high=100)`：小于 low 返回 low，大于 high 返回 high，否则原样返回。"
starter = """
def clamp(value, low=0, high=100):
    # 在这里实现
    pass
"""
solution = """
def clamp(value, low=0, high=100):
    if value < low:
        return low
    if value > high:
        return high
    return value
"""
tests = [
  "assert clamp(50) == 50, '区间内应原样返回'",
  "assert clamp(150) == 100, '超过上限应返回 high'",
  "assert clamp(-5) == 0, '低于下限应返回 low'",
  "assert clamp(5, low=10) == 10, '自定义下限也要生效'"
]
hints = [
  "用两个 if 分别处理越界，最后兜底返回 value。",
  "注意 low/high 有默认值，调用时可以只覆盖其中一个。"
]
xp = 10
```

## 小结

- 默认参数在**定义时**求值一次，可变默认值会跨调用共享。
- 用 `None` 当哨兵，在函数体内创建新的可变对象。
- `*args` 收位置参数，`**kwargs` 收关键字参数。
- `*` 之后的参数只能关键字传，适合布尔开关。
