+++
id = "s0-11-conditionals"
order = 11
stage = "s0"
official_group = "beginner"
title = "条件与 match"
concepts = ["if", "elif", "match", "pattern matching", "walrus"]
prereq = [10]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 4.1：if 语句"
url = "https://docs.python.org/3/tutorial/controlflow.html#if-statements"

[[doc_refs]]
title = "Tutorial 4.6：match 语句"
url = "https://docs.python.org/3/tutorial/controlflow.html#match-statements"
+++

# 分支的两种写法

`if` 处理布尔条件，`match` 处理**结构**。两者不是替代关系——用 `match` 去代替一长串 `x == 1 or x == 2` 反而更绕。

## if / elif / else：只走一条

```python
def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    return "D"


for s in [95, 85, 72, 60]:
    print(s, grade(s))
```

```expect
95 A
85 B
72 C
60 D
```

`elif` 是"否则如果"，**命中一条就跳出整条链**。如果写成三个独立的 `if`，60 分会同时满足 `>=70` 之外的条件？不会，但 95 分会同时进入 `>=90` 和 `>=80` 两个分支——这就是 `elif` 存在的理由。

```python
score = 95

print("用 elif：")
if score >= 90:
    print(" A")
elif score >= 80:
    print(" B")

print("用独立 if：")
if score >= 90:
    print(" A")
if score >= 80:
    print(" B")
```

```expect
用 elif：
 A
用独立 if：
 A
 B
```

## match：匹配形状，不是匹配值

`match` 的强项是拆结构。看一个坐标点：

```python
def describe(point):
    match point:
        case (0, 0):
            return "原点"
        case (x, 0):
            return f"x 轴上，x={x}"
        case (0, y):
            return f"y 轴上，y={y}"
        case (x, y):
            return f"点 ({x}, {y})"


print(describe((0, 0)))
print(describe((3, 0)))
print(describe((2, 5)))
```

```expect
原点
x 轴上，x=3
点 (2, 5)
```

注意 `case (x, 0)` 里的 `x` 是**捕获变量**，不是常量。这是 `match` 最容易误读的地方：小写名字一律当"新变量"。

匹配类型 + 守卫条件：

```python
def classify(value):
    match value:
        case int() as n if n < 0:
            return "负整数"
        case int():
            return "非负整数"
        case str() as s if s:
            return f"非空字符串：{s}"
        case _:
            return "其他"


for v in [-3, 7, "hi", ""]:
    print(classify(v))
```

```expect
负整数
非负整数
非空字符串：hi
其他
```

`int()` 是类模式，表示"是 int 的实例"；`as n` 把匹配到的值绑到 `n`；`if n < 0` 是守卫，不满足就继续往下试；`_` 是兜底通配符。

> [!warn] match 不是 switch
> 它不会做"相等比较"。`case 1:` 用的是字面量模式（等价于 `== 1` 且类型匹配），但 `case x:` 是捕获，永远匹配成功——如果你想要常量比较，必须用带点的名字（`case Color.RED:`）或字面量。

## 海象运算符：在条件里赋值

```python
data = [1, 2, 3, 4]

if (n := len(data)) > 3:
    print(f"长度 {n}，超过 3")
```

```expect
长度 4，超过 3
```

`:=` 把"算出来"和"判断"合成一步，避免写两遍 `len(data)`。它最常见的场景正是 `while (line := f.readline()):` 这类循环。

```quiz
question = "`match` 语句里 `case (x, 0):` 中的 `x` 是什么？"
options = [
  "名为 x 的常量，要求值等于 x",
  "捕获变量，匹配任意值并绑定到 x",
  "类型注解，要求 x 是整数",
  "语法错误，必须写成 case (_, 0)"
]
answer = 1
explain = "match 的规则是：裸名字一律是捕获模式（irrefutable），会匹配任何值并绑定。要匹配常量必须用字面量、带点的限定名，或加守卫。"
```

## 小结

- `elif` 命中即跳出整条链；独立 `if` 会全部检查。
- `match` 匹配的是结构，裸名字是捕获而非比较。
- 类模式 `int()`、守卫 `if cond`、绑定 `as name`、兜底 `_` 是最常用的四件套。
- `:=` 适合"算一次、用两次"的场景。
