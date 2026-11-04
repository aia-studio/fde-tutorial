+++
id = "s2-51-datetime"
order = 51
stage = "s2"
official_group = "moderate"
title = "日期与时间"
concepts = ["datetime", "timezone", "zoneinfo", "strptime", "aware"]
prereq = [49]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：datetime"
url = "https://docs.python.org/3/library/datetime.html"

[[doc_refs]]
title = "Library Reference：zoneinfo"
url = "https://docs.python.org/3/library/zoneinfo.html"
+++

# 天真时间与带时区时间

`datetime` 最重要的一条规则：**内部一律用 UTC，只在展示时转时区**。做到这条，夏令时、跨时区比较的 bug 基本绝迹。

## 时区转换：先给时间点，再换显示

```python
from datetime import datetime, timezone, timedelta

dt = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)
print(dt.isoformat())
print(dt.astimezone(timezone(timedelta(hours=8))))
```

```expect
2026-10-29T12:00:00+00:00
2026-10-29 20:00:00+08:00
```

同一个时间点，UTC 显示 12 点，东八区显示 20 点。`astimezone` 不改变时间点本身，只改变它的"读法"。

## 天真时间不能和带时区时间比较

```python
from datetime import datetime, timezone

naive = datetime(2026, 1, 1)
aware = datetime(2026, 1, 1, tzinfo=timezone.utc)

try:
    naive < aware
except TypeError:
    print("天真时间不能和带时区时间比较")
```

```expect
天真时间不能和带时区时间比较
```

没有时区的时间（naive）是"一个数字"，带时区的（aware）是"一个时刻"。两者无法比较——这个 `TypeError` 其实是保护你：混用两种时间，结果毫无意义。

## `zoneinfo`：真实世界的时区

```python
from datetime import datetime
from zoneinfo import ZoneInfo

sh = datetime(2026, 10, 29, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
print(sh.isoformat())
print(sh.astimezone(ZoneInfo("UTC")).hour)
```

```expect
2026-10-29T12:00:00+08:00
4
```

`ZoneInfo` 带着真实的时区规则（含夏令时历史），比手写 `+8` 可靠。上海没有夏令时，但纽约有——手动加减小时数的代码在 3 月和 11 月会各错一次。

> [!warn] 别用 datetime.utcnow()
> 它返回的是**天真时间**，值是 UTC 但不带时区标记，后续比较和序列化都会埋雷。用 `datetime.now(timezone.utc)`（aware）替代——它在 3.12 起已被标记弃用。

## 解析：格式必须逐字符对应

```python
from datetime import datetime

parsed = datetime.strptime("29/10/2026 14:30", "%d/%m/%Y %H:%M")
print(parsed.isoformat(sep=" "))
```

```expect
2026-10-29 14:30:00
```

`strptime` 用格式串解析，`%d` 日、`%m` 月、`%Y` 年。格式写错不会报错——`29/10/2026` 用 `%m/%d` 解析会把 29 当月数直接抛 `ValueError`，所以**解析外部时间必须捕获异常**。反过来格式化用 `strftime`。

```quiz
question = "内部存储时间戳应该用哪种形式？"
options = [
  "本地时区的 naive datetime",
  "UTC 的 aware datetime，展示时再转时区",
  "格式化好的字符串",
  "本地时间的 Unix 时间戳除以 86400"
]
answer = 1
explain = "内部一律用 UTC（aware），展示层再 astimezone 到本地。这样夏令时切换、跨时区用户都不会算错；naive 时间无法回答「这到底是什么时刻」。"
```

## 小结

- 内部存 UTC（aware），展示时 `astimezone` 转时区。
- naive 与 aware 不能比较，混用即 bug。
- `ZoneInfo` 带真实时区规则，替代手写偏移。
- `strptime` 解析外部时间要捕获 `ValueError`；`utcnow()` 已弃用。
