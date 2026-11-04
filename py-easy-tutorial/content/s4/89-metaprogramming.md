+++
id = "s4-89-metaprogramming"
order = 89
stage = "s4"
official_group = "advanced"
title = "元编程实战"
concepts = ["dynamic class", "registry", "plugin system", "__init_subclass__"]
prereq = [88]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：type 动态创建类"
url = "https://docs.python.org/3/library/functions.html#type"

[[doc_refs]]
title = "Tutorial 9.10：元类"
url = "https://docs.python.org/3/tutorial/classes.html#metaclasses"
+++

# 写代码的代码

元编程 = **用代码生成/注册/改造代码**。前几课的钩子（`__init_subclass__`、描述符）都是它的零件，这一课把零件装配成真实的插件系统。

## `type` 动态建类

```python
def make_model(name: str, fields: list[str]):
    def __init__(self, **kwargs):
        for field in fields:
            setattr(self, field, kwargs.get(field))

    return type(name, (), {"__init__": __init__})


User = make_model("User", ["name", "age"])
u = User(name="Ada", age=36)
print(u.name, u.age)
```

```expect
Ada 36
```

`type(名字, 基类元组, 属性字典)` 与 `class` 语句完全等价。字段来自运行时数据（用户输入、数据库 schema）时，动态建类是唯一选择。

## 插件系统：钩子 + 注册表 + 统一入口

```python
class Plugin:
    """基类：定义接口 + 自动注册。"""
    registry: dict[str, type["Plugin"]] = {}
    name = "plugin"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry[cls.name] = cls

    def run(self, data: dict) -> str:
        raise NotImplementedError


class Upper(Plugin):
    name = "upper"

    def run(self, data):
        return data["text"].upper()


class Reverse(Plugin):
    name = "reverse"

    def run(self, data):
        return data["text"][::-1]


def process(kind: str, text: str) -> str:
    plugin = Plugin.registry[kind]()
    return plugin.run({"text": text})


print(process("upper", "hello"))
print(process("reverse", "hello"))
print(sorted(Plugin.registry))
```

```expect
HELLO
olleh
['reverse', 'upper']
```

三层分工：**基类**定义接口与注册表（`__init_subclass__` 自动登记）；**子类**只声明 `name` 与 `run`；**入口函数**按名字取插件。新增一种处理方式 = 增加一个子类，`process` 一行不改。

> [!warn] 元编程的可读性代价
> 插件系统让"谁会被调用"变成运行时才能回答的问题——IDE 跳转、静态检查都变弱。规则：**注册入口必须唯一且显式**（这里是 `Plugin.registry`），并在注册表旁边写清有哪些插件。魔法可以被理解，但不可以被隐藏。

```quiz
question = "插件系统里 `__init_subclass__` 替代了传统写法中的哪一步？"
options = [
  "替代了每个插件手写 @register 装饰器",
  "替代了 run 方法的实现",
  "替代了插件的单元测试",
  "替代了 import 语句"
]
answer = 0
explain = "__init_subclass__ 在子类定义时自动执行注册，等于把「装饰器登记」这一步内置到基类。子类只需继承，忘写装饰器这种事故不再可能。"
```

## 小结

- `type(name, bases, ns)` 动态建类，字段可来自运行时数据。
- 插件系统 = 接口基类 + `__init_subclass__` 自动注册 + 统一入口。
- 注册入口必须唯一显式，否则魔法失控。
- 元编程的收益是消灭重复代码，代价是静态可见性。
