# 交互式 Python 教程

一个**在本地跑、代码真的会执行**的 Python 教程。103 课按难度分成六个阶段，从「能跑」到「能读 CPython 源码」。不需要 pip 安装任何东西，不需要 Node 工具链，不联网。

## 要求与平台

- **Python 3.15 或更高**。低于这个版本会直接退出并提示，不做降级运行。
- 平台：Windows 全流程实测；macOS/Linux 的代码路径（`killpg`、`RLIMIT_AS`、`libc` 路径）按文档实现，欢迎反馈。

## 要求

- **Python 3.15 或更高**。低于这个版本会直接退出并提示，不做降级运行。

## 启动

```bash
conda activate pytest      # 或任何装了 3.15 的环境
python app.py
```

会自动选端口并打开浏览器。常用参数：

```bash
python app.py --port 8800     # 指定端口
python app.py --no-browser    # 不开浏览器
```

## 目录结构

```
app.py                 启动器（含版本前置检查）
build.py               内容编译：content/*.md → web/data/*.json
tutorial/
  schema.py            课程元数据与难度曲线校验
  markdown.py          Markdown 子集 → 块数组
  runner.py            子进程执行、流式输出、超时、进程树清理
  server.py            静态服务 + API + SSE
content/s0..s5/        课程源文件（Markdown + TOML front matter）
web/                   前端（原生 ES Module，无构建）
  data/                编译产物
tests/                 unittest（项目零依赖，不用 pytest）
```

## 开发命令

```bash
python build.py            # 编译，只做结构校验
python build.py --check    # 额外真跑每个代码块，比对 expect 输出
python build.py --strict   # 缺课也算错误（发布前用）
python -m unittest discover -s tests -v
```

## 写一门课

文件放在 `content/s<阶段>/` 下，`+++` 之间是 TOML front matter：

```toml
+++
id = "s0-01-install-repl"
order = 1
stage = "s0"                  # s0..s5
official_group = "beginner"   # beginner|moderate|advanced|general|resources
title = "安装、解释器与运行方式"
concepts = ["interpreter", "repl"]
prereq = []
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Using Python"
url = "https://docs.python.org/3/using/index.html"
+++
```

正文支持的语法：标题、段落、列表、表格、引用、行内代码/粗体/斜体/链接，以及四种围栏：

````
```python          # 可运行、可编辑
print("hi")
```

```expect          # 紧跟上一个代码块，构建期会真跑并比对
hi
```

```quiz
question = "..."
options = ["A", "B"]
answer = 1
explain = "..."
```
````

提示块用引用语法：`> [!warn] 标题`（`note`/`tip`/`warn`/`danger`/`why`）。

**构建期会强制检查**：id 唯一、order 不重复、`prereq` 编号必须小于本课、跨阶段只能指向更早阶段、每个可运行代码块真的能跑、`expect` 与实际输出一致。任一条不过，`build.py` 直接失败。

## 当前进度

M0–M4 五个里程碑与 **S0–S5 全部六阶段 103 课**已全部交付（起步 14、组织 17、抽象 22、工程 20、深入 23、参考 7）。

- 执行内核：真实子进程 + 流式输出、`input()` 交互（输入会重置超时计时）、超时杀整棵进程树、输出上限、内存上限（Windows Job Object / POSIX rlimit）、默认禁网（放行回环）、traceback 定位到编辑器行号。
- 阅读体验：Python 语法高亮编辑器（自动缩进、括号配对）、页内标题树、`Ctrl+K` 全站搜索（可跳到小节）、快捷键表、深色/浅色主题。
- 判题与进度：练习块在沙箱里跑隐藏测试、逐条显示通过/失败原因、提示阶梯（连续失败 3 次解锁参考实现）、XP 与连续天数、进度落盘到 `.data/progress.json`（原子写 + 备份）、导出/导入。
- 单步可视化：`step` 块基于 `sys.settrace` 逐步执行，行高亮 + 调用栈 + 局部变量卡；可变对象带同色身份标记（两个名字指向同一列表 → 同色），支持播放/单步/跳到结束。

> `build.py --check` 会真跑所有代码块与练习参考答案（并行，全量约 18 秒）；改完单课用 `--only <编号>` 只需 3 秒。

> `build.py --check` 会真跑所有代码块与练习参考答案，课程越多越慢（当前约 3 分钟）。

写作约定见 `docs/AUTHORING.md`。
