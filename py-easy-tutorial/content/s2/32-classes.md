+++
id = "s2-32-classes"
order = 32
stage = "s2"
official_group = "moderate"
title = "类与实例"
concepts = ["class", "__init__", "self", "instance attribute", "class attribute"]
prereq = [31]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 9.3：类定义初步"
url = "https://docs.python.org/3/tutorial/classes.html#a-first-look-at-classes"

[[doc_refs]]
title = "Language Reference §3.3：自定义类"
url = "https://docs.python.org/3/reference/datamodel.html#customizing-class-creation"
+++

# 类是模板，实例是复印件

类定义一种东西"长什么样"；实例是照着它造出来的具体对象。`__init__` 不是构造函数本体（构造是 `__new__`），它是**实例创建后的初始化钩子**——记住这个措辞，后面讲元类时不困惑。

## self 是谁

```python
class Counter:
    def __init__(self):
        self.n = 0

    def bump(self):
        self.n += 1
        return self.n


c = Counter()
c.bump()
c.bump()
print(c.bump())

d = Counter()
print(d.bump())
```

```expect
3
1
```

`self` 就是"这个实例本身"。`c.bump()` 等价于 `Counter.bump(c)`——`self.n` 改的是 `c` 自己的属性，所以两个计数器互不干扰。

## 类属性 vs 实例属性

```python
class Dog:
    kind = "犬科"

    def __init__(self, name):
        self.name = name


a = Dog("旺财")
b = Dog("小黑")
print(a.kind, b.kind, Dog.kind)

a.kind = "特殊"
print(a.kind, b.kind, Dog.kind)
```

```expect
犬科 犬科 犬科
特殊 犬科 犬科
```

给 `a.kind` 赋值**没有修改类属性**，而是给实例 a 新建了一个属性，把它遮住了——和第 3 课的名字绑定是同一个机制。真正改类要用 `Dog.kind = "..."`。

> [!warn] 不要用类属性存可变默认值
> `class Dog: toys = []` 会让**所有实例共享同一个列表**。要每只狗有自己的列表，就在 `__init__` 里 `self.toys = []`。这是第 8 课嵌套列表陷阱的另一个变体。

## 方法也是属性

```python
class Calc:
    def add(self, a, b):
        return a + b


c = Calc()
print(Calc.add(c, 1, 2))
print(c.add(3, 4))
print(type(Calc.add).__name__)
```

```expect
3
7
function
```

`Calc.add` 就是一个普通函数；`c.add` 是绑定后的方法（原理在第 55 课讲描述符时拆开）。所以方法内漏写 `self` 参数，调用时会报"参数数量不对"——报错点在参数，不在 self。

```quiz
question = "`class Dog: toys = []`，然后 `a = Dog(); b = Dog()`，执行 `a.toys.append(\"球\")` 后 `b.toys` 是什么？"
options = ["[]", "['球']", "None", "报错：无法访问"]
answer = 1
explain = "toys 是类属性，所有实例共享同一个列表对象。append 是原地修改，b 看到的也是 ['球']。要每只狗独立，必须在 __init__ 里 self.toys = []。"
```

## 小结

- `__init__` 是初始化钩子，`self` 就是实例本身。
- 类属性被所有实例共享；给实例赋值只是"遮住"，不是改类。
- 可变类属性是共享状态，别这么写。
- 方法在类上叫函数，在实例上叫绑定方法。
