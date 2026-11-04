+++
id = "s1-21-files"
order = 21
stage = "s1"
official_group = "beginner"
title = "文件读写"
concepts = ["open", "with", "encoding", "readlines", "json"]
prereq = [20]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 7.2：读写文件"
url = "https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files"

[[doc_refs]]
title = "Library Reference：open()"
url = "https://docs.python.org/3/library/functions.html#open"
+++

# 打开的，一定要关

文件句柄是操作系统资源，用完不还会泄漏。Python 的 `with` 语句保证即使中途抛异常也会关闭——所以**只要是 `open`，就配 `with`**，几乎没有例外。

## 写与读

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n第二行\n")

with open("notes.txt", encoding="utf-8") as f:
    print(f.read())
```

```expect
第一行
第二行
```

`"w"` 会清空原文件再写，`"a"` 是追加。读写都要显式指定 `encoding="utf-8"`——虽然 3.15 默认就是 UTF-8，但写出来是给读代码的人看的，也让跨平台行为确定。

## 逐行读，不要一次全读进来

```python
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("a\nb\nc\n")

with open("data.txt", encoding="utf-8") as f:
    lines = [line.strip() for line in f]

print(lines)
print(len(lines))
```

```expect
['a', 'b', 'c']
3
```

文件对象本身可迭代，逐行读内存占用是常数。`f.readlines()` 会把整个文件载入列表，大文件会爆内存；`f.read()` 更是把全文变成一个字符串。

> [!tip] 为什么要 strip
> 每行末尾都带 `\n`。不处理的话 `["a\n", "b\n"]` 在比较、显示时都会有意外。`strip()` 去掉首尾空白，`rstrip("\n")` 只去换行、保留行首缩进——处理代码文件时后者更合适。

## 用 json 存结构化数据

```python
import json

data = {"name": "Ada", "langs": ["Python", "C"]}
with open("user.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

with open("user.json", encoding="utf-8") as f:
    loaded = json.load(f)

print(loaded)
print(loaded["langs"][0])
```

```expect
{'name': 'Ada', 'langs': ['Python', 'C']}
Python
```

`ensure_ascii=False` 让中文原样写入而不是转成 `\uXXXX`——文件给人看时可读性差很多。

## 二进制与文本要分清

```python
with open("blob.bin", "wb") as f:
    f.write(b"\x00\x01\x02")

with open("blob.bin", "rb") as f:
    raw = f.read()

print(len(raw), raw[0])
```

```expect
3 0
```

`"rb"` / `"wb"` 读写 `bytes`，不做编码转换。图片、压缩包、`pickle` 都要走这条路。

```quiz
question = "用 `open(path)` 打开文件但不关闭，最直接的后果是什么？"
options = [
  "文件内容会丢失",
  "文件句柄泄漏，进程可能耗尽可打开文件数",
  "下次打开会报编码错误",
  "没有任何影响，GC 会自动处理"
]
answer = 1
explain = "CPython 的引用计数通常会在对象销毁时关闭文件，但这是实现细节，不能依赖：异常路径、循环引用、其他解释器都可能让句柄迟迟不释放。用 with 才是确定的。"
```

```exercise
id = "s1-21-ex1"
title = "统计非空行"
prompt = "文件 `words.txt` 已经创建好。统计**非空行**的数量，存到变量 `count`。"
starter = '''
with open("words.txt", "w", encoding="utf-8") as f:
    f.write("alpha\n\nbeta\ngamma\n")

count = 0
# 在这里统计非空行数
'''
solution = '''
with open("words.txt", "w", encoding="utf-8") as f:
    f.write("alpha\n\nbeta\ngamma\n")

count = 0
with open("words.txt", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            count += 1
'''
tests = [
  "assert count == 3, '应该有 3 个非空行'",
  "assert isinstance(count, int), 'count 应该是整数'"
]
hints = [
  "逐行读文件，判断 `line.strip()` 是否为空。",
  "空行 strip 之后是空字符串，布尔值为假。",
  "循环里写 `if line.strip(): count += 1`。"
]
xp = 10
```

## 小结

- 永远用 `with open(...)`，异常时也会关闭。
- 显式写 `encoding="utf-8"`，省得换平台出问题。
- 逐行迭代文件比 `read()` / `readlines()` 省内存。
- `json.dump/load` 处理结构化数据，`ensure_ascii=False` 保留中文。
- `"rb"` / `"wb"` 是二进制，不涉及编码。
