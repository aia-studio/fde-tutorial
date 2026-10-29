+++
id = "s0-03-names-objects"
order = 3
stage = "s0"
official_group = "beginner"
title = "名字与对象：变量到底是什么"
concepts = ["variable", "binding", "reference", "id", "mutability"]
prereq = [2]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference §3.1：对象、值与类型"
url = "https://docs.python.org/3/reference/datamodel.html#objects-values-and-types"

[[doc_refs]]
title = "Tutorial 3.2：初探 Python"
url = "https://docs.python.org/3/tutorial/introduction.html"
+++

# 变量不是盒子，是标签

如果你从 C 或 Java 过来，"变量"这个词会带来一个错误的心理模型：盒子，里面装着值。Python 不是这样。**名字只是贴在对象上的标签**，赋值就是把标签揭下来贴到另一个对象上。这一课把这个模型钉死，后面讲可变对象、函数传参、默认参数陷阱时才不会反复摔跤。

## 两个名字，一个对象

```python
a = [1, 2]
b = a

b.append(3)
print(a)
print(a is b)
```

```expect
[1, 2, 3]
True
```

修改 `b` 却让 `a` 也变了，因为**根本没有两个列表**。`a` 和 `b` 是同一个对象的两个名字。`is` 判断的正是"是不是同一个对象"，而不是"长得一样不一样"。

想复制一份，得明确说要复制：

```step
title = "单步看：b = a 之后发生了什么"
code = """
a = [1, 2]
b = a
b.append(3)
print(a)
"""
```

```python
a = [1, 2]
c = a.copy()

print(a == c)
print(a is c)

c.append(3)
print(a)
```

```expect
True
False
[1, 2]
```

`==` 比较内容，`is` 比较身份。复制出来的列表内容相同、身份不同，所以改 `c` 不会影响 `a`。这两个符号混用是新手最常见的 bug 来源，第 10 课会专门拆开讲。

## 重新赋值 ≠ 修改对象

```python
x = 1
y = x
x = x + 1

print(x, y)
```

```expect
2 1
```

这里 `y` 没跟着变，因为 `x = x + 1` 做的是"算出一个新整数 2，把 x 这个标签贴过去"。整数不可变，所以**不可能**出现"改了 x 顺便改了 y"的情况。

对比上面两个列表的例子：

| 操作 | 发生了什么 | 其他名字受影响吗 |
|---|---|---|
| `b.append(3)` | 原地修改那个列表 | 会，因为共用同一个对象 |
| `x = x + 1` | 创建新对象并重新绑定 | 不会 |

一句话：**可变对象能原地改，不可变对象只能换新的。**

## 为什么这件事值得单独一课

因为函数传参就是这个模型：

```python
def add_item(items):
    items.append("新元素")


box = ["原有"]
add_item(box)
print(box)
```

```expect
['原有', '新元素']
```

参数 `items` 拿到的是同一个列表的另一个标签，不是副本。所以函数里的 `append` 会改到外面的 `box`。

> [!warn] 这是特性，不是缺陷
> "函数改了我的数据" 的抱怨，几乎都源于没意识到这一点。要么在函数里 `.copy()` 再改，要么干脆返回一个新对象——别指望 Python 替你复制。

```quiz
question = "执行 `a = [1, 2]` 后 `b = a`，再执行 `b += [3]`，此时 `a` 是什么？"
options = [
  "[1, 2]，因为 b 是新列表",
  "[1, 2, 3]，因为 a 和 b 指向同一个列表",
  "[3]，因为 += 会覆盖",
  "报错：列表不支持 +="
]
answer = 1
explain = "`b = a` 让两个名字指向同一个列表对象。`+=` 对列表是原地扩展（等价于 extend），所以 a 看到的也是 [1, 2, 3]。注意：`b = b + [3]` 才是创建新列表。"
```

## 小结

- 赋值是**绑定名字**，不是复制值。
- `is` 看身份，`==` 看内容；混用会出隐蔽 bug。
- 可变对象（list/dict/set）能原地改，不可变对象（int/str/tuple）只能换新的。
- 函数参数传的是对象引用，改不改得到外面，取决于对象可不可变。
