+++
id = "s2-38-enum"
order = 38
stage = "s2"
official_group = "moderate"
title = "枚举与常量组织"
concepts = ["Enum", "auto", "Flag", "singleton", "constants"]
prereq = [37]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：enum"
url = "https://docs.python.org/3/library/enum.html"

[[doc_refs]]
title = "PEP 663：标准库中枚举的惯用法"
url = "https://peps.python.org/pep-0663/"
+++

# 魔法字符串是定时炸弹

`if status == "published"` 写十遍，第九遍拼成 `"publised"`，程序不会报错——只是行为悄悄错了。枚举把"合法取值"收进一个类型里，拼错会在**写代码的当下**被编辑器标红。

## 基本用法

```python
from enum import Enum


class Status(Enum):
    DRAFT = 1
    PUBLISHED = 2
    ARCHIVED = 3


print(Status.DRAFT.name, Status.DRAFT.value)
print(Status(2))
print(sorted(m.name for m in Status))
```

```expect
DRAFT 1
Status.PUBLISHED
['ARCHIVED', 'DRAFT', 'PUBLISHED']
```

成员是**单例**：`Status.DRAFT is Status.DRAFT` 恒为 True，可以直接用 `is` 比较。成员默认不可重复赋值，创建第二个 `DRAFT = 9` 会抛错。

## `auto()`：让解释器编号

```python
from enum import Enum, auto


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


print(Color.RED.value, Color.GREEN.value)
print(Color["GREEN"].name)
```

```expect
1 2
GREEN
```

数值本身不重要（永远别依赖它是 1 还是 2）时用 `auto()`。`Color["GREEN"]` 按名字取成员，和 `Color.GREEN` 等价——适合从配置文件读进来的字符串。

## Flag：位标志

```python
from enum import Flag, auto


class Perm(Flag):
    READ = auto()
    WRITE = auto()
    EXEC = auto()


p = Perm.READ | Perm.WRITE
print(Perm.READ in p)
print(Perm.EXEC in p)
print(p)
```

```expect
True
False
Perm.READ|WRITE
```

`Perm.READ | Perm.WRITE` 组合成一个权限集合，`in` 检查是否包含。比 `can_read = True; can_write = True` 这类散落变量强得多——一个变量携带全部状态。

> [!tip] 什么时候该用枚举
> 当一个值的取值集合**封闭且有限**（状态、方向、类型码），用 Enum。取值开放的（文件名、数字）不该用。用枚举后，函数签名 `def set_status(s: Status)` 本身就是文档。

```quiz
question = "枚举成员 `Status.DRAFT` 和 `Status(1)` 的关系是？"
options = [
  "不同对象，值相等",
  "同一个单例对象，可以用 is 比较",
  "每次 Status(1) 都会新建成员",
  "Status(1) 会抛 ValueError"
]
answer = 1
explain = "枚举成员在类定义时创建且唯一，按值查找返回同一个单例。所以两者 is 相等。如果 1 不对应任何成员才抛 ValueError。"
```

## 小结

- 枚举消灭魔法字符串/数字，拼错立刻报错。
- 成员是单例，用 `is` 比较；`Enum(值)` 按值反查。
- `auto()` 表示"编号无所谓"，永远别依赖具体数字。
- 多个可同时成立的开关用 `Flag`，`|` 组合、`in` 检查。
