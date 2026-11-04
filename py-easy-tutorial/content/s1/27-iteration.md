+++
id = "s1-27-iteration"
order = 27
stage = "s1"
official_group = "moderate"
title = "迭代协议"
concepts = ["iter", "next", "StopIteration", "__iter__", "__next__", "iterator"]
prereq = [26]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 9.8：迭代器"
url = "https://docs.python.org/3/tutorial/classes.html#iterators"

[[doc_refs]]
title = "Language Reference：迭代器类型"
url = "https://docs.python.org/3/library/stdtypes.html#iterator-types"
+++

# `for` 到底做了什么

`for x in obj` 背后只有两步：先 `iter(obj)` 拿迭代器，再反复 `next()` 直到 `StopIteration`。理解这两步，你就能让自己的类支持 `for`、`in`、`list()`、`sum()`。

## 手写一个迭代器

```python
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


print(list(Countdown(3)))
print(sum(Countdown(4)))
```

```expect
[3, 2, 1]
10
```

要点：`__iter__` 返回**迭代器对象**（这里是自己），`__next__` 每次返回一个值，取完了必须 `raise StopIteration`——`for` 靠这个异常知道该停了。

## 可迭代对象 ≠ 迭代器

```python
data = [1, 2, 3]
it = iter(data)

print(iter(it) is it)
print(iter(data) is data)
```

```expect
True
False
```

- **可迭代对象**（list、str、dict）有 `__iter__`，每次调用产生一个**新的**迭代器。
- **迭代器**（`iter(list)` 的结果）同时有 `__iter__` 和 `__next__`，且 `__iter__` 返回自己。

所以列表能被反复遍历，而迭代器只能走一遍：

```python
nums = iter([1, 2])
print(next(nums), next(nums))

try:
    next(nums)
except StopIteration:
    print("耗尽")
```

```expect
1 2
耗尽
```

> [!warn] 迭代器用完就没了
> 传迭代器给函数要小心：函数内部消耗掉之后，外面再遍历就是空的。需要多次遍历时传列表，或者在函数里先 `list()` 物化——但要权衡内存。

```quiz
question = "一个类要实现 `for x in obj`，最少需要哪两个方法？"
options = [
  "__len__ 和 __getitem__",
  "__iter__ 和 __next__",
  "__enter__ 和 __exit__",
  "__init__ 和 __call__"
]
answer = 1
explain = "for 先调用 iter(obj) 得到迭代器（__iter__），再反复调用 __next__ 直到 StopIteration。只实现 __getitem__ 的老式协议也还能用，但已不推荐。"
```

```exercise
id = "s1-27-ex1"
title = "实现偶数迭代器"
prompt = "实现 `evens(limit)`：返回一个可迭代对象，依次产出 `0, 2, 4, ...` 直到小于 `limit`。"
starter = """
def evens(limit):
    # 返回一个可迭代对象
    pass
"""
solution = """
def evens(limit):
    return (n for n in range(0, limit, 2))
"""
tests = [
  "assert list(evens(6)) == [0, 2, 4], '0 到 5 之间的偶数'",
  "assert list(evens(1)) == [0], '0 小于 1，所以有一个元素'",
  "assert sum(evens(10)) == 20, '0+2+4+6+8'",
  "assert list(evens(2)) == [0], '不含上限本身'"
]
hints = [
  "range 支持步长：range(0, limit, 2)。",
  "返回生成器表达式即可满足「可迭代对象」的要求。",
  "也可以写一个带 yield 的函数。"
]
xp = 10
```

## 小结

- `for` = `iter()` + 反复 `next()` + 捕获 `StopIteration`。
- 可迭代对象的 `__iter__` 每次返回新迭代器；迭代器的 `__iter__` 返回自己。
- 迭代器只能遍历一次，耗尽后再取就是 `StopIteration`。
- 自定义迭代器要实现 `__iter__` 和 `__next__`。
