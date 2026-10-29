+++
id = "s1-31-testing"
order = 31
stage = "s1"
official_group = "moderate"
title = "测试入门"
concepts = ["unittest", "pytest", "assertEqual", "assertRaises", "test naming"]
prereq = [30]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：unittest"
url = "https://docs.python.org/3/library/unittest.html"

[[doc_refs]]
title = "Tutorial 10.4：测试"
url = "https://docs.python.org/3/tutorial/stdlib.html#quality-control"
+++

# 测试是给未来的自己写的

写测试不只是"验证现在对不对"，更是把"我以为它该怎样"固化成可执行的断言。半年后改代码时，这些断言会告诉你哪里被弄坏了。

## 最小可用的测试

```python
import io
import unittest


def add(a, b):
    return a + b


class TestAdd(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(add(1, 2), 3)

    def test_negative(self):
        self.assertEqual(add(-1, -2), -3)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAdd)
result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)

print(result.wasSuccessful())
print(result.testsRun)
```

```expect
True
2
```

三件事：继承 `TestCase`、测试方法名以 `test_` 开头、用 `assertEqual` 而不是裸 `assert`。`assertEqual` 失败时会打出两边的值，裸 assert 只告诉你"不相等"。

## 测试异常

```python
import io
import unittest


def parse(text):
    return int(text)


class TestParse(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(parse("42"), 42)

    def test_raises_on_bad_input(self):
        with self.assertRaises(ValueError):
            parse("x")


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestParse)
result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)

print(result.wasSuccessful(), result.testsRun)
```

```expect
True 2
```

`assertRaises` 还能拿到异常对象，进一步检查消息：

```python
import unittest


def withdraw(balance, amount):
    if amount > balance:
        raise ValueError(f"余额不足：{balance} < {amount}")
    return balance - amount


class TestWithdraw(unittest.TestCase):
    def test_message(self):
        with self.assertRaises(ValueError) as ctx:
            withdraw(10, 20)
        self.assertIn("余额不足", str(ctx.exception))


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestWithdraw)
result = unittest.TextTestRunner(stream=__import__("io").StringIO()).run(suite)
print(result.wasSuccessful())
```

```expect
True
```

## unittest 与 pytest 的差别

| 维度 | unittest | pytest |
|---|---|---|
| 来源 | 标准库，零安装 | 第三方，需安装 |
| 写法 | 类 + 方法 | 普通函数 + 裸 assert |
| 断言信息 | 内置多种 assertXxx | 靠 assert 重写，自动展开 |
| fixture | setUp/tearDown | `@pytest.fixture`，按需组合 |

小项目用 `unittest` 足够，而且不用装东西；团队项目多用 `pytest`，因为写起来短、失败信息更好读。**两者不冲突**——`pytest` 能直接跑 `unittest` 写的用例。

> [!tip] 先写一个会失败的测试
> 新功能开始时，先写一个断言"期望行为"的测试，看它红；再实现，看它绿。这个循环能防止"写完发现测的是错的东西"。

```quiz
question = "`assertRaises(ValueError)` 用在 `with` 语句里，断言的是什么？"
options = [
  "代码块里任何异常都会通过",
  "代码块执行时必须抛出 ValueError",
  "代码块执行时不能抛异常",
  "ValueError 必须被捕获后不再抛出"
]
answer = 1
explain = "assertRaises 要求 with 块内抛出指定异常，没抛或抛了别的类型都算失败。它还能 as ctx 拿到异常对象，用来检查消息。"
```

## 小结

- 测试方法以 `test_` 开头，断言用 `assertEqual` / `assertRaises` 这类专用方法。
- `assertRaises` 用 `with` + `as ctx` 可以进一步检查异常消息。
- `unittest` 是标准库、零依赖；`pytest` 更短更好读，且能跑 unittest 用例。
- 先写失败测试再实现，能避免"测了错的东西"。
