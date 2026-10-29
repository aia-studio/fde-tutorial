+++
id = "s0-14-builtins"
order = 14
stage = "s0"
official_group = "beginner"
title = "内置函数工具箱"
concepts = ["zip", "enumerate", "sorted", "any", "all", "sum"]
prereq = [13]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：内置函数"
url = "https://docs.python.org/3/library/functions.html"

[[doc_refs]]
title = "HOWTO：排序"
url = "https://docs.python.org/3/howto/sorting.html"
+++

# 十个函数，少写一半循环

这些函数不是"高级技巧"，是日常写代码的地基。认得它们，同一个逻辑就不用自己拿 `for` 拼。

## enumerate：同时拿下标和值

```python
names = ["Ada", "Bob", "Cara"]

for index, name in enumerate(names):
    print(index, name)

print(list(enumerate(names, start=1)))
```

```expect
0 Ada
1 Bob
2 Cara
[(1, 'Ada'), (2, 'Bob'), (3, 'Cara')]
```

`start=` 让编号从 1 开始，输出给人看时很常用。不要写 `for i in range(len(names))`——那样既慢又容易越界。

## zip：并排走

```python
names = ["Ada", "Bob", "Cara"]
ages = [36, 25, 41]

for name, age in zip(names, ages):
    print(f"{name} 今年 {age} 岁")

print(list(zip([1, 2, 3], "ab")))
```

```expect
Ada 今年 36 岁
Bob 今年 25 岁
Cara 今年 41 岁
[(1, 'a'), (2, 'b')]
```

`zip` 以**最短的那个**为准，多出来的直接丢掉——这是特性也是坑。要按最长的来，用 `itertools.zip_longest`（第 34 课）。

## sorted：key 才是重点

```python
people = [("Ada", 36), ("Bob", 25), ("Cara", 41)]

print(sorted(people, key=lambda p: p[1]))
print(sorted(people, key=lambda p: p[0], reverse=True))
```

```expect
[('Bob', 25), ('Ada', 36), ('Cara', 41)]
[('Cara', 41), ('Bob', 25), ('Ada', 36)]
```

`sorted` 返回新列表，`list.sort()` 原地改。`key` 接收一个函数，返回用来比较的值——**不要用它做变换**，它只影响排序依据。

多级排序靠元组：

```python
rows = [("b", 1), ("a", 2), ("a", 1)]
print(sorted(rows, key=lambda r: (r[0], r[1])))
```

```expect
[('a', 1), ('a', 2), ('b', 1)]
```

## any / all / sum / min / max

```python
nums = [2, 4, 6]

print(all(n % 2 == 0 for n in nums))
print(any(n > 5 for n in nums))
print(sum(nums), min(nums), max(nums))
```

```expect
True
True
12 2 6
```

`any` / `all` 接收可迭代对象，**短路求值**：`any` 遇到第一个真就停，`all` 遇到第一个假就停。所以传生成器表达式比先建列表更划算。

空集合的边界值得一提：

```python
print(all([]))
print(any([]))
```

```expect
True
False
```

`all([])` 是 `True`——"所有元素都满足"在空集上平凡成立。这个默认值经常让判断逻辑出错，写 `if all(...)` 时要想到空列表的情况。

```quiz
question = "`list(zip([1, 2, 3], ['a', 'b']))` 的结果是？"
options = [
  "[(1, 'a'), (2, 'b'), (3, None)]",
  "[(1, 'a'), (2, 'b')]",
  "报错：长度不一致",
  "[(1, 'a'), (2, 'b'), (None, 'c')]"
]
answer = 1
explain = "zip 以最短的可迭代对象为准，多出来的元素被丢弃，不会补 None。需要按最长对齐要用 itertools.zip_longest。"
```

```exercise
id = "s0-14-ex1"
title = "用 zip 对齐两个列表"
prompt = "给定 `names` 和 `scores`，生成 `pairs`：元素是 `(名字, 分数)` 的列表。"
starter = """
names = ["Ada", "Bob", "Cara"]
scores = [90, 85, 77]

# 在下面生成 pairs
"""
solution = """
names = ["Ada", "Bob", "Cara"]
scores = [90, 85, 77]

pairs = list(zip(names, scores))
"""
tests = [
  "assert isinstance(pairs, list), 'pairs 应该是列表'",
  "assert len(pairs) == 3, '长度应该是 3'",
  "assert pairs[0] == ('Ada', 90), '第一个元素应该是元组 (Ada, 90)'"
]
hints = [
  "`zip` 按位置把两个序列配对，得到 (名字, 分数) 的元组。",
  "`zip` 返回的是迭代器，不是列表——需要 `list(...)` 转换。",
  "完整写法：`pairs = list(zip(names, scores))`。"
]
xp = 10
```

## 小结

- `enumerate` 拿下标，`zip` 并行遍历（以最短为准）。
- `sorted(key=...)` 决定排序依据，多级排序返回元组。
- `any`/`all` 短路求值；`all([])` 是 `True`。
- 这些函数配合生成器表达式，能替掉大量手写循环。
