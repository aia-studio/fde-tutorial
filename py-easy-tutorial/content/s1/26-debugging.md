+++
id = "s1-26-debugging"
order = 26
stage = "s1"
official_group = "beginner"
title = "调试"
concepts = ["traceback", "assert", "warnings", "pdb", "reproduce"]
prereq = [25]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：traceback"
url = "https://docs.python.org/3/library/traceback.html"

[[doc_refs]]
title = "Library Reference：pdb"
url = "https://docs.python.org/3/library/pdb.html"
+++

# 先看清，再动手

调试最大的浪费不是修得慢，而是**修错了地方**。所以顺序永远是：拿到完整 traceback → 定位到具体行 → 复现最小案例 → 再改。

## traceback 是线索，不是噪音

```python
import traceback


def inner():
    return 1 / 0


try:
    inner()
except ZeroDivisionError:
    tb = traceback.format_exc()

print("ZeroDivisionError" in tb)
print("inner" in tb)
```

```expect
True
True
```

从下往上看 traceback：最后一行是异常类型和消息，上面依次是调用栈，**离你最近的帧在最下面**。`format_exc()` 拿到完整文本，可以写进日志。

> [!tip] 读 traceback 的顺序
> 先看最后一行（什么错），再看倒数第二个 `File` 行（哪一行），最后才往上看调用链。初学者常从第一行读起，读完一屏还没看到错误类型。

## assert：把假设写进代码

```python
def average(nums):
    assert nums, "空列表没有平均值"
    return sum(nums) / len(nums)


print(average([1, 2, 3]))

try:
    average([])
except AssertionError as exc:
    print(type(exc).__name__, exc)
```

```expect
2.0
AssertionError 空列表没有平均值
```

`assert` 表达的是"这里必须成立，否则是我的代码有 bug"，不是"用户输入要校验"。区别很重要：**`python -O` 会移除所有 assert**，所以不能用它做参数校验。

## warnings：提醒但不打断

```python
import warnings

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    warnings.warn("这个参数下个版本会移除", UserWarning)

print(len(caught))
print(caught[0].message)
```

```expect
1
这个参数下个版本会移除
```

弃用警告就该用 `warnings`，而不是 `print`——调用方可以按类别过滤或升级为异常。

## pdb：断点比 print 高效

```python
def buggy(nums):
    total = 0
    for n in nums:
        total += n
    return total / len(nums)
```

在 `return` 那行写 `breakpoint()`，程序会停在那里，可以逐行执行、查看每个变量。常用命令只有五个：`n`（下一行）、`s`（进入函数）、`c`（继续）、`p expr`（打印）、`q`（退出）。

```quiz
question = "用 `assert` 校验用户输入，最大的问题是什么？"
options = [
  "assert 只能比较数字",
  "python -O 会移除所有 assert，校验直接失效",
  "assert 会抛 ValueError",
  "assert 不能带消息"
]
answer = 1
explain = "assert 是给开发者自己用的自检，优化模式下会被整体删掉。用户输入校验必须用 if + raise，否则生产环境等于没校验。"
```

## 小结

- traceback 从下往上读：错误类型 → 出错行 → 调用链。
- `assert` 用于内部不变式，不用于输入校验（`-O` 会移除）。
- 弃用提醒用 `warnings`，别用 `print`。
- `breakpoint()` + `n/s/c/p/q` 五个命令足够日常调试。
