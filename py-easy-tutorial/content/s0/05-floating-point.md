+++
id = "s0-05-floating-point"
order = 5
stage = "s0"
official_group = "beginner"
title = "浮点数专题：0.1 + 0.2 为什么不是 0.3"
concepts = ["float", "ieee754", "isclose", "decimal", "rounding"]
prereq = [4]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 15：浮点数运算的局限"
url = "https://docs.python.org/3/tutorial/floatingpoint.html"

[[doc_refs]]
title = "Library Reference：math.isclose"
url = "https://docs.python.org/3/library/math.html#math.isclose"
+++

# 误差不在你的代码里，在二进制里

上一课看到 `0.1 + 0.2` 得到 `0.30000000000000004`。这一课把这件事拆到底：误差从哪来、什么时候可以忽略、什么时候必须换工具。

## 先看清误差有多大

```python
print(0.1 + 0.2)
print(f"{0.1 + 0.2:.17f}")
print(0.1 + 0.2 - 0.3)
```

```expect
0.30000000000000004
0.30000000000000004
5.551115123125783e-17
```

误差是 `5.5e-17`，也就是小数点后第 16 位。**这个量级对绝大多数计算毫无影响**——真正的问题是很多人用 `==` 去比较它。

## 比较浮点数：用 isclose，不要用 ==

```python
import math

a = 0.1 + 0.2
print(a == 0.3)
print(math.isclose(a, 0.3))
print(math.isclose(a, 0.3, rel_tol=0, abs_tol=1e-12))
```

```expect
False
True
True
```

`isclose` 默认用相对误差 `1e-09`。当数值本身接近 0 时相对误差会失效（除以 0），所以它还提供 `abs_tol` 兜底。这也是为什么"自己写 `abs(a-b) < 1e-9`"往往是错的——对 `1e-12` 这种数值，绝对误差阈值比数本身还大。

> [!warn] 排序和去重也会被误差影响
> `sorted` 用的是 `<`，两个"理论上相等"的浮点数可能因为末位不同而排序结果不稳定。需要确定性时，先量化到固定小数位再比。

## 三个必须换工具的场景

| 场景 | 别用 | 用什么 |
|---|---|---|
| 金额、账目 | `float` | `decimal.Decimal`（从字符串构造） |
| 精确分数（1/3 这种） | `float` | `fractions.Fraction` |
| 判断两个浮点"差不多" | `==` | `math.isclose` |

```python
from decimal import Decimal
from fractions import Fraction

print(Decimal("0.1") + Decimal("0.2"))
print(Decimal("1.10") * Decimal("3"))
print(Fraction(1, 3) + Fraction(1, 6))
```

```expect
0.3
3.30
1/2
```

`Decimal` 会保留末尾的 0（`3.30`），这在账目里是有意义的——它表示精度到分。`Fraction` 保持分数形式，`1/3 + 1/6` 精确等于 `1/2`。

## 打印时怎么控制显示

```python
value = 1 / 3
print(value)
print(f"{value:.4f}")
print(format(value, ".2%"))
```

```expect
0.3333333333333333
0.3333
33.33%
```

格式化只影响**显示**，不改变存储的值。想要"存进去就是两位小数"，得用 `Decimal.quantize`，而不是格式化。

```quiz
question = "判断两个计算出来的浮点数是否相等，最稳妥的写法是？"
options = [
  "a == b",
  "abs(a - b) < 1e-9",
  "math.isclose(a, b)",
  "round(a, 9) == round(b, 9)"
]
answer = 2
explain = "isclose 同时考虑相对误差与绝对误差，能适应不同量级。固定阈值 1e-9 在数值很小时会误判为相等、在数值很大时又可能误判为不等；round 则在边界处仍可能翻转。"
```

## 小结

- 误差来自二进制表示，量级约 1e-16，正常计算可以忽略。
- 比较用 `math.isclose`，别用 `==`，也别自己拍一个固定阈值。
- 钱用 `Decimal`（从字符串构造），分数用 `Fraction`。
- 格式化只改显示，不改存储；要改精度用 `quantize`。
