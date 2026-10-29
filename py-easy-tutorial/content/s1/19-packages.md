+++
id = "s1-19-packages"
order = 19
stage = "s1"
official_group = "beginner"
title = "包与项目结构"
concepts = ["package", "__init__.py", "namespace package", "relative import", "layout"]
prereq = [18]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 6.4：包"
url = "https://docs.python.org/3/tutorial/modules.html#packages"

[[doc_refs]]
title = "Python Packaging User Guide：项目布局"
url = "https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/"
+++

# 目录也是模块

包就是"带 `__init__.py` 的目录"。这层目录结构决定了 `import` 怎么找、名字怎么拼。项目一大，布局选错会连带影响测试、打包、导入路径三件事。

## 建一个包，然后导入它

```python
import os
import sys

os.makedirs("shop", exist_ok=True)
with open("shop/__init__.py", "w", encoding="utf-8") as f:
    f.write('VERSION = "1.0"\n')
with open("shop/cart.py", "w", encoding="utf-8") as f:
    f.write("def total(prices):\n    return sum(prices)\n")

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from shop import cart
import shop

print(cart.total([10, 20, 30]))
print(shop.VERSION)
```

```expect
60
1.0
```

`shop/__init__.py` 在包被导入时执行，通常用来放版本号、导出公共接口。`shop/cart.py` 是子模块，导入名是 `shop.cart`。

## 点号就是层级

```python
import os
import sys

os.makedirs("shop2", exist_ok=True)
with open("shop2/__init__.py", "w", encoding="utf-8") as f:
    f.write("")
with open("shop2/pricing.py", "w", encoding="utf-8") as f:
    f.write("RATE = 0.9\n")

sys.path.insert(0, os.getcwd())
import shop2.pricing

print("shop2.pricing" in sys.modules)
print(shop2.pricing.RATE)
```

```expect
True
0.9
```

`import shop2.pricing` 会把 `shop2` 和 `shop2.pricing` 都放进 `sys.modules`，但只把 `shop2` 绑到当前命名空间——所以访问要写全路径。

## 相对导入只认包上下文

```python
# shop/cart.py 里可以写：
# from . import pricing
# from .pricing import RATE
```

`from . import x` 里的点表示"当前包"。它**只在包内被导入时有效**；直接 `python shop/cart.py` 运行会报 `ImportError: attempted relative import with no known parent package`——因为此时 `__package__` 是空的。

这就是为什么包内模块要用 `python -m shop.cart` 运行（第 1 课讲过）。

> [!tip] 布局选择的实际影响
> `src/` 布局（`src/mypkg/...`）能防止"在仓库根目录下 import 到未安装的包"，测试跑的是安装后的版本，更接近用户环境。小项目用扁平布局没问题，要发布就换 `src/`。

```quiz
question = "在包 `app/` 内的 `app/main.py` 里写 `from . import config`，直接执行 `python app/main.py` 会怎样？"
options = [
  "正常导入同级模块",
  "报 ImportError：没有已知的父包",
  "自动把 app 加入 sys.path 后成功",
  "报 SyntaxError"
]
answer = 1
explain = "直接运行文件时该文件是顶层脚本，__package__ 为空，解释器不知道父包是谁，相对导入无从解析。改用 python -m app.main。"
```

## 小结

- 包 = 含 `__init__.py` 的目录；子模块用点号访问。
- `__init__.py` 在导入包时执行，适合放版本号和导出。
- 相对导入（`from . import x`）只在包上下文里有效，要用 `-m` 运行。
- 要发布的项目优先 `src/` 布局，避免拿到未安装的源码。
