+++
id = "s2-49-regex"
order = 49
stage = "s2"
official_group = "moderate"
title = "正则表达式"
concepts = ["re", "findall", "groups", "greedy", "sub"]
prereq = [48]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：re"
url = "https://docs.python.org/3/library/re.html"

[[doc_refs]]
title = "HOWTO：正则表达式"
url = "https://docs.python.org/3/howto/regex.html"
+++

# 一把快刀，但刀刃向内

正则能一行解决文本提取，也能一行制造没人看得懂的代码。这一课只讲**日常 80% 场景**的用法，以及两个最容易翻车的点：贪婪和预编译。

## findall 与分组

```python
import re

text = "Ada 36, Bob 25"

print(re.findall(r"\d+", text))
print(re.findall(r"(\w+) (\d+)", text))
```

```expect
['36', '25']
[('Ada', '36'), ('Bob', '25')]
```

`\d+` 匹配数字串。加括号就是**分组**，`findall` 返回元组列表而不是字符串列表。命名分组更可读：

```python
import re

match = re.search(r"(?P<name>\w+)=(?P<value>\d+)", "port=5432")
print(match.group("name"), match.group("value"))
print(match.group(0))
```

```expect
port 5432
port=5432
```

`search` 找**第一个**匹配（没有则 None），`findall` 找全部，`fullmatch` 要求整串匹配——校验用户输入用 `fullmatch`，别用 `match`（它只锚定开头）。

## 贪婪：`.*` 的默认行为会坑你

```python
import re

html = "<a><b>"

print(re.findall(r"<.+>", html))
print(re.findall(r"<.+?>", html))
```

```expect
['<a><b>']
['<a>', '<b>']
```

`.*` 是**贪婪**的：能吃多少吃多少，一口气吞到行尾的 `>` 才回退。加 `?` 变成**非贪婪**：碰到第一个能结束的位置就停。这两行代码的差异，是正则 bug 排行榜的第一名。

> [!warn] 复杂解析不要用正则
> 嵌套结构（HTML、JSON）不是正则语言，`<div>` 套 `<div>` 的场景迟早出事。文本用正则，结构用解析器。

## `sub`：替换也带分组

```python
import re

print(re.sub(r"\s+", " ", "a  b\n c"))
print(re.sub(r"(\d{4})-(\d{2})", r"\2/\1", "2026-10"))
```

```expect
a b c
10/2026
```

替换串里 `\1`、`\2` 引用分组——日期重排这类转换一行完成。

## 预编译：同一个模式用两次就该编译

```python
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

text = "联系 a@x.com 或 b@y.org"
print(EMAIL.findall(text))
print(bool(EMAIL.fullmatch("c@z.io")))
```

```expect
['a@x.com', 'b@y.org']
True
```

模块级 `re.compile` 一次、复用多次；速度更快，模式有名字、离使用处远一点，可读性也更好。

```quiz
question = "校验用户输入的手机号格式，应该用哪个函数？"
options = [
  "re.match(pattern, text)",
  "re.search(pattern, text)",
  "re.fullmatch(pattern, text)",
  "re.findall(pattern, text)"
]
answer = 2
explain = "fullmatch 要求整个字符串匹配，末尾多余字符会导致失败——校验场景正需要这种严格性。match 只锚定开头，'13800138000abc' 也会通过。"
```

## 小结

- `search` 找第一个、`findall` 找全部、`fullmatch` 校验整串。
- 分组 `(...)` 捕获，`(?P<name>...)` 命名，替换用 `\1` 引用。
- `.*` 贪婪、`.*?` 非贪婪，90% 的正则 bug 在这里。
- 复用模式先 `re.compile`；解析结构化文本（HTML/JSON）不用正则。
