+++
id = "s0-06-strings"
order = 6
stage = "s0"
official_group = "beginner"
title = "字符串：不可变序列"
concepts = ["str", "slicing", "fstring", "immutability", "split"]
prereq = [5]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 3.1.2：字符串"
url = "https://docs.python.org/3/tutorial/introduction.html#strings"

[[doc_refs]]
title = "Library Reference：文本序列类型 str"
url = "https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str"
+++

# 切片、方法、格式化

字符串是 Python 里最常用的类型，没有之一。它有两个性质决定了所有用法：**是序列**（能索引、能切片、能迭代），**不可变**（任何"修改"都产生新字符串）。

## 索引与切片

```python
s = "Python"

print(s[0], s[-1])
print(s[1:4])
print(s[::-1])
print(len(s))
```

```expect
P n
yth
nohtyP
6
```

切片是 `start:stop:step`，**含头不含尾**。`s[1:4]` 取下标 1、2、3。`s[::-1]` 是最常用的反转写法——step 为负时默认从尾到头。

负索引不是"从右边数第几个"的语法糖，它就是 `len(s) + i`，所以 `s[-1]` 是最后一个字符。

## 常用方法都是返回新字符串

```python
raw = "  Hello, World  "

print(raw.strip())
print(raw.strip().lower())
print(raw.strip().upper())
print(raw.strip().replace("World", "Python"))
print("a,b,c".split(","))
print("-".join(["a", "b", "c"]))
```

```expect
Hello, World
hello, world
HELLO, WORLD
Hello, Python
['a', 'b', 'c']
a-b-c
```

`split` 和 `join` 是一对：`join` 的分隔符在前，被拼接的列表在后，顺序别记反（`",".join(items)` 而不是 `items.join(",")`，后者在 Python 里不存在）。

## 不可变意味着什么

```python
s = "abc"

try:
    s[0] = "z"
except TypeError as exc:
    print(type(exc).__name__, exc)
```

```expect
TypeError 'str' object does not support item assignment
```

想"改"一个字符，只能拼一个新的：

```python
s = "abc"
s2 = s[:1] + "z" + s[2:]
print(s)
print(s2)
```

```expect
abc
azc
```

> [!why] 为什么不可变反而是优点
> 不可变对象可以安全地共享、可以作为 `dict` 的键、可以被缓存哈希值。第 9 课会看到：可变对象不能当键，正是因为哈希值会变。

## f-string 是默认选择

```python
name = "世界"
pi = 3.14159

print(f"你好，{name}！")
print(f"{pi:.2f}")
print(f"{42:>5}|")
print(f"{0.256:.1%}")
```

```expect
你好，世界！
3.14
   42|
25.6%
```

格式说明符跟在冒号后面：`.2f` 两位小数、`>5` 右对齐占 5 格、`.1%` 百分比一位小数。这套语法值得花十分钟翻一遍文档——`str.format()` 和 `%` 都属于"见得到但不必写"的旧写法。

```quiz
question = "`\"abcdef\"[1:4]` 的结果是？"
options = ["abcd", "bcd", "bcde", "bcdef"]
answer = 1
explain = "切片含头不含尾，取下标 1、2、3，即 b、c、d。要包含下标 4 得写 [1:5]。"
```

## 小结

- 字符串是序列：索引、切片、迭代都支持，切片含头不含尾。
- 所有"修改"方法都返回新字符串，原对象不变。
- `split` / `join` 配对使用，`join` 的调用者是分隔符。
- 格式化优先用 f-string，格式说明符写在冒号后。
