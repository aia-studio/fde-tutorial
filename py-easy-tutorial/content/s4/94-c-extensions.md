+++
id = "s4-94-c-extensions"
order = 94
stage = "s4"
official_group = "resources"
title = "C 扩展入门"
concepts = ["ctypes", "c extension", "numpy", "build process"]
prereq = [93]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：ctypes"
url = "https://docs.python.org/3/library/ctypes.html"

[[doc_refs]]
title = "Python Packaging：C/C++ 扩展"
url = "https://packaging.python.org/en/latest/guides/building-and-distributing-packages-with-setuptools/#extending-or-customizing-setuptools"
+++

# 走到解释器边界（只读延伸）

这是本阶段第一门**只读课**：不判题、部分代码不可运行。当 Python 层的优化（第 80 课）已经到顶，把热点下沉到 C 是最后一级火箭。这一课看清边界在哪、怎么跨过去、代价是什么。

## ctypes：不写 C 也能调 C

```python
import ctypes


class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]


p = Point(3, 4)
print(p.x, p.y, ctypes.sizeof(p))
```

```expect
3 4 8
```

`ctypes` 能直接加载动态链接库（Windows 的 DLL、Linux 的 .so）并调用其导出函数——`libc` 的数学函数、系统 API、自己编译的 `.so` 都行。上面用 `Structure` 定义了一个与 C 结构体布局一致的对象：两个 c_int 正好 8 字节。

## 手写扩展的流程（不可在沙箱运行）

```c
// mymod.c —— 概念示意，实际还需模块初始化与错误处理
#include <Python.h>

static PyObject *square(PyObject *self, PyObject *args) {
    long n;
    if (!PyArg_ParseTuple(args, "l", &n))
        return NULL;
    return PyLong_FromLong(n * n);
}
```

```text
编译（三种路径）：
1. setuptools：在 pyproject.toml 声明 ext_modules，pip install 时自动编译
2. 手动：cl /LD mymod.c /I<include>（Windows）或 gcc -shared（Linux/macOS）
3. scikit-build / meson：需要 cmake 的复杂项目

产物：mymod.cp315-win_amd64.pyd → import mymod 直接可用
```

发布含 C 扩展的包，**每个平台 × 每个 Python 版本都要出一个 wheel**（`cp315-cp315-win_amd64` 就是这个含义），社区用 cibuildwheel 自动化。这也是"纯 Python 包随处可装、C 扩展包要挑平台"的根本原因。

## 性能边界：什么时候值得

| 情况 | 结论 |
|---|---|
| 循环里有大量纯数值计算 | 下沉收益巨大（numpy 就是这么做的） |
| 主要在等 IO | 下沉无用——瓶颈在网络，不在解释器 |
| 只是函数调用太慢 | 先试算法与数据结构（第 66 课） |

```quiz
question = "含 C 扩展的包发布到 PyPI，与纯 Python 包最大的差别是？"
options = [
  "需要更多文档",
  "每个平台与 Python 版本组合都要构建对应的 wheel，否则用户需本地编译",
  "不能使用 pyproject.toml",
  "必须开源 C 代码"
]
answer = 1
explain = "C 扩展的 wheel 与解释器 ABI、平台绑定（如 cp315-win_amd64），矩阵很大，通常用 cibuildwheel 在 CI 上批量构建。纯 Python 包只有一个 universal wheel。"
```

## 小结

- `ctypes` 免编译调用动态库；`Structure` 与 C 结构体布局对齐。
- 手写扩展 = 实现 PyInit + 构建 wheel，按平台 × 版本出矩阵。
- 下沉 C 的前提是 CPU 热点；IO 密集场景无收益。
- 本课与 95、96 均为只读延伸：不判题，示例以可复制的真实命令为主。
