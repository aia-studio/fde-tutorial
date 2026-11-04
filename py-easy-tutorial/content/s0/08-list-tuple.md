+++
id = "s0-08-list-tuple"
order = 8
stage = "s0"
official_group = "beginner"
title = "列表与元组"
concepts = ["list", "tuple", "mutability", "aliasing", "unpacking"]
prereq = [7]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 5.1：列表的更多特性"
url = "https://docs.python.org/3/tutorial/datastructures.html#more-on-lists"

[[doc_refs]]
title = "Library Reference：序列类型"
url = "https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range"
+++

# 一个能改，一个不能改

`list` 和 `tuple` 长得像，用法也像，区别只有一条：**列表可变，元组不可变**。这一条差别决定了它们各自的用途，也制造了 Python 里最经典的一个陷阱。

## 列表的基本操作

```python
nums = [3, 1, 2]

nums.append(4)
nums.sort()
print(nums)
print(nums[1:3])
print(len(nums), sum(nums))
```

```expect
[1, 2, 3, 4]
[2, 3]
4 10
```

注意 `sort()` 是**原地排序**，返回 `None`：

```python
nums = [3, 1, 2]

result = nums.sort()
print(result)
print(nums)
```

```expect
None
[1, 2, 3]
```

写成 `nums = nums.sort()` 会让 `nums` 变成 `None`，这是新手最常见的错误之一。要新列表就用 `sorted(nums)`。

## 元组：不可变，所以能当键

```python
point = (3, 4)
x, y = point

print(x, y)
print(point[0])

try:
    point[0] = 9
except TypeError as exc:
    print(type(exc).__name__)
```

```expect
3 4
3
TypeError
```

元组最常见的用途不是"只读的列表"，而是**把几个值绑成一个整体**：坐标、数据库行、函数返回多个值。它可哈希，所以能当字典的键；列表不能。

## 那个著名的嵌套列表陷阱

```python
grid = [[0] * 2] * 2
grid[0][0] = 1
print(grid)
```

```expect
[[1, 0], [1, 0]]
```

只改了一个格子，两行都变了。因为 `[[0]*2] * 2` 复制的不是内层列表，而是**指向同一个内层列表的引用**。外层确实有两个元素，但它们指向同一个对象——和第 3 课的名字绑定是同一回事。

单步跑一遍，注意 `grid[0]` 和 `grid[1]` 旁边的色块是不是同一个：

```step
title = "单步看：为什么两行一起变了"
code = """
grid = [[0] * 2] * 2
grid[0][0] = 1
print(grid)
"""
```

正确写法是让每一行独立创建：

```python
grid = [[0] * 2 for _ in range(2)]
grid[0][0] = 1
print(grid)
```

```expect
[[1, 0], [0, 0]]
```

> [!warn] 凡是 `[x] * n` 都要停一下
> 如果 `x` 是不可变值（数字、字符串），复制没问题。如果 `x` 是列表、字典、集合这类可变对象，`* n` 得到的是 n 个指向同一对象的引用。推导式才是安全的建表方式。

```quiz
question = "`row = [0] * 3` 之后 `grid = [row] * 2`，再执行 `grid[1][0] = 9`，`grid[0][0]` 是多少？"
options = ["0", "9", "None", "报错"]
answer = 1
explain = "grid 的两个元素指向同一个 row 对象，改任何一个位置都是改同一个列表，所以两行同时变成 [9, 0, 0]。"
```

## 小结

- `list` 可变、`tuple` 不可变；`sort()` 原地改并返回 `None`。
- 元组适合打包多个值，且能当字典键。
- `[x] * n` 复制的是引用，嵌套可变对象必须用推导式。
- 解包 `a, b = pair` 是元组最常见的用法。
