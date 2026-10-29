+++
id = "s2-33-inheritance"
order = 33
stage = "s2"
official_group = "moderate"
title = "继承与组合"
concepts = ["inheritance", "super", "composition", "isinstance", "override"]
prereq = [32]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 9.5：继承"
url = "https://docs.python.org/3/tutorial/classes.html#inheritance"

[[doc_refs]]
title = "Tutorial 9.6：私有变量"
url = "https://docs.python.org/3/tutorial/classes.html#private-variables"
+++

# 先问"是什么"，再问"有一个"

继承表达"is-a"（狗是动物），组合表达"has-a"（车有引擎）。Python 两种都支持，但社区共识是：**优先组合**。这一课讲清两种写法和 `super()` 的真实行为。

## 继承与方法覆盖

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."


class Dog(Animal):
    def speak(self):
        return f"{self.name}: 汪"


print(Dog("旺财").speak())
print(Animal("无名").speak())
print(isinstance(Dog("旺财"), Animal))
```

```expect
旺财: 汪
...
True
```

子类覆盖 `speak` 后，父类版本被遮住。`isinstance` 沿继承链为 True。

## `super()` 是"下一个"，不是"父类"

```python
class Base:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return f"Base({self.name})"


class Sub(Base):
    def __init__(self, name, extra):
        super().__init__(name)
        self.extra = extra

    def describe(self):
        return super().describe() + f" + {self.extra}"


print(Sub("x", "y").describe())
```

```expect
Base(x) + y
```

`super().__init__(name)` 把父类的初始化逻辑接过来，再补充自己的部分。**漏写这一行是继承最常见的 bug**：子类自己写了 `__init__`，父类的属性就没了。

> [!why] super() 为什么不直接写类名
> 直接写 `Base.__init__(self, name)` 在单继承时没问题，但多继承时会把某个祖先初始化两次。`super()` 按 MRO 找"下一个"类，钻石结构也能每个类只初始化一次——第 78 课展开。

## 组合：把零件装进去

```python
class Engine:
    def start(self):
        return "引擎启动"


class Car:
    def __init__(self):
        self.engine = Engine()

    def start(self):
        return self.engine.start()


print(Car().start())
print(isinstance(Car(), Engine))
```

```expect
引擎启动
False
```

`Car` 持有一个 `Engine`，把"启动"委托给它。`isinstance` 不成立——组合不建立类型关系，这正是它灵活的原因：换引擎不用动 `Car` 的继承树。

## 怎么选

| 关系 | 用法 | 例子 |
|---|---|---|
| A 是一种 B | 继承 | 金毛 → Dog → Animal |
| A 有一个 B | 组合 | Car → Engine |
| A 需要用到 B 的功能 | 组合/参数 | 日志器作为参数传入 |

继承树深超过 2~3 层，基本说明该用组合了。**"复用代码"不是继承的理由，"类型确实是同一种"才是。**

```quiz
question = "想让 `PdfDoc` 和 `WordDoc` 都能被 `save(doc)` 处理，且 `save` 不改代码。更适合哪种设计？"
options = [
  "让两个类继承自同一个基类，save 接收基类",
  "给两个类各自写一个 save 方法，save 里 if isinstance 判断",
  "两个类互不相关，save 里复制两份代码",
  "把 save 写成全局函数，里面用全局变量区分类型"
]
answer = 0
explain = "这是「多态」的典型场景：save 只依赖基类接口，调用 doc.save() 时自动分发到各自的实现。isinstance 链条每加一种文档就要改一次，是维护黑洞。"
```

## 小结

- 继承是 is-a，组合是 has-a；默认选组合。
- 子类写了 `__init__` 就必须 `super().__init__`，否则父类属性丢失。
- `super()` 按 MRO 找"下一个"类，不是字面上的"父类"。
- `isinstance` 沿继承链成立，组合不成立。
