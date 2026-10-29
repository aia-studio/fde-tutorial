+++
id = "s4-96-c-api"
order = 96
stage = "s4"
official_group = "resources"
title = "C API：对象协议与引用计数"
concepts = ["PyObject", "refcount", "PyArg_ParseTuple", "borrowed reference"]
prereq = [95]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python C API：对象协议"
url = "https://docs.python.org/3/c-api/object.html"

[[doc_refs]]
title = "Python C API：引用计数"
url = "https://docs.python.org/3/c-api/refcounting.html"
+++

# 引用计数显形了

第 81 课说"CPython 靠引用计数回收"。C API 是这个机制**显形**的地方：每个 `PyObject` 都带计数器，每个 API 调用都明确写着"这是新引用还是借用引用"。读一遍 C API，Python 层的所有"约定俗成"都有了物证。

## PyObject 与引用计数

```python
import sys

x = "hello"
base = sys.getrefcount(x)

y = x          # 强引用 +1
print(sys.getrefcount(x) - base)

del y          # 归还
print(sys.getrefcount(x) - base)
```

```expect
1
0
```

C 层对应两条规则：

- **新引用**（new reference）：`PyTuple_GetItem` 之外的大多数"创建/获取"调用——调用方拥有它，用完必须 `Py_DECREF`。
- **借用引用**（borrowed reference）：如 `PyTuple_GetItem`——不拥有，只在使用期内有效；宿主一释放它就悬空。

C 扩展里绝大多数内存 bug 是这两类搞混：该 `Py_DECREF` 的没减（泄漏），不该减的减了（悬空崩溃）。

## 从 C 侧看一个调用

```c
// C API 版本的 "result = parse(text)"（概念示意）
static PyObject *parse(PyObject *self, PyObject *args) {
    const char *text;
    if (!PyArg_ParseTuple(args, "s", &text))   // 解析参数，失败自动设置异常
        return NULL;                           // 返回 NULL = 向 Python 抛异常
    long value = atol(text);
    return PyLong_FromLong(value);             // 返回新引用
}
```

`PyArg_ParseTuple` 的格式串（`"s"`、`"l"`）是 C API 的"类型注解"；返回 `NULL` 等价于 Python 层的 `raise`（异常已在全局状态里设置）。

## 可变的另一面：对象不变性

```text
Python 层观察到的：
- 不可变对象（int/str/tuple）永不改变——所以能当 dict 键
- 可变对象（list/dict）原地修改——引用它的所有名字同步看到

C 层的真实情况：
- 所谓不可变 = 实现 __hash__ 与 __eq__ 后，C 代码"约定"不去改它
- mutable 默认参数、别名共享等陷阱，全是「引用同一个 C 结构体」的表现
```

第 3 课的"名字是标签"、第 53 课的深浅拷贝，到这里都能落回同一条物证：**Python 对象在 C 里就是一个带计数器的结构体，名字只是指针**。

```quiz
question = "C 扩展函数 `PyTuple_GetItem` 返回的是借用引用，这意味着？"
options = [
  "必须立刻 Py_DECREF，否则泄漏",
  "只在宿主对象存活期间使用；不拥有它，不需要也不应该 Py_DECREF",
  "借用引用是线程安全的",
  "借用引用会自动升级为新引用"
]
answer = 1
explain = "借用引用不拥有对象：只要不 Py_DECREF 就不会泄漏；但宿主对象一旦被回收（比如列表被缩小），这个指针就悬空。需要长期持有必须 Py_INCREF 或换成 PyTuple_GetItemRef。"
```

## 小结

- `PyObject` = 对象头（含引用计数）+ 具体数据；一切皆 PyObject。
- C API 区分**新引用**（要 DECREF）与**借用引用**（不可 DECREF）。
- `PyArg_ParseTuple` 是参数层的"类型注解"；返回 NULL 即抛异常。
- Python 层的不可变性、别名共享，在 C 层都是显式的指针操作。
