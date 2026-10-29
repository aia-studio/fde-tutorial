+++
id = "s2-37-operators"
order = 37
stage = "s2"
official_group = "moderate"
title = "运算符重载与容器协议"
concepts = ["__add__", "__len__", "__getitem__", "__contains__", "NotImplemented"]
prereq = [36]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：模拟数字类型"
url = "https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types"

[[doc_refs]]
title = "Library Reference：模拟容器类型"
url = "https://docs.python.org/3/reference/datamodel.html#emulating-container-types"
+++

# 让自己的类" behaves like builtins"

`a + b`、`len(x)`、`"x" in y` 背后都是协议方法：`__add__`、`__len__`、`__contains__`。实现哪个协议，类就获得哪种"内置感"。

## `__add__` 与反射版本

```python
class Money:
    def __init__(self, cents):
        self.cents = cents

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.cents + other.cents)

    def __repr__(self):
        return f"Money({self.cents})"


print(Money(100) + Money(250))
print(sum([Money(1), Money(2), Money(3)], start=Money(0)))
```

```expect
Money(350)
Money(6)
```

`sum` 的写法暴露了另一个要点：`Money(0) + Money(1)` 走 `__add__`，没问题。但如果反过来 `1 + Money(2)`，`int.__add__` 不认识 Money，Python 会问 Money 的 `__radd__`（反射加法）——没实现就返回 `NotImplemented`，最后抛 `TypeError`。

**`NotImplemented` 不是异常，是"我不认识，你去问对方"的信号**，第 79 课展开。

## 容器协议：len、索引、in

```python
class Playlist:
    def __init__(self, songs):
        self._songs = list(songs)

    def __len__(self):
        return len(self._songs)

    def __getitem__(self, index):
        return self._songs[index]

    def __contains__(self, song):
        return song in self._songs


pl = Playlist(["a", "b", "c"])
print(len(pl), pl[0], pl[-1])
print("b" in pl, "z" in pl)
print(list(pl))
```

```expect
3 a c
True False
['a', 'b', 'c']
```

只实现了 `__getitem__`，`for` 和 `list()` 就都能用——Python 的旧式迭代协议看到 `__getitem__` 会自动包一层。想更规范，实现 `__iter__`（第 27 课的协议）。

## 可变容器：再补两个方法

```python
class Registry:
    def __init__(self):
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)


r = Registry()
r["a"] = 1
r["b"] = 2
print(r["a"], len(r))
del r["a"]
print(len(r))
```

```expect
1 2
1
```

完整实现 `__setitem__` / `__delitem__` 后，类可以像字典一样用——但**没有字典快**。这是接口便利和性能的权衡，数据量大时包一层真字典更明智。

```quiz
question = "`__add__` 遇到不支持的类型时，正确做法是什么？"
options = [
  "抛 TypeError",
  "返回 NotImplemented，让 Python 去问对方的反射方法",
  "返回 None",
  "返回 0"
]
answer = 1
explain = "返回 NotImplemented 后，Python 会尝试 other.__radd__；两边都 NotImplemented 才抛 TypeError。抛 TypeError 会剥夺对方参与运算的机会，1 + Money(2) 这种「谁在前」的问题就无解了。"
```

## 小结

- `__add__` 等算术方法返回**新对象**，不要原地改。
- 不支持的类型返回 `NotImplemented`，让反射方法有机会接手。
- 容器协议：`__len__` / `__getitem__` / `__setitem__` / `__contains__` 按需实现。
- 实现了 `__getitem__` 就自动获得迭代能力，但显式 `__iter__` 更规范。
