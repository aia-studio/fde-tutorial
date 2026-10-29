+++
id = "s1-23-paths"
order = 23
stage = "s1"
official_group = "beginner"
title = "路径与文件系统"
concepts = ["pathlib", "glob", "rglob", "mkdir", "tempfile"]
prereq = [22]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：pathlib 的常用操作"
url = "https://docs.python.org/3/library/pathlib.html#basic-use"

[[doc_refs]]
title = "Library Reference：tempfile"
url = "https://docs.python.org/3/library/tempfile.html"
+++

# 建、找、删

`pathlib` 把文件系统操作变成方法调用：`mkdir`、`glob`、`read_text`、`unlink`。比 `os.path` 加字符串拼接清楚得多，也更难写错。

## 建目录、写文件、遍历

```python
import tempfile
from pathlib import Path

base = Path(tempfile.mkdtemp())
(base / "sub").mkdir()
(base / "sub" / "x.txt").write_text("hi", encoding="utf-8")

print(sorted(p.name for p in base.rglob("*")))
print((base / "sub" / "x.txt").read_text(encoding="utf-8"))
```

```expect
['sub', 'x.txt']
hi
```

`rglob("*")` 递归遍历，`glob("*")` 只看当前层。`mkdir()` 默认只能建一层，要建多层用 `mkdir(parents=True, exist_ok=True)`——这两个参数几乎总是要写。

## 按模式筛选

```python
import tempfile
from pathlib import Path

base = Path(tempfile.mkdtemp())
for name in ["a.py", "b.py", "c.txt"]:
    (base / name).write_text("", encoding="utf-8")

print(sorted(p.name for p in base.glob("*.py")))
print(len(list(base.glob("*.txt"))))
```

```expect
['a.py', 'b.py']
1
```

模式匹配只支持 `*`、`?`、`[seq]`，不是正则。要复杂匹配就先 `glob("*")` 再用 `re` 筛。

## 临时目录：测试的好帮手

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "demo.txt"
    path.write_text("临时", encoding="utf-8")
    print(path.exists(), path.stat().st_size)

print(path.exists())
```

```expect
True 6
False
```

`TemporaryDirectory` 是上下文管理器，离开 `with` 自动递归删除。测试里需要"造文件"时优先用它，不要往仓库目录里写。

`size` 是 6，因为 "临时" 两个汉字在 UTF-8 下各占 3 字节——`stat().st_size` 数的是字节，不是字符。

```quiz
question = "`Path('a').mkdir()` 在 `a` 已存在时会怎样？"
options = [
  "什么也不做",
  "抛 FileExistsError",
  "清空目录内容",
  "返回 False"
]
answer = 1
explain = "默认 exist_ok=False，目录已存在就抛 FileExistsError。要幂等就写 mkdir(exist_ok=True)；要一次建多层再加 parents=True。"
```

## 小结

- `pathlib` 用 `/` 拼路径，`mkdir(parents=True, exist_ok=True)` 建多层且幂等。
- `glob("*")` 只看当前层，`rglob("*")` 递归。
- `read_text` / `write_text` 记得传 `encoding="utf-8"`。
- `TemporaryDirectory` 自动清理，测试首选。
- `stat().st_size` 是字节数，不是字符数。
