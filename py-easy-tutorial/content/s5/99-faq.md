+++
id = "s5-99-faq"
order = 99
stage = "s5"
official_group = "general"
title = "FAQ 与报错对照"
concepts = ["KeyError", "TypeError", "ModuleNotFoundError", "troubleshooting"]
prereq = []
standalone = true
requires_python = "3.15"
allow_network = false
xp = 10

[[doc_refs]]
title = "Python FAQ（官方）"
url = "https://docs.python.org/3/faq/"

[[doc_refs]]
title = "Library Reference：内置异常"
url = "https://docs.python.org/3/library/exceptions.html"
+++

# 报错 → 原因 → 修法

遇到报错先别改代码。这张表按出现频率排列了八个最常见异常，每个都给最小复现与修法——**先对号，再入座**。

## 现场复现八种常见异常

```python
samples = {
    "KeyError": lambda: {}["missing"],
    "IndexError": lambda: [][0],
    "AttributeError": lambda: None.upper(),
    "TypeError": lambda: 1 + "a",
    "ZeroDivisionError": lambda: 1 / 0,
    "ValueError": lambda: int("x"),
    "NameError": lambda: undefined_name,
    "RecursionError": lambda: (lambda f: f(f))(lambda f: f(f)),
}

for name, trigger in samples.items():
    try:
        trigger()
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")
```

```expect
KeyError: 'missing'
IndexError: list index out of range
AttributeError: 'NoneType' object has no attribute 'upper'
TypeError: unsupported operand type(s) for +: 'int' and 'str'
ZeroDivisionError: division by zero
ValueError: invalid literal for int() with base 10: 'x'
NameError: name 'undefined_name' is not defined
RecursionError: maximum recursion depth exceeded
```

## 对照表：报错 → 最可能的原因

| 报错 | 最常见原因 | 第一反应 |
|---|---|---|
| `KeyError` | 字典里没有这个键 | `d.get(k, default)` 或先 `in` 判断 |
| `IndexError` | 序列比想象的短 | 打印 `len()`，检查边界 |
| `AttributeError: NoneType` | 上游函数返回了 None 却被调用方法 | 检查返回类型注解（`X \| None`） |
| `TypeError: ... + ...` | 混用了不兼容类型 | 打印两个操作数的 `type()` |
| `ModuleNotFoundError` | pip 装到了另一个解释器 | 看 `sys.executable`，用 `python -m pip` |
| `ImportError: partially initialized` | 循环导入 | 打破依赖环（局部导入/抽共享模块） |
| `UnboundLocalError` | 函数内赋值让名字变局部，却先读了它 | 需要改全局就写 `global` |
| `IndentationError` | 混用 Tab 与空格 | 编辑器统一配置为 4 空格 |

## FAQ 精编三则

**为什么 0.1 + 0.2 不等于 0.3？** 二进制浮点的表示误差（第 5 课），比较用 `math.isclose`，金额用 `Decimal`。

**为什么列表 `in` 很慢？** 逐个比较 O(n)；频繁成员判断换 `set` O(1)（第 64 课）。

**为什么我的字符串是 `'a\nb'` 而显示两行？** `repr` 与 `str` 的区别（第 20 课）——调试时打印 `repr` 才能看见隐藏字符。

> [!tip] 排查顺序
> 1. 读完整个 traceback（从下往上）；2. 复制最后一行到本表对号；3. 定位到行后打印相关变量的 `repr` 与 `type`。三步走完还没头绪，才进 pdb（第 26 课）。

```quiz
question = "`AttributeError: 'NoneType' object has no attribute 'append'` 最典型的成因是？"
options = [
  "对象是不可变类型",
  "某个函数默认返回 None，而调用方直接链式调用了它的方法",
  "模块没有导入",
  "列表索引越界"
]
answer = 1
explain = "Python 函数不写 return 就返回 None。最常见于「调用了 append/in-place 方法（返回 None）后又链式调用」，或忘记写 return。"
```

## 小结

- 八大高频异常：KeyError / IndexError / AttributeError / TypeError / ZeroDivisionError / ValueError / NameError / RecursionError。
- `NoneType` 报错 = 有人返回了 None；`ModuleNotFoundError` = 解释器不对。
- 排查三步：读 traceback → 对号入座 → 打印 repr 与 type。
- 完整 FAQ 在 `docs.python.org/3/faq/`，按异常名搜索最快。
