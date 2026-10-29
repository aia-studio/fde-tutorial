+++
id = "s0-12-loops"
order = 12
stage = "s0"
official_group = "beginner"
title = "循环与循环控制"
concepts = ["for", "while", "range", "break", "continue", "loop-else"]
prereq = [11]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 4.2：for 语句"
url = "https://docs.python.org/3/tutorial/controlflow.html#for-statements"

[[doc_refs]]
title = "Tutorial 4.4：break 与 continue"
url = "https://docs.python.org/3/tutorial/controlflow.html#break-and-continue-statements"
+++

# for 遍历的是东西，不是计数器

Python 的 `for` 和 C 的 `for` 不是一回事。它遍历的是**可迭代对象**——列表、字符串、文件、生成器都行。需要下标时才用 `range`，而多数时候你并不需要下标。

## for 与 range

```python
for i in range(3):
    print(i)

print(list(range(1, 10, 3)))
print(list(range(5, 0, -2)))
```

```expect
0
1
2
[1, 4, 7]
[5, 3, 1]
```

`range(start, stop, step)` 同样**含头不含尾**。`range(3)` 是 `0, 1, 2`，不含 3。

遍历容器本身，比遍历下标更直接：

```python
fruits = ["apple", "banana"]

for fruit in fruits:
    print(fruit.upper())
```

```expect
APPLE
BANANA
```

需要下标时用 `enumerate`，别写 `for i in range(len(fruits))`——第 14 课会展开。

## while 与 break

```python
n = 1
while n < 100:
    n *= 2

print(n)
```

```expect
128
```

`while` 适合"不知道要循环几次"的场景。`break` 立刻跳出整个循环：

```python
for n in [2, 4, 7, 8]:
    if n % 2 == 1:
        print("第一个奇数：", n)
        break
```

```expect
第一个奇数： 7
```

`continue` 只跳过本轮剩下的语句，继续下一轮：

```python
total = 0
for n in range(1, 6):
    if n % 2 == 0:
        continue
    total += n

print(total)
```

```expect
9
```

1、3、5 相加得 9，偶数被跳过。

## 循环的 else：没被 break 才执行

这是 Python 独有、也最常被忽略的语法：

```python
for n in [2, 4, 7]:
    if n % 2 == 1:
        print("发现奇数：", n)
        break
else:
    print("没有奇数")
```

```expect
发现奇数： 7
```

换一组全偶数的数据：

```python
for n in [2, 4, 6]:
    if n % 2 == 1:
        break
else:
    print("全是偶数")
```

```expect
全是偶数
```

`else` 在循环**正常走完**时执行，被 `break` 打断就不执行。它等价于"没找到"分支，比设一个 `found = False` 标志干净得多。

> [!tip] 读法：for ... else 读作「找……，没找到就……」
> 这个名字起得不好，很多人以为是"否则循环"，其实是"否则（没有 break）"。记住这一点就不会用错。

```quiz
question = "`for x in items: ... else: ...` 里的 else 什么时候执行？"
options = [
  "循环一次都没执行时",
  "循环被 break 打断时",
  "循环正常结束（没有被 break）时",
  "每次循环结束后都执行"
]
answer = 2
explain = "else 分支只在循环自然走完时执行；只要遇到 break，else 就被跳过。它表达的是「没找到」这条路径。"
```

## 小结

- `for` 遍历可迭代对象；`range` 含头不含尾，可指定步长与方向。
- `while` 用于循环次数未知的场景。
- `break` 跳出整个循环，`continue` 跳过本轮。
- `for/while ... else` 在"没有被 break"时执行，适合表达"没找到"。
