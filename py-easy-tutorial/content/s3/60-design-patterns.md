+++
id = "s3-60-design-patterns"
order = 60
stage = "s3"
official_group = "moderate"
title = "Pythonic 设计模式"
concepts = ["singleton", "factory", "strategy", "observer", "pythonic"]
prereq = [59]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：dataclasses 与枚举"
url = "https://docs.python.org/3/library/dataclasses.html"

[[doc_refs]]
title = "PEP 8：编程建议"
url = "https://peps.python.org/pep-0008/#programming-recommendations"
+++

# 用语言特性替代模式

GoF 的 23 种模式诞生于没有闭包、没有一等函数、没有字典的语言。Python 里大约三分之一被语言特性直接消化了。这一课讲四个最常用的，以及它们的 Pythonic 写法。

## 单例：模块就是单例

```python
# config.py 里写：
# settings = load()   ← 全模块只有这一份
#
# 别处：
# from config import settings

class App:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


a = App()
b = App()
print(a is b)
```

```expect
True
```

Java 需要 `getInstance()` 双重检查锁；Python 里**模块天然是单例**（第 18 课的导入缓存）。必须用类时才用 `__new__`，且并发场景要加锁。

## 策略：字典代替 if 链

```python
def discount_none(price):
    return price

def discount_vip(price):
    return price * 0.8

STRATEGIES = {
    "none": discount_none,
    "vip": discount_vip,
    "svip": lambda p: p * 0.6,
}


def price_for(level, price):
    return STRATEGIES.get(level, discount_none)(price)


print(price_for("vip", 100), price_for("svip", 100), price_for("别的", 100))
```

```expect
80.0 60.0 100
```

面向对象版需要一个 `Strategy` 接口 + N 个子类；Python 里**函数就是一等公民**，字典直接把键映射到行为。新增策略就是加一个函数。

## 观察者：回调列表

```python
class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event, callback):
        self._subscribers.setdefault(event, []).append(callback)

    def emit(self, event, data):
        for callback in self._subscribers.get(event, []):
            callback(data)


bus = EventBus()
bus.subscribe("order", lambda d: print("邮件：", d))
bus.subscribe("order", lambda d: print("库存：", d))

bus.emit("order", {"id": 1})
```

```expect
邮件： {'id': 1}
库存： {'id': 1}
```

发布者和订阅者互不知道对方存在。第 40 课的"注册表装饰器"可以再进一步：用 `@bus.on("order")` 语法注册。

## 工厂：dict + 类

```python
def make_json():
    return {"type": "json"}

def make_csv():
    return {"type": "csv"}

FACTORY = {"json": make_json, "csv": make_csv}

obj = FACTORY["json"]()
print(obj)
```

```expect
{'type': 'json'}
```

> [!tip] 判断标准：模式是"问题的名字"，不是"要写的东西"
> 当你发现自己在写"防重复创建""按类型分支""通知多个对象"时，去查那个模式对应 Python 的哪种惯用法。反过来先写工厂单例观察者，再找地方用——那叫过度设计。

```quiz
question = "Python 里最自然的单例实现是？"
options = [
  "模块级对象：config.py 里的 settings",
  "每个类加 __new__ 判断",
  "全局变量 global settings",
  "装饰器加锁"
]
answer = 0
explain = "模块在导入缓存里天然只有一份（第 18 课），settings 自动是单例，无锁无样板。__new__ 方案只在「必须用类承载」时才用，且并发初始化要自己处理。"
```

## 小结

- 单例 → 模块；策略 → 字典映射函数；观察者 → 回调列表；工厂 → dict + 类。
- 语言特性（一等函数、导入缓存）消化了大多数经典模式。
- 模式是"问题的名字"：先有重复出现的问题，再套模式。
