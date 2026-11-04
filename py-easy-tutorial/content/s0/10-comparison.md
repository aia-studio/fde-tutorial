+++
id = "s0-10-comparison"
order = 10
stage = "s0"
official_group = "beginner"
title = "比较、真值与身份"
concepts = ["comparison", "truthiness", "identity", "equality", "None"]
prereq = [9]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference §6.10：比较运算"
url = "https://docs.python.org/3/reference/expressions.html#comparisons"

[[doc_refs]]
title = "内置类型：真值检验"
url = "https://docs.python.org/3/library/stdtypes.html#truth-value-testing"
+++

# 三个问句：相等吗、是同一个吗、算真吗

Python 里判断一件事，有三种不同的问法，混用就会出隐蔽 bug：

- `a == b`：值相等吗
- `a is b`：是同一个对象吗
- `if a:`：它的"真值"是什么

## `==` 看内容，`is` 看身份

```python
x = [1, 2]
y = [1, 2]

print(x == y)
print(x is y)
print(x is x)
```

```expect
True
False
True
```

`==` 会调用 `__eq__`，逐个元素比；`is` 直接比对象地址，没有商量的余地。

那什么时候该用 `is`？**只有跟单例比较时**：`None`、`True`、`False`。

```python
value = None
print(value is None)
print(value == None)
```

```expect
True
True
```

两行都是 `True`，但只有第一行是对的。`None` 是全局唯一对象，用 `is` 既准确又快；写 `==` 会调用 `__eq__`，如果对面是个重载了比较的自定义对象，还可能返回意想不到的结果。

> [!warn] 永远不要用 `is` 比较数字和字符串
> `a = 1000; b = 1000; a is b` 的结果依赖实现细节（小整数缓存、常量折叠），不是语言保证。要比较值就用 `==`。

## 链式比较是语法糖，但很值

```python
age = 25

print(18 <= age < 65)
print(1 < 2 < 3 < 4)
```

```expect
True
True
```

`18 <= age < 65` 等价于 `18 <= age and age < 65`，但 `age` 只求值一次。写区间判断时优先用这个形式。

## 真值：空的就是假

```python
for value in [0, 1, "", "0", [], [0], None, False]:
    print(repr(value), bool(value))
```

```expect
0 False
1 True
'' False
'0' True
[] False
[0] True
None False
False False
```

规则：**空容器、零、`None`、`False` 为假，其余为真**。注意 `"0"` 和 `[0]` 都是真的——"非空"就是真，内容是什么不重要。

所以 Python 里不写 `if len(items) > 0:`，直接 `if items:`；也不写 `if x == None:`，直接 `if x is None:`。

```python
def greet(name=None):
    if not name:
        return "你好，陌生人"
    return f"你好，{name}"


print(greet())
print(greet("Ada"))
print(greet(""))
```

```expect
你好，陌生人
你好，Ada
你好，陌生人
```

第三行暴露了一个真实的坑：空字符串也是"假"，所以传 `""` 会被当成没传。要区分"没传"和"传了空值"，得写 `if name is None:`。

```quiz
question = "`[] == False` 的结果是？"
options = ["True", "False", "报错", "取决于 Python 版本"]
answer = 1
explain = "空列表的布尔值是 False，但 `==` 比较的是值相等：列表和布尔值类型不同，直接不等。`bool([]) == False` 才是 True。这正是「真值」和「相等」不能混用的例子。"
```

## 小结

- `==` 比内容，`is` 比身份；只有 `None`/`True`/`False` 该用 `is`。
- 链式比较 `a < b < c` 只求值一次，写区间首选。
- 空容器、0、`None`、`False` 为假；`"0"`、`[0]` 为真。
- 判断"有没有传参"用 `is None`，不要用 `if not x`。
