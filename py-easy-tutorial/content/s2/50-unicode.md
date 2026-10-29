+++
id = "s2-50-unicode"
order = 50
stage = "s2"
official_group = "moderate"
title = "文本与 Unicode"
concepts = ["unicode", "NFC", "casefold", "textwrap", "combining"]
prereq = [49]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：unicodedata"
url = "https://docs.python.org/3/library/unicodedata.html"

[[doc_refs]]
title = "Library Reference：textwrap"
url = "https://docs.python.org/3/library/textwrap.html"
+++

# 看起来相同，可能不是同一个字符串

两个"长相一样"的字符串 `==` 却是 False，这是 Unicode 的深坑：**同一个字形可以由不同的码点序列组成**。处理用户输入、文件名、搜索时不知道这一点，迟早踩到。

## 组合字符：两种写法的 é

```python
import unicodedata

s1 = "café"
s2 = "cafe\u0301"

print(len(s1), len(s2))
print(s1 == s2)
print(unicodedata.normalize("NFC", s2) == s1)
```

```expect
4 5
False
True
```

`s1` 的 é 是**一个码点**（U+00E9）；`s2` 是 `e` 加上**组合重音符**（U+0301），5 个码点。显示完全一样，但字符串不同——文件名、数据库唯一键、哈希都会当作两个东西。

`unicodedata.normalize("NFC", s)` 把组合序列合并成单个码点（NFD 反向拆开）。**用户输入入库前先 NFC 归一化**，是防止"同名不同人"的标准做法。

## 大小写：`lower` 不够用

```python
print("Straße".casefold() == "strasse")
print("Straße".lower() == "strasse")
```

```expect
True
False
```

德语 ß 的大写形式是 SS，`lower()` 处理不了这种"一对多"映射，`casefold()` 专门为**无大小写比较**设计。做搜索、用户名去重，用 `casefold()` 而不是 `lower()`。

## textwrap：折行与缩略

```python
import textwrap

print(textwrap.fill("a" * 25, width=10))
print(textwrap.wrap("a" * 25, width=10))
```

```expect
aaaaaaaaaa
aaaaaaaaaa
aaaaa
['aaaaaaaaaa', 'aaaaaaaaaa', 'aaaaa']
```

`fill` 就是 `"\n".join(wrap(...))`，两者永远一致。另一种需求是截断：`textwrap.shorten("a b c d e f", width=8, placeholder="…")` 得到 "a b c…"，长摘要转短摘要用它。

> [!tip] 字符 ≠ 显示宽度
> `"中文"` 是 2 个字符，但终端占 4 格；组合字符让"5 个字符"看起来像 4 个。做表格对齐时按显示宽度算（`unicodedata.east_asian_width` 可以判断），按字符数算必然错位。

```quiz
question = "两个用户输入的昵称“看起来一样”，但判断相等是 False，最可能的原因是？"
options = [
  "其中一个多了隐藏的换行",
  "两者码点序列不同（组合字符 vs 预组合字符）",
  "Python 的字符串比较有随机性",
  "编码是 UTF-16 导致的"
]
answer = 1
explain = "é 可以是一个码点也可以是 e+组合符，显示相同但序列不同。用 unicodedata.normalize('NFC', s) 归一化后再比较即可。"
```

## 小结

- 同一字形可有不同码点序列，`==` 是逐码点比较。
- 入库/做键之前先 `unicodedata.normalize("NFC", s)`。
- 无大小写比较用 `casefold()`。
- 字符数 ≠ 显示宽度，对齐按显示宽度算。
