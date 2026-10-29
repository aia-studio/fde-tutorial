+++
id = "s0-13-comprehensions"
order = 13
stage = "s0"
official_group = "beginner"
title = "推导式与生成器表达式"
concepts = ["comprehension", "generator expression", "lazy", "filter", "nesting"]
prereq = [12]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 5.1.3：列表推导式"
url = "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions"

[[doc_refs]]
title = "Language Reference §6.2.5：推导式"
url = "https://docs.python.org/3/reference/expressions.html#displays-for-lists-sets-and-dictionaries"
+++

# 一行建一个容器

推导式不是"炫技语法"，它是**把一个循环 + 一次 append 压成表达式**。认得出这个模式，代码能短一半；滥用它，可读性会崩。判断标准很简单：一行放得下、且读起来像一句话。

## 三种推导式

```python
nums = [1, 2, 3, 4, 5]

squares = [n * n for n in nums]
evens = [n for n in nums if n % 2 == 0]

print(squares)
print(evens)
```

```expect
[1, 4, 9, 16, 25]
[2, 4]
```

字典和集合的写法只差括号：

```python
words = ["a", "bb", "ccc"]

lengths = {w: len(w) for w in words}
unique_lengths = {len(w) for w in words}

print(lengths)
print(sorted(unique_lengths))
```

```expect
{'a': 1, 'bb': 2, 'ccc': 3}
[1, 2, 3]
```

`{...}` 里带冒号是字典推导，不带是集合推导。两种都只能写一个表达式，不能塞语句。

## 条件写在两个位置，含义不同

```python
nums = [1, 2, 3, 4]

print([n if n % 2 == 0 else 0 for n in nums])
print([n for n in nums if n % 2 == 0])
```

```expect
[0, 2, 0, 4]
[2, 4]
```

- 条件在 `for` **前面**：是三元表达式，每个元素都要产出，只是产出什么由条件决定。
- 条件在 `for` **后面**：是过滤，不满足的元素直接丢掉。

这个区别很多人写错，结果列表长度不对。

## 生成器表达式：不建列表

```python
gen = (n * n for n in range(5))

print(type(gen).__name__)
print(list(gen))
print(list(gen))
```

```expect
generator
[0, 1, 4, 9, 16]
[]
```

方括号换成圆括号，得到的是**生成器**：惰性求值、只可遍历一次、不占内存。第二次 `list(gen)` 是空的，因为迭代器已经耗尽。

数据量大、或者只需要遍历一次时（`sum(...)`、`any(...)`），生成器表达式比列表推导省得多：

```python
total = sum(n * n for n in range(1000))
print(total)
print(sum(n * n for n in range(1000)) == sum([n * n for n in range(1000)]))
```

```expect
332833500
True
```

## 嵌套：从左到右读

```python
matrix = [[1, 2], [3, 4]]
flat = [n for row in matrix for n in row]
print(flat)
```

```expect
[1, 2, 3, 4]
```

读法是"对于 matrix 里的每个 row，对于 row 里的每个 n，产出 n"——**顺序与嵌套 for 循环完全一致**。写成 `[n for n in row for row in matrix]` 会直接报错，因为 `row` 还没定义。

> [!warn] 两层以上就该换写法
> `[f(x) for a in A for b in B if ... for c in C]` 这种东西，读的人要在脑子里跑一遍解释器。超过两层嵌套，用普通循环更负责任。

```quiz
question = "`[n for n in range(6) if n % 2]` 的结果是？"
options = ["[0, 2, 4]", "[1, 3, 5]", "[1, 3, 5, 6]", "报错"]
answer = 1
explain = "条件是 `n % 2`，奇数取余为 1（真），偶数取余为 0（假）。所以只保留 1、3、5。"
```

## 小结

- 推导式 = 循环 + 产出，一行一个表达式。
- 条件在 `for` 前是三元（全产出），在 `for` 后是过滤（可丢弃）。
- 圆括号得到生成器：惰性、单次、省内存。
- 嵌套顺序与普通 for 循环一致，超过两层建议改回循环。
