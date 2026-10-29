+++
id = "s1-25-exceptions"
order = 25
stage = "s1"
official_group = "beginner"
title = "异常处理"
concepts = ["try", "except", "finally", "raise", "exception chaining", "custom exception"]
prereq = [24]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 8：错误与异常"
url = "https://docs.python.org/3/tutorial/errors.html"

[[doc_refs]]
title = "Library Reference：内置异常"
url = "https://docs.python.org/3/library/exceptions.html"
+++

# 异常是控制流，不是灾难

Python 用异常表示"这件事做不成"，而且鼓励用它来传递失败：`int("x")` 抛 `ValueError`，`d["missing"]` 抛 `KeyError`。学会精确捕获，比到处 `try: except: pass` 有价值得多。

## 四个子句各管一段

```python
def parse(text):
    try:
        value = int(text)
    except ValueError:
        return "不是整数"
    else:
        return value * 2
    finally:
        print("清理")


print(parse("21"))
print(parse("x"))
```

```expect
清理
42
清理
不是整数
```

- `try` 里只放**可能失败的那一句**，范围越小越不容易误捕获。
- `except` 指定异常类型，捕获面越窄越好。
- `else` 在 try 没异常时执行——把"成功后的逻辑"移出 try，避免它自己的异常被同一个 except 吞掉。
- `finally` 无论成败都执行，适合释放资源（其实 `with` 更合适）。

## 自定义异常：让调用方分得清

```python
class ConfigError(Exception):
    pass


def load(value):
    if value < 0:
        raise ConfigError(f"配置不能为负：{value}")
    return value


try:
    load(-1)
except ConfigError as exc:
    print(type(exc).__name__, exc)
```

```expect
ConfigError 配置不能为负：-1
```

自定义异常的价值在于**可区分**：调用方可以只捕获 `ConfigError`，让其他异常照常冒泡。继承 `Exception` 而不是 `BaseException`——后者是给 `KeyboardInterrupt` 这种系统级信号用的。

## 异常链：别丢掉根因

```python
try:
    try:
        int("x")
    except ValueError as exc:
        raise RuntimeError("解析配置失败") from exc
except RuntimeError as exc:
    print(type(exc).__name__)
    print(type(exc.__cause__).__name__)
```

```expect
RuntimeError
ValueError
```

`raise ... from exc` 把原始异常存进 `__cause__`，traceback 会显示 "The above exception was the direct cause..."。这在一层层包装的函数里至关重要——否则你只能看到最后一层，根因丢了。

> [!danger] 不要写 `except Exception: pass`
> 它会把 `KeyError`、拼写错误、甚至 `MemoryError` 一起吞掉，程序继续带着错误状态运行。至少要 `except Exception as exc: logger.exception(...)`，或者干脆别捕获。

```quiz
question = "`try` 里 `return` 之后，`finally` 还会执行吗？"
options = [
  "不会，return 直接结束函数",
  "会，finally 在函数真正返回前执行",
  "只有抛异常时才执行",
  "取决于是否写了 else"
]
answer = 1
explain = "finally 在离开 try 语句前一定执行，包括 return、break、continue 和异常路径。这也是它适合做清理的原因。"
```

```exercise
id = "s1-25-ex1"
title = "安全地转成整数"
prompt = "实现 `safe_int(text, default=0)`：能转就返回整数，转不了返回 default。不要用 `if text.isdigit()` 之类的预判，用异常处理。"
starter = """
def safe_int(text, default=0):
    # 在这里实现
    pass
"""
solution = '''
def safe_int(text, default=0):
    try:
        return int(text)
    except (TypeError, ValueError):
        return default
'''
tests = [
  "assert safe_int('42') == 42, '正常数字应该转成功'",
  "assert safe_int('x') == 0, '非法输入回退到默认值'",
  "assert safe_int('x', -1) == -1, '默认值可以被覆盖'",
  "assert safe_int('3.5') == 0, '小数不算整数'",
  "assert safe_int(None) == 0, 'None 也要兜住'"
]
hints = [
  "int() 在解析失败时抛 ValueError，类型不对时抛 TypeError。",
  "把两个异常一起捕获：`except (TypeError, ValueError):`。",
  "不要先判断再转换——预判总会漏掉边界情况。"
]
xp = 10
```

## 小结

- `try` 范围要小，`except` 类型要窄。
- `else` 放成功路径，`finally` 做清理（但资源释放优先用 `with`）。
- 自定义异常继承 `Exception`，让调用方能精确捕获。
- `raise ... from exc` 保留根因，不要用 `except: pass` 掩盖问题。
