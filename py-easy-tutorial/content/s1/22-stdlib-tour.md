+++
id = "s1-22-stdlib-tour"
order = 22
stage = "s1"
official_group = "beginner"
title = "标准库速览：os、pathlib、datetime"
concepts = ["os", "sys", "pathlib", "datetime", "timedelta"]
prereq = [21]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 10：标准库概览"
url = "https://docs.python.org/3/tutorial/stdlib.html"

[[doc_refs]]
title = "Library Reference：pathlib"
url = "https://docs.python.org/3/library/pathlib.html"
+++

# 三个模块，覆盖大半日常活

写脚本时最常打交道的标准库是这三个：`os`/`sys` 处理运行时环境，`pathlib` 处理路径，`datetime` 处理时间。它们不需要额外安装，也不该用第三方库替代。

## `os` 与 `sys`：问清楚自己在哪

```python
import os
import sys

print(os.name in ("nt", "posix"))
print(sys.version_info[:2] >= (3, 15))
print(len(sys.path) > 0)
```

```expect
True
True
True
```

`os.name` 在 Windows 上是 `"nt"`，在 Linux/macOS 上是 `"posix"`。判断平台时别写死字符串比较，用这种"是否属于集合"的写法更稳。

`sys.path` 是导入搜索路径，`sys.argv` 是命令行参数，`sys.exit()` 是退出。这三个是脚本的入口三件套。

## `pathlib`：路径是对象，不是字符串

```python
from pathlib import Path

p = Path("data") / "2026" / "report.csv"

print(p.as_posix())
print(p.name)
print(p.stem)
print(p.suffix)
print(p.parent.as_posix())
```

```expect
data/2026/report.csv
report.csv
report
.csv
data/2026
```

用 `/` 拼路径是 `pathlib` 最舒服的地方——不用管反斜杠转义，也不用 `os.path.join`。`name`/`stem`/`suffix`/`parent` 这几个属性比字符串切片可靠得多。

## `datetime`：区分"时间点"和"时长"

```python
from datetime import datetime, timedelta

start = datetime(2026, 10, 29, 12, 0)
end = start + timedelta(days=1, hours=3)

print(start.strftime("%Y-%m-%d %H:%M"))
print(end - start)
print(end > start)
```

```expect
2026-10-29 12:00
1 day, 3:00:00
True
```

`datetime` 是时间点，`timedelta` 是时长，相减得到时长、相加得到新时间点。`strftime` 负责格式化输出，`strptime` 反过来解析字符串。

> [!warn] 不带时区的时间是"天真"的
> `datetime(2026, 10, 29)` 没有时区信息，比较和相减只在同一假设下成立。跨时区要用 `datetime.now(timezone.utc)` 或 `zoneinfo`，第 42 课专门讲。

```quiz
question = "`Path('a/b/c.txt').stem` 的结果是？"
options = ["a/b/c", "c.txt", "c", ".txt"]
answer = 2
explain = "name 是 'c.txt'，stem 是去掉最后一个后缀的 'c'，suffix 是 '.txt'，parent 是 'a/b'。"
```

## 小结

- `os.name` 判断平台，`sys.path` 是导入路径，`sys.argv` 是命令行参数。
- `pathlib` 用 `/` 拼路径，`name`/`stem`/`suffix`/`parent` 比字符串切片可靠。
- `datetime` 是时间点，`timedelta` 是时长；`strftime` 格式化，`strptime` 解析。
- 不带时区的 `datetime` 只在单一时区假设下成立。
