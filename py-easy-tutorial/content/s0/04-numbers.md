+++
id = "s0-04-numbers"
order = 4
stage = "s0"
official_group = "beginner"
title = "数字与精度"
concepts = ["int", "float", "division", "modulo", "round", "decimal"]
prereq = [3]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 3.1.1：数字"
url = "https://docs.python.org/3/tutorial/introduction.html#numbers"

[[doc_refs]]
title = "Library Reference：内置类型 int / float"
url = "https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex"
+++

# 三种数字，两个除法，一个坑

Python 的数字类型不复杂：`int`、`float`、`complex`。真正让人栽跟头的是**两个除法符号**和**浮点数的表示误差**。这一课把它们一次说清。

## `/` 和 `//` 不是一回事

```python
print(7 / 2)
print(7 // 2)
print(-7 // 2)
print(7 % 3)
print(-7 % 3)
```

```expect
3.5
3
-4
1
2
```

前两行：`/` 永远返回 float，`//` 是**向下取整**，不是截断。所以 `-7 // 2` 是 `-4` 而不是 `-3`。

`%` 也跟着这个规则走：结果符号跟**除数**一致，所以 `-7 % 3` 是 `2`（因为 `-7 = 3 * (-3) + 2`）。习惯了 C 的截断语义的人，这里十有八九会算错。

```python
print(divmod(17, 5))
print(2**10)
print(2**100)
```

```expect
(3, 2)
1024
1267650600228229401496703205376
```

`divmod` 一次拿到商和余数。`int` 没有溢出概念——位数只受内存限制，`2**100` 就是精确值，不会像 C 那样变成 0。

## 浮点数：0.1 + 0.2 不等于 0.3

```python
print(0.1 + 0.2)
print((0.1 + 0.2) == 0.3)
```

```expect
0.30000000000000004
False
```

这不是 Python 的 bug，是 IEEE 754 二进制的必然结果：0.1 在二进制里是无限循环小数，存进 64 位就只能近似。两个近似值相加，误差落在最后几位上。

> [!why] 为什么显示成 0.30000000000000004
> Python 会选一个最短的字符串，使得它能唯一还原这个 float。真实的二进制值大约是 0.30000000000000004440892098500626。这不是"显示问题"，值本身就是这个。

下一课专门处理这件事。这里先记住一条：**只要涉及钱和精确比较，就别用 float。**

## 四舍五入也不是你想的那样

```python
print(round(2.5), round(3.5))
print(round(2.675, 2))
```

```expect
2 4
2.67
```

`round` 用的是**银行家舍入**（四舍六入五成双）：`.5` 时向偶数靠。所以 `round(2.5)` 是 2，`round(3.5)` 是 4。

第二行更反直觉：`2.675` 存成 float 后其实是 `2.67499999...`，所以在第二位就舍掉了。**对 float 谈"四舍五入到几位"本身就是不精确的。**

要精确，用 `Decimal`：

```python
from decimal import Decimal

print(Decimal("2.675").quantize(Decimal("0.01")))
print(Decimal("0.1") + Decimal("0.2"))
```

```expect
2.68
0.3
```

注意参数是**字符串** `"2.675"`。写成 `Decimal(2.675)` 会先把 float 的误差带进去，等于白用。

```quiz
question = "`-7 // 2` 的结果是？"
options = ["-3", "-3.5", "-4", "3"]
answer = 2
explain = "// 是向下取整（floor），不是向零截断。-7/2 = -3.5，向下取整得 -4。C 语言的整数除法才是截断，得 -3。"
```

## 小结

- `/` 总返回 float，`//` 向下取整，`%` 的符号跟除数。
- `int` 无溢出，位数只受内存限制。
- float 有二进制表示误差，`0.1 + 0.2 != 0.3` 是正常的。
- `round` 是银行家舍入，对 float 使用要格外小心。
- 要精确用 `Decimal("字符串")`，别把 float 传进去。
