+++
id = "s0-07-bytes"
order = 7
stage = "s0"
official_group = "beginner"
title = "编码与字节：str 和 bytes 的边界"
concepts = ["str", "bytes", "utf-8", "encode", "decode", "unicode"]
prereq = [6]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：二进制序列类型 bytes"
url = "https://docs.python.org/3/library/stdtypes.html#binary-sequence-types-bytes-bytearray-memoryview"

[[doc_refs]]
title = "Python HOWTOs：Unicode"
url = "https://docs.python.org/3/howto/unicode.html"
+++

# 文本是文本，字节是字节

Python 3 把这件事做了一次硬切割：`str` 是**字符**序列，`bytes` 是**字节**序列。两者不能混用，转换必须显式调用 `encode` / `decode`。这条规则看起来麻烦，但它消灭了 Python 2 时代一半的乱码问题。

## 一个字，几个字节？

```python
text = "你好"

data = text.encode("utf-8")
print(data)
print(len(text), len(data))
print(data.decode("utf-8"))
```

```expect
b'\xe4\xbd\xa0\xe5\xa5\xbd'
2 6
你好
```

"你好"是 2 个字符，但 UTF-8 下一个汉字占 3 字节，所以编码后是 6 字节。**长度取决于你在数什么**——`len(str)` 数字符，`len(bytes)` 数字节。

`b'...'` 前缀就是 bytes 字面量，里面的 `\xe4` 是一个字节的十六进制表示。

## 编码是一张映射表，选错了就对不上

```python
print("café".encode("utf-8"))
print("café".encode("latin-1"))
```

```expect
b'caf\xc3\xa9'
b'caf\xe9'
```

同一个 `é`，UTF-8 用 2 字节，latin-1 用 1 字节。用 A 编码、用 B 解码，得到的不是报错就是乱码——这就是"锟斤拷"的来源。

```python
try:
    "你好".encode("ascii")
except UnicodeEncodeError:
    print("ascii 装不下中文")
    print("café".encode("ascii", errors="replace"))
```

```expect
ascii 装不下中文
b'caf?'
```

`errors="replace"` 把编不出来的字符换成 `?`。还有 `ignore`（直接丢掉）和 `backslashreplace`（转成 `\uXXXX`）。**默认严格模式是好事**——静默丢数据比报错可怕得多。

> [!danger] 别用 errors="ignore" 掩盖问题
> 它会让"用户名字里的生僻字"在入库时静默消失。要处理编码问题，先确认源头用的是什么编码，而不是把异常吞掉。

## 什么时候会遇到 bytes

| 场景 | 拿到的是 |
|---|---|
| 读文本文件（默认） | `str` |
| 读二进制文件（`"rb"`） | `bytes` |
| socket / HTTP 响应体 | `bytes` |
| `hashlib` 的结果 | `bytes` |
| 命令行参数 | `str` |

```python
import hashlib

digest = hashlib.sha256("abc".encode("utf-8")).hexdigest()
print(digest[:16])
print(len(digest))
```

```expect
ba7816bf8f01cfea
64
```

`hashlib` 只接受 bytes，所以要先把字符串编码。`hexdigest()` 再把它变成 64 个十六进制字符的 `str`——注意这两步的方向相反。

```quiz
question = "`len(\"你好\")` 和 `len(\"你好\".encode(\"utf-8\"))` 分别是什么？"
options = ["2 和 2", "6 和 6", "2 和 6", "6 和 2"]
answer = 2
explain = "str 的长度是字符数（2 个汉字），UTF-8 编码后每个汉字 3 字节，所以 bytes 长度是 6。"
```

## 小结

- `str` 是字符，`bytes` 是字节，转换必须显式 `encode`/`decode`。
- UTF-8 下一个汉字 3 字节，`len` 的语义取决于类型。
- 编解码必须配对，`UTF-8` 是默认选择。
- 出错时先查源头编码，别用 `ignore` 吞掉。
- 哈希、网络、二进制文件这些场景拿到的是 bytes。
