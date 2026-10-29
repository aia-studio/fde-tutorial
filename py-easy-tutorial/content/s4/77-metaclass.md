+++
id = "s4-77-metaclass"
order = 77
stage = "s4"
official_group = "advanced"
title = "元类与类创建钩子"
concepts = ["metaclass", "type", "__init_subclass__", "__prepare__", "registry"]
prereq = [76]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference：自定义类创建"
url = "https://docs.python.org/3/reference/datamodel.html#customizing-class-creation"

[[doc_refs]]
title = "Tutorial 9.10：元类"
url = "https://docs.python.org/3/tutorial/classes.html#metaclasses"
+++

# 类是对象，type 是造类的东西

`class` 语句执行时，Python 调用 `type(名字, 基类, 属性字典)` 造出类对象。定制这个过程有两种方式：**`__init_subclass__`（首选）** 和 **元类（核武器）**。99% 的需求用前者。

## 类创建时的自动钩子

```python
class Plugin:
    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry[cls.__name__] = cls


class JSONPlugin(Plugin):
    pass


class CSVPlugin(Plugin):
    pass


print(sorted(Plugin.registry))
```

```expect
['CSVPlugin', 'JSONPlugin']
```

**每定义一个子类，`__init_subclass__` 就自动执行一次**——不用装饰器、不用元类，注册表模式一行钩子搞定。它就是"元类"需求的官方降压版。

## `type` 在工作

```python
klass = type("Dynamic", (), {"value": 42})

print(klass, klass.value)
print(isinstance(klass, type))
```

```expect
<class '__main__.Dynamic'> 42
True
```

`class` 语句与 `type()` 调用等价。动态创建类（插件、根据配置生成）就是直接调 `type`。

## 元类：定制"造类"本身

```python
class AutoRepr(type):
    def __new__(mcls, name, bases, ns):
        def __repr__(self):
            fields = ", ".join(f"{k}={v!r}" for k, v in ns.items() if not k.startswith("_"))
            return f"{name}({fields})"
        ns["__repr__"] = __repr__
        return super().__new__(mcls, name, bases, ns)


class Item(metaclass=AutoRepr):
    color = "red"
    size = 10


print(Item())
```

```expect
Item(color='red', size=10)
```

元类的 `__new__` 在类**创建时**修改它的属性字典——这是它能做 `__init_subclass__` 做不到的事（比如改写方法、限制接口）。代价是可读性、继承冲突、生态兼容（工具对元类的假设）。

> [!tip] 判断顺序：能用钩子，不用元类
> 需求清单：注册子类 → `__init_subclass__`；校验子类属性 → `__init_subclass__`；自动加方法 → 也常能用继承或装饰器。**只有在"必须控制类本身的创建过程"**（如抽象接口的强制、DSL 解析）时才上元类。tim Peters 的名言：写普通代码 99% 的人永远不需要元类。

```quiz
question = "想「每定义一个子类就自动注册进字典」，最小改动的写法是？"
options = [
  "给基类写 __init_subclass__，里面把 cls 存进注册表",
  "给每个子类手动加装饰器",
  "写一个元类重写 __new__",
  "用 type() 动态创建所有子类"
]
answer = 0
explain = "__init_subclass__ 正是为这个场景设计的：子类定义时自动触发，基类一行钩子，子类零感知。装饰器要求每个子类都标注；元类在这里是杀鸡用牛刀。"
```

## 小结

- `class` 语句 ≈ `type(name, bases, ns)`；类是 `type` 的实例。
- `__init_subclass__` 是子类定义时的自动钩子，注册表首选。
- 元类 `__new__` 能改类的属性字典，是最后手段。
- 99% 的"元类需求"用 `__init_subclass__` 就够了。
