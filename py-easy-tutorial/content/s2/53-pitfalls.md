+++
id = "s2-53-pitfalls"
order = 53
stage = "s2"
official_group = "moderate"
title = "十大陷阱合集"
concepts = ["pitfalls", "copy", "aliasing", "late binding", "integer cache"]
prereq = [52]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python FAQ：编程常见问题"
url = "https://docs.python.org/3/faq/programming.html"

[[doc_refs]]
title = "Library Reference：copy"
url = "https://docs.python.org/3/library/copy.html"
+++

# 这些坑，每个都会有人踩

前 52 课各自埋过一个"看起来对、跑起来错"的点。这一课把它们收拢成一张清单，配上最小复现代码——以后遇到诡异行为，先来这里对号入座。

## 深拷贝与浅拷贝

```python
import copy

grid = [[1, 2], [3, 4]]

shallow = grid.copy()
shallow[0][0] = 99
print(grid)

deep = copy.deepcopy(grid)
deep[0][0] = 0
print(grid)
```

```expect
[[99, 2], [3, 4]]
[[99, 2], [3, 4]]
```

`copy()` 只复制**最外层**，内层列表还是共享的，改浅拷贝会穿透。要完全独立用 `deepcopy`。判定方法：数据里有嵌套容器，就想想"我复制到第几层"。

## 闭包晚绑定

```python
funcs = [lambda: i for i in range(3)]
fixed = [lambda i=i: i for i in range(3)]

print([f() for f in funcs], [f() for f in fixed])
```

```expect
[2, 2, 2] [0, 1, 2]
```

闭包捕获变量不是值。循环里建回调、定时任务时必中，修法是 `lambda i=i: i` 固化当前值。

## `is` 不是 `==`

```python
x = [1, 2]
y = x.copy()
print(x == y, x is y)

c = x
c.clear()
print(x)
```

```expect
True False
[]
```

`==` 比内容、`is` 比身份。`c = x` 之后 `c.clear()` 把两个名字指向的列表清空——共享可变对象时，任何"删除"都是全局的。

整数还有个小整数缓存（`-5..256` 内 `is` 恒真），让人误以为 `is` 能比数值——那是实现细节，不是语言保证。

## 其余七个，一句话版

| 陷阱 | 一句话 | 详见 |
|---|---|---|
| 可变默认参数 | `def f(x, items=[])` 全调用共享 | 第 15 课 |
| 循环里的 `else` 语义 | 没被 break 才执行 | 第 12 课 |
| `groupby` 不排序 | 只对相邻项分组 | 第 42 课 |
| `except Exception: pass` | 吞掉一切包括拼写错误 | 第 25 课 |
| 字符串逐字符拼接 | O(n²)，用 `"".join(parts)` | 第 6 课 |
| `lru_cache` 缓存有副作用函数 | 相同参数返回过期数据 | 第 43 课 |
| `datetime.utcnow()` | 返回 naive 时间，3.12 起弃用 | 第 51 课 |

每一条在对应课程里都有完整的最小复现。这个合集的价值是**当变量**：排查问题时先扫一遍清单，命中率比想象高。

```quiz
question = "下面哪个写法**没有**踩到本课列出的陷阱？"
options = [
  "def add(x, box=[]): box.append(x)",
  "callbacks = [lambda: flag for _ in range(3)]",
  "grid2 = copy.deepcopy(grid)",
  "for i in range(len(items)): print(items[i])"
]
answer = 2
explain = "deepcopy 正是深拷贝的正确用法。A 是可变默认参数；B 是闭包晚绑定；D 能跑但风格差（应该 for item in items 或 enumerate），不算踩坑但也不 Pythonic。"
```

## 小结

- 深浅拷贝的差别在嵌套层；有嵌套容器就考虑 `deepcopy`。
- 闭包捕获变量不捕获值，循环里建函数用默认参数固化。
- `==` / `is` / 真值 三种判断不可混用。
- 把这十种症状记熟，排查"诡异行为"能省一半时间。
