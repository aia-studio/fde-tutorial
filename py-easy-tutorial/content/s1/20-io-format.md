+++
id = "s1-20-io-format"
order = 20
stage = "s1"
official_group = "beginner"
title = "输入输出与格式化"
concepts = ["print", "sep", "end", "fstring", "format spec", "repr"]
prereq = [18]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 7.1：格式化字符串字面量"
url = "https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals"

[[doc_refs]]
title = "Library Reference：格式规格迷你语言"
url = "https://docs.python.org/3/library/string.html#format-specification-mini-language"
+++

# 输出的三种控制：分隔、结尾、格式

`print` 的 `sep` 和 `end` 决定"怎么连"，f-string 的格式说明符决定"每个值怎么显示"。这两件事分清楚，输出就不会再靠手工拼空格对齐。

## `sep` 与 `end`

```python
print("a", "b", sep="-", end="!\n")
print("x", end="")
print("y")
```

```expect
a-b!
xy
```

`sep` 只在多个参数之间插入，`end` 决定本次输出怎么收尾。默认 `end="\n"`，所以第二行的 `print("x", end="")` 把换行去掉了，`y` 接在后面。

## 对齐与精度

```python
print(f"{3.14159:10.3f}|")
print(f"{'hi':>6}|")
print(f"{255:#06x}")
print(f"{0.5:.1%}")
```

```expect
     3.142|
    hi|
0x00ff
50.0%
```

格式说明符的通用形状是 `[[填充]对齐][符号][宽度][,][.精度][类型]`：

| 写法 | 含义 | 结果 |
|---|---|---|
| `10.3f` | 宽 10、保留 3 位小数 | `     3.142` |
| `>6` | 右对齐占 6 格 | `    hi` |
| `#06x` | 十六进制、补 `0x`、总宽 6 | `0x00ff` |
| `.1%` | 百分比、1 位小数 | `50.0%` |
| `,` | 千分位 | `1,234,567` |

```python
print(f"{1234567:,}")
print(f"{-42:+d}")
print(f"{'ok':^8}|")
```

```expect
1,234,567
-42
   ok   |
```

## `repr` 与 `str` 的区别

```python
text = "a\nb"

print(text)
print(repr(text))
print(f"{text!r}")
```

```expect
a
b
'a\nb'
'a\nb'
```

`str` 给人看（真的换行），`repr` 给开发者看（转义后的字面量）。调试时打印 `repr`，才能看清到底有没有隐藏字符——空格、制表符、换行、不可见 Unicode。

> [!tip] 调试三件套
> `print(repr(x))` 看真实内容，`print(type(x), len(x))` 看类型和长度，`print(f"{x=}")` 直接输出"变量名=值"，省掉手写标签。

```quiz
question = "`print('a', 'b', sep='', end='')` 之后紧接着 `print('c')`，屏幕上输出什么？"
options = ["a b\\nc", "ab\\nc", "abc", "a b c"]
answer = 1
explain = "sep='' 让 a 和 b 之间没有分隔符，end='' 让第一次 print 不换行；第二次 print('c') 结束时补上换行。所以屏幕上是 ab 紧接着 c，然后换行。"
```

## 小结

- `sep` 控制参数之间，`end` 控制本次结束，默认换行。
- 格式说明符 `[[填充]对齐][宽度][.精度][类型]`，对齐用 `<` `>` `^`。
- `,` 千分位、`+` 强制符号、`#` 加前缀，都能组合。
- 调试用 `repr`，`!r` 是 f-string 里的简写。
