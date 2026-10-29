+++
id = "s3-57-testing-advanced"
order = 57
stage = "s3"
official_group = "moderate"
title = "测试进阶"
concepts = ["setUp", "mock", "subTest", "patch", "test isolation"]
prereq = [56]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：unittest.mock"
url = "https://docs.python.org/3/library/unittest.mock.html"

[[doc_refs]]
title = "Library Reference：setUp 与 tearDown"
url = "https://docs.python.org/3/library/unittest.html#setup-and-teardown"
+++

# 隔离、替身、批量

入门测试验证"给定输入得到输出"；进阶测试解决三件事：**每个用例独立**（setUp）、**依赖替换成假货**（mock）、**同一逻辑测多组数据**（subTest）。

## setUp：每个用例全新开始

```python
import io
import unittest


class Cart:
    def __init__(self):
        self.items = []

    def add(self, x):
        self.items.append(x)


class TestCart(unittest.TestCase):
    def setUp(self):
        self.cart = Cart()

    def test_add_one(self):
        self.cart.add("球")
        self.assertEqual(self.cart.items, ["球"])

    def test_starts_empty(self):
        self.assertEqual(self.cart.items, [])


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCart)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(result.wasSuccessful(), result.testsRun)
```

```expect
True 2
```

`setUp` 在**每个测试方法前**各跑一次——所以 `test_starts_empty` 看到的是空购物车，而不是被上一个用例污染的。测试之间互不知晓，这是测试可信的前提。

## mock：把"真东西"换成假的

```python
import io
import unittest
from unittest import mock


class TestClient(unittest.TestCase):
    def test_uses_api(self):
        fake = mock.Mock(return_value={"status": 200})
        self.assertEqual(fake("https://api.example.com")["status"], 200)
        fake.assert_called_once_with("https://api.example.com")


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestClient)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(result.wasSuccessful(), result.testsRun)
```

```expect
True 1
```

`Mock()` 是一个"什么都接受、可以预设返回值"的对象，还能事后核验"被怎么调用过"。测试网络客户端时，用 Mock 替掉真请求——测试要快、要离线、要能模拟失败，这三件事真接口都做不到。

> [!warn] 只 mock 自己的边界
> 原则：**mock 你拥有所有权的东西**（自己封装的 API 客户端），不要 mock 被测模块的内部实现——那样测的是实现细节而不是行为，重构一下测试就全红。

## subTest：一组数据，一次失败各自报告

```python
import io
import unittest


def is_palindrome(text):
    return text == text[::-1]


class TestPalindrome(unittest.TestCase):
    def test_samples(self):
        for text in ["abba", "abc", "aba"]:
            with self.subTest(text=text):
                self.assertTrue(is_palindrome(text))


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPalindrome)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(result.wasSuccessful(), result.testsRun)
```

```expect
False 1
```

这个结果**诚实**：用例失败是因为 `"abc"` 根本不是回文，测试数据里有两个错例（`abc` 应删掉，或断言写 `assertFalse`）。`subTest` 的价值是**每组数据独立报告**，错哪一条清清楚楚，而不是第一个失败就中断。

```quiz
question = "测试网络客户端，为什么要把请求函数 mock 掉？"
options = [
  "让测试跑得更快、不依赖网络、能模拟服务器故障",
  "因为 mock 能让测试通过",
  "因为真实接口必须付费",
  "因为 mock 是标准库要求"
]
answer = 0
explain = "测试的三要素：快、稳定、可控。真请求慢、断网就挂、很难构造「服务器返回 500」这种分支。mock 把这些变成确定性的输入，同时还能核验调用参数。"
```

## 小结

- `setUp` 每用例各跑一次，测试之间必须互相独立。
- `Mock` 替掉外部依赖，并核验调用方式；只 mock 自己拥有的边界。
- `subTest` 让一组数据各自报告失败，不用拆成 N 个方法。
- 测试挂在实现细节上等于没写——重构一改就全红。
