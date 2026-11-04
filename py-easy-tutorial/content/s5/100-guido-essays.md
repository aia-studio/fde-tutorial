+++
id = "s5-100-guido-essays"
order = 100
stage = "s5"
official_group = "general"
title = "读 Guido 的设计文章"
concepts = ["design philosophy", "readability", "BDFL", "explicit"]
prereq = []
standalone = true
requires_python = "3.15"
allow_network = false
xp = 10

[[doc_refs]]
title = "Guido 的文章合集（python.org/doc/essays）"
url = "https://www.python.org/doc/essays/"

[[doc_refs]]
title = "Design Principles（设计原则幻灯片）"
url = "https://www.python.org/doc/essays/ppt/"
+++

# 设计者的自白

Guido van Rossum 写过一组短文与幻灯片，解释 Python 为什么长成这样。读它们的价值不是"考据历史"，而是**学会用设计者的眼光评价自己的代码**：这段代码，读者十秒后还能看懂吗？

## 原则一：为可读性优化，为写的人让路

代码的读者远多于作者，而且读者常常是三个月后的自己。所以 Python 的关键字是英文全拼（`not`、`in`、`and`），宁可多敲几个字符也要让句子像英语：

```python norun
# 一眼可读：像英语句子
if user is not None and user.is_active:
    send(user)

# 信息等价，但读者要先解码符号
if user != None and user.is_active == True:
    send(user)
```

第二段多出两处噪音：`!= None` 要翻译一遍，`== True` 是冗余比较。**可读性优先**就是删掉这些让读者减速的东西。

## 原则二：一种明显的方式

> There should be one — and preferably only one — obvious way to do it.

语法不提供花括号、不提供 `++`、不提供三元的多套写法——**选择少，代码风格就趋同**，读别人的代码像读自己的。这条原则的反面教材是"十个团队十种 ORM 用法"的生态碎片化。

## 原则三：显式优于隐式

```python norun
# 显式：来源、意图都在调用处
from collections import Counter
counts = Counter(words)

# 隐式：* 导入把来源藏起来，撞名后查半天
from collections import *
from strings import *
counts = Counter(words)  # 这是谁的 Counter？
```

`import *`、隐式类型转换、魔法属性注入——这些都"能用"，但都把成本转嫁给了读者。显式的代价是几个字符，收益是可追溯性。

> [!why] 为什么没有花括号
> Guido 在多篇文章里提过同一个理由：**缩进本来就是代码结构的一部分**，花括号只是把同一信息写两遍，还制造了"缩进与括号不一致"这类纯 Python 没有的 bug。强制缩进把"排版问题"升级成了"语法问题"，风格自然统一。

```quiz
question = "下面哪个写法违背了「显式优于隐式」？"
options = [
  "from collections import Counter",
  "from collections import *",
  "with open(path) as f:",
  "return f\"{name} done\""
]
answer = 1
explain = "import * 把来源信息从代码里抹掉了，Counter 来自哪个模块要靠猜，还有撞名风险。显式导入（哪怕名字长）让每一行都自解释。"
```

## 小结

- 代码的读者远多于作者，可读性优先于书写速度。
- 一种明显的方式：语法选择少，风格趋同，读谁都顺。
- 显式导入、显式 None 判断、显式参数——把来源写出来。
- 强制缩进消灭了"括号与缩进不一致"这整类问题。
