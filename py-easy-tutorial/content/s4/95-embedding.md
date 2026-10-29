+++
id = "s4-95-embedding"
order = 95
stage = "s4"
official_group = "resources"
title = "嵌入解释器"
concepts = ["embedding", "Py_Initialize", "free-threading", "subinterpreters"]
prereq = [94]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python Packaging：嵌入 Python"
url = "https://docs.python.org/3/extending/embedding.html"

[[doc_refs]]
title = "Library Reference：C API 的初始化与终结"
url = "https://docs.python.org/3/c-api/init.html"
+++

# 反过来：把 Python 装进别的程序

前一课是"用 Python 调 C"；这一课是**反过来**——让 C/C++ 程序（游戏引擎、CAD、Blender 这类软件的脚本接口）内嵌一个 Python 解释器，用脚本驱动宿主。

## 嵌入的最小形态（不可在沙箱运行）

```c
// embed.c —— 概念示意
#include <Python.h>

int main(void) {
    Py_Initialize();                     // 启动解释器
    PyRun_SimpleString("print('hello from embedded python')");
    Py_Finalize();                       // 终结：释放一切解释器资源
    return 0;
}
```

```text
编译与运行（Windows 示意）：
cl embed.c /I<python include> /link <python3x.lib>
embed.exe
→ hello from embedded python
```

三个阶段对应三组 C API：`Py_Initialize`（分配解释器状态、初始化内置模块）、`PyRun_*`（执行字符串或文件）、`Py_Finalize`（终结）。**finalize 之后不能再 Initialize**——这是个单向门，需要重置就用子解释器。

## 子解释器与 per-interpreter GIL

```text
3.12 起：Py_NewInterpreterFromConfig 可创建带独立 GIL 的子解释器
3.14 起：解释器作为一等公民暴露（InterpreterPoolExecutor）
```

每个子解释器有自己的模块缓存与 GIL，**互相之间可以真并行**——这是 free-threading（去 GIL）之外，CPython 官方给出的另一条并发路线。3.15 里它仍在快速演进，生产使用需谨慎评估。

## 现实世界的嵌入长什么样

| 软件 | 内嵌的脚本 |
|---|---|
| Blender | Python 驱动 3D 场景 |
| Unreal / 游戏引擎 | 关卡脚本、UI 逻辑 |
| Sublime / vim 插件 | 编辑器扩展 API |

共同点：宿主是性能敏感的 C/C++ 程序，把"可定制性"外包给 Python——宿主快、脚本灵活，两者各司其职。

```quiz
question = "嵌入 Python 的宿主程序在 `Py_Finalize()` 之后想再跑一段脚本，正确的做法是？"
options = [
  "再次调用 Py_Initialize 并继续使用",
  "finalize 是单向门，需要重新初始化就用子解释器或重启宿主",
  "Py_Finalize 只是清理缓存，解释器还能继续用",
  "调用 Py_ReInit()"
]
answer = 1
explain = "Py_Finalize 释放了模块缓存、类型对象等全部解释器状态，之后再 Py_Initialize 得到的是全新解释器，旧对象指针全部失效。运行期需要隔离/重置时用子解释器。"
```

## 小结

- 嵌入三阶段：Initialize → Run → Finalize，finalize 是单向门。
- 子解释器（3.12+）可带独立 GIL，是并行的新路线。
- 嵌入的典型场景是给性能敏感的宿主加脚本能力。
- free-threading（无 GIL 构建）与子解释器是两条并行演进的路线。
