# 课程写作约定

写给后面继续补课的人（也包括我自己）。这些规则不是审美偏好，多数是 `build.py --check` 会直接卡住的硬约束。

## 一、文件与命名

```
content/<阶段>/<序号>-<短横线标题>.md
```

- 阶段目录：`s0`…`s5`，与 `stage` 字段一致。
- 文件名的序号只是为了排序方便，**课程编号以 front matter 的 `order` 为准**。
- 一个文件一门课，不拆多文件。

## 二、front matter（TOML）

```toml
+++
id = "s0-06-strings"          # 小写字母/数字/连字符，全局唯一
order = 6                     # 1..103，连续，不重复
stage = "s0"                  # s0..s5
official_group = "beginner"   # beginner|moderate|advanced|general|resources
title = "字符串：不可变序列"
concepts = ["str", "slicing", "fstring"]
prereq = [5]                  # 必须是更小的编号；跨阶段只能指向更早阶段
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 3.1.2：字符串"
url = "https://docs.python.org/3/tutorial/introduction.html#strings"
+++
```

`prereq` 不是装饰：`build.py` 会校验它必须小于本课编号、且不能指向更晚的阶段，第 1 课之外的课不允许"孤岛"（无前置又没标 `standalone`）。

## 三、正文骨架

固定七段，顺序别乱：

1. **开头 2–3 段**：这课解决什么问题。不要"欢迎来到本节"，直接说事。
2. **概念 + 可运行示例**：讲一个点，给一段能跑的代码。
3. **反例/陷阱**：至少一个"看起来对但其实错"的写法。
4. **表格或对照**：把并列概念压成一张表。
5. **测验**：1 题，放在主要概念讲完之后、小结之前。
6. **小结**：4–6 条，每条一行，能当速查卡。
7. **官方链接**：`doc_refs` 自动渲染，正文不用重复贴。

单课长度参考：**正文 600–1000 字，代码块 3–5 个，测验 1 个**。超过就拆课，少于就并课。

## 四、代码块的三条硬规则

### 1. 每个代码块独立运行

**块与块之间不共享变量**。每段代码在独立子进程里执行，所以：

```python
# 第二个块里不能直接用上一个块定义的 greet
def greet(name):
    ...
```

需要复用的定义，在块内重新写一遍。写课件时这是最容易踩的坑，报错信息是 `NameError`。

### 2. 能预期输出的块，一定写 `expect`

```python
print(2 ** 10)
```

```expect
1024
```

`expect` 紧跟代码块，构建期会真跑并逐字比对（忽略行尾空白）。**没有 `expect` 的块也能过校验，但等于放弃了这条防线**——除了演示交互（`input()`）或输出不可预期的块，都应该写。

### 3. `expect` 必须是确定性的

以下都不能进 `expect`：

| 不要 | 原因 | 替代 |
|---|---|---|
| 对象地址 `<... at 0x...>` | 每次不同 | 只断言类型或布尔结果 |
| `print({...})` 集合 | 字符串哈希随机化 | `print(sorted(s))` |
| `id()` 的具体值 | 每次不同 | `print(a is b)` |
| 完整版本号 | 随环境变 | `print(sys.version_info[:2] >= (3, 15))` |
| 浮点末位 | 平台差异 | 用 `isclose` 或格式化到固定位数 |

## 五、测验（quiz）

用围栏 TOML：

````
```quiz
question = "……"
options = ["A", "B", "C", "D"]
answer = 1
explain = "……"
```
````

- 4 个选项，正确答案**不要总放第一个**。
- 错误选项要"像真的"：常见误解比明显胡话更有教学价值。
- `explain` 必须解释**为什么**，而不是重复正确答案。

## 六、练习（exercise）

````
```exercise
id = "s0-14-ex1"
title = "用 zip 对齐两个列表"
prompt = "给定 `names` 和 `scores`，生成 `pairs`。"
starter = """
names = ["Ada", "Bob"]
scores = [90, 85]
# 在下面写
"""
solution = """
names = ["Ada", "Bob"]
scores = [90, 85]
pairs = list(zip(names, scores))
"""
tests = [
  "assert isinstance(pairs, list)",
  "assert pairs[0] == ('Ada', 90)"
]
hints = ["想想 zip 的作用。", "zip 返回迭代器，要 list() 转换。"]
xp = 10
```
````

规则（`build.py --check` 会强制）：

- **`solution` 必填**，且必须通过全部测试——否则构建失败，避免出无解的题。
- `starter` 如果能直接通过全部测试，构建会给 warn：题目太简单。
- 测试**只做断言，不改状态**。多条测试在同一个进程里顺序执行，前面的测试改了全局变量会影响后面。
- 测试里的 `assert` 建议带消息：`assert len(pairs) == 3, '长度应该是 3'`，前端会原样显示。
- `hints` 是**渐进**的：第 1 次失败显示第 1 条，第 2 次显示前 2 条，以此类推；连续 3 次失败会解锁参考实现。
- 一道课 1–2 个练习即可，位置在"小结"之前。

**代码里含 `\n` 时用 TOML 字面量字符串**：`starter` / `solution` 里如果要写 `f.write("a\nb")`，必须用 `'''...'''`。用 `"""..."""` 时 TOML 会把 `\n` 解释成真实换行，生成的 Python 源码直接语法错误（这条踩过一次）。

## 七、语言风格

- 中文正文，术语首次出现保留英文：编码（encoding）、描述符（descriptor）。
- 用"你"，不用"我们"；不用"大家"。
- 不写"很简单""显然"——读者卡住时会觉得自己蠢。
- 一句话说完一件事，长句拆开。
- 代码注释只写"为什么"，不写"是什么"。

## 八、提交前自检

```bash
python build.py --check    # 所有 run 块可执行、expect 一致
python -m unittest discover
```

再人工过一遍：

- [ ] 每段代码都能独立运行，不依赖上一块
- [ ] `expect` 里没有地址、集合、`id()`、版本号
- [ ] 练习的 `starter` 跑不过测试（否则题目白给）
- [ ] 至少一处反例，且说明了为什么会错
- [ ] 测验的干扰项是真实误解，不是凑数
- [ ] 小结能单独当速查卡用
