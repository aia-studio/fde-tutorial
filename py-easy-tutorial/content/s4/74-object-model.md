+++
id = "s4-74-object-model"
order = 74
stage = "s4"
official_group = "advanced"
title = "对象模型：属性到底从哪来"
concepts = ["type", "object", "__dict__", "attribute lookup", "method binding"]
prereq = [34]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference §3.2：标准类型层级"
url = "https://docs.python.org/3/reference/datamodel.html#the-standard-type-hierarchy"

[[doc_refs]]
title = "Language Reference §3.3.2：自定义属性访问"
url = "https://docs.python.org/3/reference/datamodel.html#customizing-attribute-access"
+++

# `a.x` 背后发生的事

`a.x` 看起来是“取一个字段”，实际上是**一次协议调用**：解释器按固定顺序在实例字典、类字典、以及类的继承链上查找，途中还可能撞上描述符。理解这条链，你才能解释清楚为什么类属性会被实例属性遮蔽、为什么方法调用不用手动传 `self`、为什么 `__slots__` 能省内存。

## 实例字典与类字典是两本账

```python
class A:
    x = "class"

a = A()
print("实例字典:", a.__dict__)
print("读 a.x :", a.x)
a.x = "instance"
print("写入后 :", a.__dict__)
print("读 a.x :", a.x)
print("读 A.x :", A.x)
```

```expect
实例字典: {}
读 a.x : class
写入后 : {'x': 'instance'}
读 a.x : instance
读 A.x : class
```

关键在第三行：**读操作不写实例字典**。`a.x` 在实例里找不到，就去类里找，找到就返回，不会顺手把值复制到实例上。只有赋值才会在实例字典里建条目，从此遮蔽类属性。

## 类也是对象，类型是 `type`

```python
print(type(int))
print(type(type))
print(isinstance(int, type))
print(int.__mro__)
```

```expect
<class 'type'>
<class 'type'>
True
(<class 'int'>, <class 'object'>)
```

`type(type)` 还是 `type`——这条自指链到此为止。`object` 是所有类的基类，`type` 是所有类的类型，两者互相支撑，构成 Python 对象模型的地基。

## 方法为什么不用手动传 self

```python
class C:
    def hello(self):
        return "hi"


print(type(C.hello).__name__)
print(type(C().hello).__name__)
print(C().hello())
```

```expect
function
method
hi
```

同一个 `hello`，从类上取是普通函数，从实例上取变成绑定方法（bound method）。差别在于后者已经把实例“记住”了。

这背后是**描述符协议**：函数本身实现了 `__get__`，当它作为类属性被访问时，`__get__` 返回一个把实例绑定进去的可调用对象。所以 `C().hello()` 等价于 `C.hello(C())`。

> [!why] 为什么这很重要
> 你不用记“方法会自动传 self”，只要知道“函数是描述符”。下一课《描述符协议》会把这条机制完整拆开——`property`、`classmethod`、`staticmethod`、`__slots__` 全都是它的应用。

## 找不到时才轮到 `__getattr__`

```python
class D:
    def __getattr__(self, name):
        return f"{name} 不存在，但我不想报错"


d = D()
print(d.whatever)
print(hasattr(d, "typo"))
```

```expect
whatever 不存在，但我不想报错
True
```

`__getattr__` 只在**常规查找失败之后**才被调用。上面这段代码看着“友好”，实际上很危险：任何拼写错误都会被吞掉，`hasattr` 对任何名字都返回 `True`。

> [!danger] 不要用它掩盖错误
> 需要“可选属性”时，应该抛出 `AttributeError` 而不是返回字符串。代理对象（proxy）是少数正当场景，记得同时实现 `__dir__`，否则 `dir()` 和自动补全会失效。

## 完整查找顺序

| 顺序 | 查什么 | 备注 |
|---|---|---|
| 1 | 数据描述符（类里实现了 `__set__`） | 优先级最高，能压过实例字典 |
| 2 | 实例 `__dict__` | 普通属性存这里 |
| 3 | 非数据描述符或类属性 | 函数、`classmethod` 在这一层 |
| 4 | `__getattr__` | 前三步都失败才调用 |

`__slots__` 的作用也能由此解释：它把实例字典换成固定偏移的槽位，省掉 `__dict__` 的开销，代价是不能动态加属性。

```quiz
question = "`C().hello()` 能正常执行，最根本的原因是？"
options = [
  "解释器在调用时自动把实例塞进第一个参数",
  "函数实现了 `__get__`，从实例访问时返回绑定方法",
  "`self` 是 Python 的关键字，由编译器注入",
  "类会把实例保存为全局变量供方法读取"
]
answer = 1
explain = "方法是「函数作为类属性被访问」的结果。函数是描述符，`__get__` 返回把实例绑定进去的 method 对象，调用时再展开成 `C.hello(c)`。`self` 不是关键字，只是约定俗成的参数名。"
```

## 小结

- 读属性不写实例字典，只有赋值才写；实例属性遮蔽类属性。
- `type` 与 `object` 互为地基，`type(type) is type`。
- 方法是描述符的产物，`self` 是 `__get__` 绑定出来的，不是语法魔法。
- `__getattr__` 是兜底通道，滥用会把拼写错误变成静默 bug。
