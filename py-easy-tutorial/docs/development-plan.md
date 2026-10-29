# 交互式 Python 全特性教程 · 开发计划

> 状态：**范围与结构已定稿，待你下"开始"指令**（未开始编码）
> 目标读者：本项目开发者
> 版本：v0.4 / 2026-10-29（v0.3 重排分组，v0.4 最低版本定为 3.15）

---

## 1. 需求评估

### 1.1 对原始需求的判断

原始需求：以 `https://www.python.org/doc/` 为蓝本，做一个**本地运行、互动感强、覆盖 Python 全部特性**的教程。

三点评估结论：

1. **蓝本的六组是"目录"，不是"课程"。** 经核对原始 HTML（2026-10-29，页面标注文档版本 3.15.2），`python.org/doc/` 确实包含 `Beginner`、`Moderate`、`Advanced`、`General`、`Python 3.x Resources` 五组，另有同页的 `Porting from Python 2 to Python 3`。但五组性质不同：

   | 分组 | 实际内容 | 性质 |
   |---|---|---|
   | Beginner | Beginner's Guide（wiki）、Python FAQs | 资源型，指向 wiki |
   | Moderate | Python Periodicals、Python Books | 读物目录 |
   | Advanced | Python Packaging User Guide、In-development Docs、Guido's Essays | 混合：1 个技术指南 + 2 个文献 |
   | General | PEP Index、Python Videos、Developer's Guide | 混合：索引 + 视频站 + 开发指南 |
   | Python 3.x Resources | Tutorial、Library、Language Reference、Extending、C API、Using Python、HOWTOs、Glossary、What's New | **文档栈，可教学** |

   只有最后一组是可展开成课程的参考文档，前四组多为外链目录。
   **决策：五组不再作为首页主入口，降级为课程标签（`official_group`）**；主视图改按难度阶段 S0–S5 分组（理由见 2.1）。课程只从"文档栈"里长出来，资源型条目不做课。逐条取舍见 1.5。
2. **"涵盖所有特性"必须被定义，否则不可验收。** 字面意义上的全覆盖（Language Reference 全章 + 200+ 标准库模块 + C API）等于重写一遍官方文档，且大部分内容不适合"互动教学"形态。
   **决策：用三层边界 + 可审计的覆盖矩阵来定义"全部"**（见 1.3）。
3. **"互动感强"的成本极不均匀。** 运行代码 ≈ 1 份工作量；自动判题 ≈ 2 份；单步执行 + 对象内存图 ≈ 5 份，且是本项目最大的技术风险点。
   **决策：可视化模块独立成层、特性开关隔离，允许它延期而不阻塞其余交付。**

### 1.2 已确认的关键决策

| # | 决策点 | 结论 | 影响 |
|---|---|---|---|
| D1 | 代码执行引擎 | **本地 Python 后端**，真实 CPython 子进程 | 可真实覆盖 asyncio / threading / multiprocessing / 文件 / socket |
| D2 | 覆盖深度 | **标准全覆盖 103 课** | 语言机制全覆盖 + 50 个高频标准库模块 + C API 作延伸阅读 |
| D3 | 内容语言 | **中文讲解 + 英文术语**（首次出现附官方链接） | 便于对照原文档；不做双语切换 |
| D4 | 互动能力 | 判题 + 单步可视化 + 轻量题型 + 进度/知识地图（全选） | 四类都要，按 M2→M4 分期落地 |
| D5 | 内容分组 | **按难度阶段 S0–S5 分组**，官方五组降为标签 | 解决官方分组带来的难度断崖；两套视图共用一份课程数据 |
| D6 | 最低 Python 版本 | **3.15**（低于即拒绝启动） | 与官方稳定文档对齐；删掉逐课降级子系统；本机需先升级 |

### 1.3 "涵盖所有特性"的边界定义

分三层，只有 L1、L2 是"必须可运行、可判题"的硬要求：

- **L1 语言机制（全部覆盖，必须可运行）**
  词法（编码/缩进/标识符/字面量）、数据模型（对象/类型/引用/特殊方法）、执行模型（代码块/帧/名字绑定）、表达式（算术/比较/布尔/位运算/调用/属性/切片/推导式/await）、简单语句（赋值/注解/assert/del/return/yield/raise/import/global/nonlocal）、复合语句（if/while/for/try/with/match/函数/类）、顶层组件与 `__main__`。
- **L2 标准库（50 个高频模块，必须可运行、可判题）**
  其余模块不做逐课讲解，但提供**可检索的模块索引页**（名称 + 一句话定位 + 官方链接），保证"找得到"。
- **L3 生态与系统层（只读延伸阅读，不判题）**
  C API、Extending/Embedding、子解释器、free-threading 展望、打包发布流程、PyPI。这些内容不适合在教程沙箱里跑，做成"延伸阅读 + 可复制的真实命令"。

### 1.4 非目标（明确不做）

- 不做多用户 / 账号 / 云同步（纯本地单用户）。
- 不作为安全沙箱对外提供代码执行服务（见 3.10）。
- 不做第三方库教学（requests / numpy / django 等），仅打包与测试环节提到生态。
- 不做视频、不做移动端优先适配（移动端保证可读，键盘类交互降级）。
- 不逐字翻译或大段摘录官方文档（版权与质量双重原因，见 3.10）。
- 不做在线部署版。

### 1.5 官方条目级取舍（已定稿）

勾选页：`docs/official-docs-selection.html`。**结果：选 17 项，弃 8 项。**

**纳入（17）**：Beginner's Guide、Python FAQs、Python Packaging User Guide、Guido's Essays、PEP Index、Browse Docs、Module Index、What's New 3.15、Tutorial、Library Reference、Language Reference、Extending and Embedding、Python/C API、Using Python、Python HOWTOs、Glossary、Search the docs。

**排除（8）**：Periodicals、Books、Python Videos、Download Docs、Releases by Version（资源型，不建外链区）；In-development Docs（不做版本前瞻）；Developer's Guide（不做 CPython 源码/参与开发课）；Porting 2→3（不做迁移课）。

取舍规则随之确定，写进 `build.py` 的校验：

- 只有**含技术内容**的条目才展开成课程；纯目录/读物一律不占课时，避免"为凑覆盖而编课"。
- 只读类（Extending / C API）**不判题**，标注"沙箱内不可运行"。
- 索引类（Module Index / PEP Index / Glossary）做成**可检索页**，Glossary 另配 1 门交互课。
- 未纳入的 8 项在覆盖矩阵里显式列为"缺口"，禁止课程引用，防止范围悄悄蔓延（见 5.2）。

条目 → 课程的逐条落点见 5.1。**总课时 103**（不是条目课时相加，条目与课程是多对多）。

---

## 2. 产品设计

### 2.1 信息架构

**主视图按难度阶段分组**，官方五组降级为标签筛选（右上角可切换）：

```
首页（知识地图 · 阶段视图）
├── S0 起步   14 课 (1–14)   能跑、能查、能算
├── S1 组织   17 课 (15–31)  函数、模块、文件、异常、测试
├── S2 抽象   22 课 (32–53)  类、协议、装饰器、生成器、注解
├── S3 工程   20 课 (54–73)  日志、打包、测试进阶、类型检查、并发
├── S4 深入   23 课 (74–96)  对象模型、描述符、元类、GC、字节码、C API
├── S5 参考    7 课 (97–103) 术语表、PEP、FAQ、Zen、路线图
├── 索引页 ×3               模块索引(200+)、PEP 索引、文档地图（不占课时）
└── 搜索（Ctrl+K）          标题 + 概念 + 正文标题的本地索引
```

为什么不沿用官方五组当主视图（三条硬理由）：

1. **五组不是难度轴，是资源分类轴。** `Python 3.x Resources` 里同时放着 Tutorial（零基础）和 C API（专家），`General` 里同时放着视频列表和陷阱合集。按它排课，难度必然出现断崖。
2. **原方案把最难的 3 门课塞进了最"入门"的入口。** Resources 被理解成"资源"，结果只有 C 扩展/嵌入/C API 三门只读课，导航语义完全错位。
3. **`Advanced` 会变成 38 课的杂物间。** 打包、测试、类型检查、安全这些工程技能和描述符、元类这些语言机制混在一栏，学习者无法判断自己该从哪进。

替代方案：课程带 `stage`（S0–S5）和 `official_group`（五组原值）两个字段。默认按 `stage` 排，一键切到官方分组视图，两种读法都成立，且不用为了"对齐文档"牺牲难度顺序。

每课固定结构：**动机 → 讲解 → 可运行示例 → 改一改 → 判题 → 小结 → 官方链接**。

### 2.2 学习闭环

```
读 (讲义) → 跑 (真实执行) → 改 (改代码看变化) → 判 (隐藏测试) → 看 (单步/对象图) → 记 (进度与薄弱点)
```

每个环节都必须有可交互产物，不允许出现"只有文字"的课程页。

### 2.3 五种互动单元（内容层的原子类型）

| 单元 | 行为 | 关键设计 |
|---|---|---|
| `code` 可运行 | 点击/`Ctrl+Enter` 在真实解释器执行，流式输出 | 支持虚拟 `input()`；超时 5s 可中断；错误定位到具体行 |
| `code` 可编辑+期望输出 | 运行后与 `expect` 比对，逐字符 diff 高亮 | 用于"预测输出"型练习 |
| `exercise` 判题 | 提交代码 → 跑隐藏测试 → 逐条 PASS/FAIL | 提示阶梯（3 级，逐级解锁）；失败不泄漏答案 |
| `quiz` 轻量题 | 单选 / 多选 / 填空 / 找 Bug（点行号） | 即时反馈 + 解析；答错记录到薄弱点 |
| `step` 单步可视化 | 逐行高亮 + 调用栈 + 堆对象引用图 | 见 2.4 |

**统一交互约定**：所有代码块都可编辑（不是只读的展示块），编辑状态按 lesson + block 存本地；所有输出都可折叠；所有错误都给"人话解释 + 官方异常文档链接"。

### 2.4 单步执行可视化规格（M4 已交付核心）

复刻 Python Tutor 的核心体验，但只针对教学场景裁剪：

- **左侧**：代码，当前行高亮（accent 背景 + 左侧色条），其余行淡色。
- **右侧上**：调用栈（Frame 链，当前帧高亮）。
- **右侧下**：局部变量卡片，可变对象带**色点**表示身份——两个名字指向同一个对象时色点相同，`b = a` 这种引用关系一眼可见。
- **变更反馈**：容器内元素逐层展开（深度 ≤ 2），超出截断并显示"还有 N 项"；当前行抛异常时显示异常消息。
- **交互**：▶ 播放（0.7s/步）/ ◀ ▶ 单步 / ⏭ 结束 / 重置；最后一步显示程序累计输出。
- **深链**：`#/lesson/<id>/step-1` 直接定位到某个 step 块。
- **限额**：3000 步、40 层栈、嵌套展开 ≤ 2 层、字符串截断 60 字符；超出截断并提示。
- **覆盖**：函数调用、递归、闭包、类实例、继承、生成器、可变默认参数陷阱。**不支持** asyncio 与多线程的并发可视化（事件循环调度无法用单栈表达），这些课改用"事件顺序时间线"图示。

**与原设计的差异**：引用关系用"同 oid 同色点"表达，没有做 SVG 贝塞尔箭头（箭头在 800px 宽的阅读栏里画不下，且箭头交叉反而更乱）；时间轴拖动改为步进按钮。如果实测发现确实需要箭头，再作为独立任务加。

### 2.5 页内导航（标题树）

一课写到六七节后，滚动就是主要成本。所以每课自动生成标题树，不靠作者手写目录。

- **锚点**：渲染时给 `h2`/`h3` 编 `sec-N`（按出现顺序），不用中文 slug —— 后者会产生一长串百分号编码，贴不进对话。
- **两种形态，一份数据**：
  - 窄屏（含预览面板）：正文顶部一个 `<details>` 折叠目录，默认展开（≤10 节），标题为「本页目录 · N 节」；
  - 宽屏（≥1260px）：右侧 sticky 导航条，滚动时高亮当前小节，`toc-inline` 自动隐藏。
- **可分享的深链**：`#/lesson/<id>/sec-3`，直接打开就停在对应段落；点目录会写入 history，浏览器后退可回到上一节。
- **标题少于 2 个时不显示**，避免为两个小节加一层噪音。
- **实现位置**：`renderer.js` 负责发锚点，`app.js` 的 `buildToc()` 负责树与滚动高亮（rAF 节流，IntersectionObserver 会更省，但滚动计算在长文里更稳）。

### 2.6 进度、XP 与知识地图

- 进度：`未开始 / 学习中 / 已完成`；每课记录已完成单元。
- XP：完成课程 +20，通过判题 +10（首次），连击日加成。
- 连续天数（streak）：按本地日期计算，允许 1 天宽限。
- 知识地图：按 `stage` 分六层的有向图，节点 = 课程，边 = 前置依赖，颜色 = 状态；点击进入课程。这是首页主体，不是装饰。切换成官方分组视图时，同一组分复用同一套渲染。
- 薄弱点：答错/判题失败的 `concepts` 标签聚合，首页给"建议复习"列表。
- 数据落盘：`<repo>/.data/progress.json`（服务端），支持导出/导入 JSON；`.data/` 不入版本库。

---

## 3. 技术方案

### 3.1 总体架构

```
┌────────────────────────────── 浏览器（无构建，原生 ES Module）──────────────────────────────┐
│  index.html  app.js(router)  renderer(md AST→DOM)  widgets: editor / terminal / quiz        │
│  exercise / stepper(SVG) / mindmap(SVG)   theme(dark|light)   store(progress cache)          │
└───────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                        │ fetch + EventSource(SSE)
┌───────────────────────────────────────┴──────────────────────────────────────────────────────┐
│  app.py  ThreadingHTTPServer（仅标准库，零 pip 依赖）                                          │
│  ├── static        web/ 静态资源（含编译后的 lessons/*.json）                                  │
│  ├── /api/run      RunManager → 子进程（launcher.py）→ stdout/stderr 流                        │
│  ├── /api/trace    TraceRunner → launcher.py --trace → trace.json                             │
│  ├── /api/progress ProgressStore → .data/progress.json（原子写）                               │
│  └── /api/health   Python 版本 + 能力探测（线程/多进程/网络/写文件）                            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴────────────────────┐
                    │  build.py（编译期，标准库）              │
                    │  content/*.md ──► web/data/lessons/*.json │
                    │  校验 schema / 代码块可执行 / 判题可解    │
                    └─────────────────────────────────────────┘
```

### 3.2 运行形态与零依赖原则

**唯一启动方式**：`python app.py`（自动选端口、自动开浏览器）。
清空环境要求：**Python ≥ 3.15，不需要 `pip install` 任何东西**。

启动前置检查（在打开浏览器之前执行）：

- 读 `sys.version_info`，低于 `(3, 15)` 直接退出，打印当前版本、最低要求、下载地址，以及 `py -3.15 app.py` 这种多版本并存时的用法；
- **不做降级运行**。既然最低版本就是目标版本，就不存在"低于标准的解释器"这种中间状态——半套课程跑不了、半套能跑，只会被误判成 bug；
- 附带收益：原设计里 `requires_python` 的逐课降级 UI 整块删掉，M0/M2 少一个子系统；课程代码可以放心用 3.15 语法（`match`、`except*`、PEP 695 泛型、PEP 750 t-string 等），不用为老解释器留后路。

> 当前开发机是 CPython **3.13.14**（`C:\Users\Hex\.workbuddy\binaries\python\versions\3.13.12\python.exe`）。改成 3.15 之后，M0 的产物在这台机器上会**拒绝启动**，需要先装 3.15（`winget install Python.Python.3.15` 或官网安装包），再 `py -3.15 app.py`。

- 后端只用标准库（`http.server`、`subprocess`、`json`、`sqlite3` 都不用）。
- 前端不使用 npm、不使用打包器、不引用 CDN；所有资源本地化，断网可用。
- 编辑器自研（textarea + 高亮 overlay，约 300 行）：语法着色、自动缩进、括号配对、Tab/Shift-Tab、`Ctrl+Enter` 运行。**不引入 CodeMirror**——教程不需要补全与多光标，省掉整个 Node 工具链。若后续确实需要补全，再以 vendored 方式引入（决策点，非当前范围）。

### 3.3 执行引擎规格

| 项 | 规格 |
|---|---|
| 进程模型 | `python -s -B -u main.py`，cwd 为一次性临时目录；用**相对文件名**启动，traceback 里就是 `File "main.py", line N` |
| 环境变量 | 白名单：`PATH`、`SYSTEMROOT`、`TEMP` 等，外加 `PYTHONIOENCODING=utf-8`、`PYTHONPATH=<shim>`、`PYTUT_ALLOW_NETWORK` |
| 流式输出 | `os.read` 按块读（不是按行），否则 `input("提示")` 的提示符会卡在缓冲区里；stdout 立即转发，stderr 按行聚合以便清洗路径 |
| 虚拟 stdin | `stdin=PIPE`；`POST /api/run/<id>/stdin` 写入一行；**每次输入都会重置超时计时器**，硬上限 60s —— 用户打字不该被当成死循环 |
| 超时 | 默认 5s；含 `input()` 的代码由前端申请 15s（`MAX_TIMEOUT`）；超时发 `timeout` 事件并杀进程树 |
| 输出上限 | stdout 256 KB / stderr 64 KB，超出截断并标记 |
| 内存限制 | **Windows：Job Object**（`PROCESS_MEMORY` + `KILL_ON_JOB_CLOSE`，顺带清理 multiprocessing 子进程）；POSIX：`RLIMIT_AS` |
| 进程树清理 | POSIX `start_new_session` + `killpg`；Windows `CREATE_NEW_PROCESS_GROUP` + `taskkill /T` |
| 网络 | `sitecustomize` 在解释器启动时挂载 connect 钩子：默认只放行回环地址，外部主机抛 `PermissionError` 并说明如何用 `allow_network` 放行 |
| 错误映射 | traceback 过滤工作目录前缀 → `File "main.py", line N`；前端解析最后一个行号，给出「错误在第 N 行」并一键选中 |
| 并发 | 单用户，最多 3 个并行 run；超出排队 |

**关于 `launcher.py`**：计划里原本要多一层引导进程做限额与 shim，实现时放弃了——多一层会让 `multiprocessing` 的 spawn 子进程重新执行用户代码，还让进程树清理更复杂。改成两处更薄的实现：父进程侧设内存上限（`tutorial/limits.py`），子解释器启动时由 `PYTHONPATH` 自动导入 `sitecustomize` 挂网络钩子（`tutorial/sandbox/sitecustomize.py`）。代价是网络拦截只覆盖 `connect`，不覆盖 DNS 查询。

### 3.4 追踪引擎规格

- 在子进程内用 `sys.settrace`，只跟踪用户代码文件帧，`depth ≤ 40`、`steps ≤ 3000`。
- 事件：`call / line / return / exception`；每步记录 `{i, line, func, depth, frame_id, locals, heap_refs}`。
- 对象图：以 `id()` 为键建堆表 `heap[id] = {type, repr, items[], attrs{}}`；只展开容器与用户自定义实例，标量内联。循环引用靠"是否已存在"去重。
- 不追踪 asyncio / 线程（说明见 2.4），这两类课用时间线图示替代。
- 输出：单个 JSON（压缩后目标 < 1.5 MB），前端一次性加载后本地回放，拖动时间轴不请求服务端。

### 3.5 内容管线（编译期 vs 运行期）

**作者写 Markdown，编译器产出 AST JSON，前端只做渲染。**

```
content/beginner/03-numbers.md
   ──build.py──► web/data/lessons/b-03-numbers.json   （块数组 AST）
                 web/data/index.json                  （标题/概念/标题树/搜索索引）
```

- Markdown 支持子集：标题、段落、列表、引用、表格、行内代码/粗体/链接、代码围栏。
- 自定义围栏映射为互动块：` ```py run ` / ` ```py expect ` / ` ```exercise ` / ` ```quiz ` / ` ```step ` / ` ```callout `。
- **编译期强校验**（这是 103 课能维护住的关键）：
  1. front matter 必填字段齐全、`id` 唯一、`prereq` 无环；
  2. 所有 `run` 块真实执行且退出码为 0（超时 5s）；
  3. 所有 `expect` 块的输出与 `expect` 完全一致；
  4. 所有 `exercise` 的 `solution` 能通过自身全部测试（防"题目无解"）；
  5. `doc_refs` URL 格式合法；`concepts` 必须在受控词表内。
- 校验失败 → 构建失败并打印文件名 + 行号，不允许"带病发布"。

### 3.6 目录结构

```
tech-python/
├── app.py                    # 入口：python app.py
├── build.py                  # 内容编译 + 校验
├── tutorial/
│   ├── server.py             # 路由、静态服务、SSE
│   ├── runner.py             # RunManager：子进程、流式输出、超时、进程树清理
│   ├── limits.py             # Windows Job Object 内存上限、POSIX rlimit
│   ├── sandbox/
│   │   └── sitecustomize.py  # 启动期护栏：默认禁网（放行回环）
│   ├── tracer.py             # 追踪与堆快照（M4 待建）
│   ├── progress.py           # 进度读写（M3 待建）
│   ├── markdown.py           # MD 子集 → AST
│   └── schema.py             # 课程元数据与难度曲线校验
├── content/
│   ├── s0/*.md    (1–14)
│   ├── s1/*.md    (15–31)
│   ├── s2/*.md    (32–53)
│   ├── s3/*.md    (54–73)
│   ├── s4/*.md    (74–96)
│   └── s5/*.md    (97–103)
├── web/
│   ├── index.html
│   ├── css/  app.css  theme.css
│   ├── js/   app.js router.js renderer.js store.js search.js
│   │         widgets/{editor,terminal,quiz,exercise,stepper,mindmap}.js
│   └── data/  index.json  lessons/*.json   (build 产物，入库)
├── tests/
│   ├── test_runner.py  test_tracer.py  test_markdown.py  test_progress.py
│   └── test_content.py       # 全量内容校验
├── docs/  development-plan.md  COVERAGE.md  AUTHORING.md
├── .data/                    # 运行时进度（git 忽略）
└── README.md
```

### 3.7 API 契约

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | `index.html` |
| GET | `/api/health` | `{python, version_ok, capabilities:{threads,processes,network,fs_write}}` |
| GET | `/api/lessons` | 课程索引（含 stage、official_group、标题、concepts、前置） |
| GET | `/api/lessons/<id>` | 单课 AST |
| POST | `/api/run` | `{code, lesson_id, timeout, allow_network}` → `{run_id}` |
| GET | `/api/stream/<run_id>` | SSE：`start` / `stdout` / `stderr` / `exit` / `timeout` / `error` / `done` |
| POST | `/api/run/<id>/stdin` | `{data}` 写入标准输入 |
| POST | `/api/run/<id>/stop` | 终止进程树 |
| POST | `/api/trace` | `{code, lesson_id}` → 追踪 JSON（M4 待建） |
| GET/PUT | `/api/progress` | 全量读写进度；PUT 走校验 + 原子替换 + 备份 |
| POST | `/api/check` | `{lesson_id, exercise_id, code}` → 逐条测试结果；测试由服务端从课程 JSON 读取，客户端不能自带 |

### 3.8 数据模型

**lesson front matter**

```yaml
id: b-03-numbers
order: 4
stage: s0                # s0 | s1 | s2 | s3 | s4 | s5
official_group: beginner # beginner | moderate | advanced | general | resources
title: 数字与精度
concepts: [int, float, division, rounding]
doc_refs:
  - {title: "Tutorial 3.1.1", url: "https://docs.python.org/3/tutorial/introduction.html#numbers"}
requires_python: "3.15"   # 默认省略；仅当课程用到 3.16+ 语法时才写
allow_network: false
prereq: [3]
interactivity: [run, quiz, exercise, step]
xp: 20
```

**进度文件**

```json
{
  "schema": 1,
  "updated_at": "2026-10-29T10:00:00+08:00",
  "user": {"xp": 0, "streak": {"current": 0, "best": 0, "last_day": null}},
  "lessons": {"b-03-numbers": {"status": "done", "done_blocks": ["q1", "ex1"]}},
  "exercises": {"b-03-ex1": {"passed": true, "attempts": 2, "last_code": "..."}},
  "quizzes": {"b-03-q1": {"correct": true, "attempts": 1}},
  "weak_concepts": {"rounding": 2}
}
```

### 3.9 前端渲染约定

- 路由：`#/`、`#/lesson/<id>`、`#/lesson/<id>/<anchor>`；锚点缺失时回顶部，锚点存在时定位到小节。浏览器滚动位置恢复关掉（`history.scrollRestoration = "manual"`），否则刷新后会被拉回顶部。
- 渲染器按 AST 块类型分派；`h2`/`h3` 自动编 `sec-N`，`build.py` 生成索引时用同一规则，两边靠单测锁住（`tests/test_build.py`）。
- **编辑器**：`textarea` 文字透明 + 下方同字体的高亮层，靠 `caret-color` 显示光标。两侧必须完全同源（字体、行高、padding、`tab-size`、`white-space: pre`），否则会出现"文字重影"。输入时同步重算高亮与行号，滚动时同步 `scrollLeft`。
- **搜索**：`Ctrl/Cmd+K` 打开命令面板，检索范围是课程标题 + 概念 + 小节标题；结果可直接跳到 `sec-N`。索引在 `build.py` 里预生成，运行时不扫描正文。
- 快捷键：`Ctrl+Enter` 运行、`Ctrl+K` 搜索、`Alt+←/→` 上/下一课、`?` 快捷键表、`Esc` 关弹层。
- 主题：默认深色，可切浅色；两套 token 配色（关键字/字符串/数字/注释/内置名）都在 CSS 变量里。
- 性能目标：首屏 < 300 ms（本地），单课 JSON < 120 KB，切换课程无整页刷新。

### 3.10 安全与合规

- **明确声明**：本项目的执行隔离用于"防止教程代码把机器搞坏"，**不是安全沙箱**。用户代码以当前用户身份运行，README 与界面首次运行提示中都要写清楚。
- 默认禁网、禁写工程目录外路径、限时限内存；危险示例（`eval`、`pickle.loads`、`shell=True`）只在"安全检查"课里以只读方式讲解并标注风险。
- **版权**：官方文档为 PSF License。本项目正文为原创中文讲解，只做概念引用与链接跳转，不大段翻译/摘录；`docs/NOTICE.md` 注明来源与许可。
- **隐私**：不采集任何遥测；进度只存本地。

---

## 4. 课程大纲（103 课 · 按难度递进重排）

编号 1–103 全局唯一，直接用作 `front matter.order`。互动列：R=运行代码，E=判题，Q=测验，S=单步可视化。

**分组原则**：按"学习者此刻需要什么"排序，不按官方条目归堆。同一阶段内前置课编号必须小于本课，跨阶段依赖只能指向更早阶段——这条由 `build.py` 强制校验（见 4.8），所以难度曲线不是写给人看的，是机器守着的。

**语法基线**：最低版本 3.15，正文默认用现代写法——PEP 695 的 `def f[T](x: T) -> T`、`except*`、`match`、t-string，不再为老版本留兼容写法。对应的旧写法只在各课的"你会遇到的遗产代码"小节里出现，且标注"不要在新代码里这么写"。

### 4.1 S0 起步 · 14 课

先能跑、能查、能算、能存。这一阶段不出现"抽象"，只建立手感。

| # | 课程 | 关键特性 | 互动 |
|---|---|---|---|
| 1 | 安装、解释器与运行方式 | 安装校验、REPL、脚本、`-m`、`-i`、`PYTHONPATH` | R Q |
| 2 | 文档地图与检索 | Tutorial/Library/Reference 分工、站内搜索技巧、怎么查一个函数 | Q |
| 3 | 名字与对象：变量到底是什么 | 动态类型、名字绑定、`id()`、引用语义 | R S Q |
| 4 | 数字与精度 | int/float/complex、`/` vs `//`、`round`、`decimal`/`fractions`/`math` | R E S |
| 5 | 浮点数专题 | IEEE 754、`0.1+0.2`、容差比较、格式化陷阱 | R E S |
| 6 | 字符串：不可变序列 | 索引切片、方法、f-string、转义 | R E |
| 7 | 编码与字节 | `str` vs `bytes`、UTF-8、encode/decode 陷阱 | R Q |
| 8 | 列表与元组 | 可变/不可变、增删改查、嵌套、解包 | R E S |
| 9 | 字典与集合 | 哈希、键约束、`get`/`setdefault`、集合运算 | R E S |
| 10 | 比较、真值与身份 | `==` vs `is`、链式比较、真值表、小整数缓存 | R Q |
| 11 | 条件与 match | if/elif、`match` 模式匹配入门、海象运算符 | R E |
| 12 | 循环与循环控制 | while/for/range、break/continue/**else 子句** | R E S |
| 13 | 推导式与生成器表达式 | list/dict/set 推导、惰性求值、嵌套 | R E |
| 14 | 内置函数工具箱 | len/sum/zip/enumerate/map/filter/sorted(key=)/any/all | R E |

### 4.2 S1 组织 · 17 课

把代码切成函数、模块、文件；学会在出错时自救。**测试放在这一阶段末尾**，而不是等到讲完抽象。

| # | 课程 | 关键特性 | 互动 |
|---|---|---|---|
| 15 | 函数与参数 | 默认值陷阱、`*args`/`**kwargs`、keyword-only、`/` | R E |
| 16 | 作用域 LEGB | global/nonlocal、闭包初识、名字查找链 | R Q S |
| 17 | 闭包与晚绑定 | cell 变量、循环里创建函数、默认参数固化 | R Q S |
| 18 | 模块与 `__main__` | import 机制、`sys.path`、`if __name__ == "__main__"` | R Q |
| 19 | 包与项目结构 | `__init__.py`、相对导入、命名空间包 | R Q |
| 20 | 输入输出与格式化 | `print` 参数、`input`、f-string 格式规范 | R E |
| 21 | 文件读写 | `open`/`with`、编码、文本 vs 二进制 | R E |
| 22 | 标准库速览 | `os`/`sys`/`pathlib`/`datetime` 各 10 分钟 | R |
| 23 | 路径与文件系统 | `pathlib` 全家桶、`glob`、`shutil`、`tempfile` | R E |
| 24 | 结构化数据 | `json`、`csv`、`tomllib`、`configparser` | R E |
| 25 | 异常处理 | try/except/else/finally、raise、自定义异常、异常链 | R E S |
| 26 | 调试 | `breakpoint()`、pdb 常用命令、读 traceback、`warnings` | R Q |
| 27 | 迭代协议 | `iter`/`next`、for 的真相、StopIteration | R S |
| 28 | 生成器 | `yield`、`send`、`yield from`、惰性流水线 | R E S |
| 29 | 小项目：命令行待办 | 文件、JSON、argparse、异常、函数拆分 | R E |
| 30 | 虚拟环境与依赖 | `venv`、`pip`、`requirements.txt`、`uv` 对照 | R Q |
| 31 | 测试入门 | `unittest` 与 `pytest` 对照、断言、测试命名 | R E |

### 4.3 S2 抽象 · 22 课

会定义自己的类型、协议和工具。这一阶段结束应当能读懂一个中小型库的源码。

| # | 课程 | 关键特性 | 互动 |
|---|---|---|---|
| 32 | 类与实例 | class、`self`、`__init__`、实例属性 vs 类属性 | R E S |
| 33 | 继承与组合 | `super()`、MRO 预告、组合优于继承 | R E S |
| 34 | 数据模型入门 | `__repr__`/`__str__`/`__eq__`/`__hash__` 一致性 | R E S |
| 35 | dataclasses | `@dataclass`、frozen、`field`、`__post_init__` | R E |
| 36 | property 与 `__slots__` | 受控属性、只读、内存开销 | R S |
| 37 | 运算符重载与容器协议 | `__add__`/`__len__`/`__getitem__`/`__contains__` | R E |
| 38 | 枚举与常量组织 | `Enum`/`IntEnum`/`Flag`、`auto()` | R E |
| 39 | 上下文管理器 | `with` 协议、`contextlib.contextmanager`、异常抑制 | R E S |
| 40 | 装饰器基础 | 高阶函数、`functools.wraps`、计时/重试装饰器 | R E S |
| 41 | 装饰器进阶 | 带参装饰器、类装饰器、装饰器顺序 | R E |
| 42 | itertools | `chain/islice/groupby/product/combinations` | R E |
| 43 | functools | `lru_cache`、`partial`、`singledispatch`、`cmp_to_key` | R E |
| 44 | collections | `Counter/defaultdict/deque/namedtuple/OrderedDict` | R E |
| 45 | operator 与排序 | `key` 函数、多级排序、稳定性、`attrgetter`/`total_ordering` | R E |
| 46 | 类型注解入门 | 注解语法、`Optional`、运行时不检查、渐进式标注 | R Q |
| 47 | typing 进阶 | `Generic`/`TypeVar`/`Protocol`/`Literal`/`TypedDict` | R Q |
| 48 | 抽象基类与协议 | `ABC`、`register`、`runtime_checkable`、结构化子类型 | R E |
| 49 | 正则表达式 | 元字符、分组、贪婪/非贪婪、`findall` vs `finditer` | R E |
| 50 | 文本与 Unicode | `textwrap`/`string`/`difflib`、规范化、宽度与排序 | R E |
| 51 | 日期与时间 | `datetime`/`zoneinfo`、naive vs aware、时间戳陷阱 | R E |
| 52 | 随机、哈希与密钥 | `random` 的坑、`secrets`、`hashlib`/`hmac`、`uuid` | R E |
| 53 | 十大陷阱合集 | 可变默认参数、闭包晚绑定、深浅拷贝、`is` vs `==`、类属性共享 | R E S |

### 4.4 S3 工程 · 20 课

把代码变成别人能装、能测、能并行跑的东西。并发放在这里而不放进"深入"，因为它是日常技能，不是猎奇知识。

| # | 课程 | 关键特性 | 互动 |
|---|---|---|---|
| 54 | 日志 | `logging` 层级、handler/formatter、库内最佳实践 | R E |
| 55 | 命令行接口 | `argparse` 子命令、退出码、`--help` 设计 | R E |
| 56 | 子进程与外部命令 | `subprocess.run`、超时、编码、`shell=True` 风险 | R E |
| 57 | 测试进阶 | fixture、参数化、`mock`/`monkeypatch`、覆盖率 | R E |
| 58 | 类型检查实战 | mypy/pyright、stub 文件、`cast`、严格模式迁移 | Q |
| 59 | 安全编程 | `eval`/`exec`、`pickle`、路径穿越、`shell=True` | R Q |
| 60 | Pythonic 设计模式 | 单例/工厂/策略/观察者的 Python 写法 | R E |
| 61 | 打包基础：pyproject 与项目布局 | `pyproject.toml`、src 布局、依赖声明、可选依赖 | R Q |
| 62 | 构建、wheel 与入口点 | `build`、wheel/sdist、`console_scripts`、版本号策略 | R Q |
| 63 | 发布到 PyPI | 测试索引、trusted publishing、撤回与 yank | Q |
| 64 | 性能直觉与 timeit | 复杂度、`timeit`、`in list` vs `in set`、不可假设的常数 | R E |
| 65 | 性能剖析 | `cProfile`/`pstats`、`tracemalloc`、读火焰图、优化顺序 | R Q |
| 66 | 优化实战：从算法到 C 加速 | 先测量、数据结构替换、`array`/`memoryview`、边界 | R Q |
| 67 | 线程与 GIL | 竞态复现、`Lock`、`queue.Queue`、GIL 的真实影响 | R Q |
| 68 | 多进程与线程池 | `multiprocessing`、`concurrent.futures`、序列化开销 | R |
| 69 | 并发模型选型 | IO-bound vs CPU-bound、何时用哪种、常见误用 | Q |
| 70 | asyncio 基础 | 事件循环、`create_task`、`gather`、`await` 语义 | R |
| 71 | asyncio 进阶 | 超时、取消、`TaskGroup`、`Queue`/`Lock`、`to_thread` | R E |
| 72 | contextvars 与异步上下文 | `ContextVar`、任务间隔离、与 `threading.local` 的区别 | R E |
| 73 | 综合项目：可测试的 CLI 工具 | 分层、测试、日志、打包、发布一条龙 | R E |

### 4.5 S4 深入 · 23 课

打开 CPython 的盖子：属性查找、描述符、元类、内存、字节码。到这一阶段，前面所有"约定俗成"都会变成可解释的机制。

| # | 课程 | 关键特性 | 互动 |
|---|---|---|---|
| 74 | 对象模型 | `type`/`object`、实例字典、属性查找链、`__dict__` | R S |
| 75 | 描述符协议 | `__get__`/`__set__`/`__set_name__`、方法为何能绑定 | R S |
| 76 | 属性拦截 | `__getattr__` vs `__getattribute__`、代理与懒加载 | R E |
| 77 | 元类 | 类也是对象、`__init_subclass__`、`__prepare__` | R E |
| 78 | MRO 与多继承 | C3 线性化、协作式 `super()`、菱形继承 | R Q S |
| 79 | 泛型与型变 | `TypeVar` 约束、协变/逆变、`Self`、PEP 695 语法 | R Q |
| 80 | 生成器进阶 | 协程演进史、`throw`/`close`、状态机、`yield from` 委托 | R S |
| 81 | 内存与垃圾回收 | 引用计数、循环引用、`gc`、`__del__` 陷阱 | R S |
| 82 | 弱引用与缓存设计 | `weakref`、`WeakValueDictionary`、缓存失效 | R E |
| 83 | 字节码与执行模型 | `dis`、编译流程、常量折叠、`LOAD_FAST` | R S |
| 84 | 导入系统深入 | finder/loader、`importlib`、循环导入、`__all__` | R Q |
| 85 | 异常进阶 | `ExceptionGroup`/`except*`、异常链、`__notes__` | R E |
| 86 | contextlib 全家桶 | `ExitStack`、`suppress`、可重入、异步上下文 | R E |
| 87 | 迭代器进阶 | 单次迭代陷阱、`reversed`/切片协议、`__length_hint__` | R S |
| 88 | 序列化与拷贝 | `pickle` 风险、深浅拷贝、`__reduce__`、`copyreg` | R E |
| 89 | 元编程实战 | 动态建类、注册表、插件系统、`__init_subclass__` 组合 | R E |
| 90 | 注解的运行时 | `__annotations__`、`get_type_hints`、PEP 649 延迟求值 | R E |
| 91 | 函数签名与 inspect | `inspect.signature`、`bind`/`bind_partial`、参数校验装饰器 | R E |
| 92 | 模块级 `__getattr__` 与懒加载 | 惰性导入、弃用警告、`__dir__` | R E |
| 93 | 数值与运算符协议 | `__radd__`/`__iadd__`、`NotImplemented`、`__index__` | R E |
| 94 | C 扩展入门 | `ctypes` 调 C、手写扩展的编译流程、性能边界 | R Q |
| 95 | 嵌入解释器 | 在 C/C++ 里跑 Python、初始化与终结、free-threading 展望 | Q |
| 96 | C API：对象协议与引用计数 | `PyObject`、引用计数规则、`PyArg_ParseTuple`、错误处理 | Q |

> 94–96 是**只读延伸**：不判题；95、96 在沙箱内无法真实编译，标注为"不可运行，附可复制的真实命令"。

### 4.6 S5 参考 · 7 课

不按难度排序，按"要用时查得到"组织。

| # | 课程 | 内容 | 互动 |
|---|---|---|---|
| 97 | 交互式术语表 | 60+ 术语，搜索 + 关联课程跳转 | Q |
| 98 | PEP 导读与索引 | PEP 8/20/484/695 精读、如何读一篇 PEP | Q |
| 99 | FAQ 与报错对照 | 官方 FAQ 精编、异常 → 原因 → 修法速查表 | Q |
| 100 | 读 Guido 的设计文章 | 可读性优先、显式优于隐式、为什么没有花括号 | Q |
| 101 | The Zen of Python 与 Pythonic 思维 | 20 条箴言逐条解读与反例 | Q |
| 102 | 新版本特性 3.10–3.15 | `match`、PEP 695 泛型语法、`except*`、性能改进 | R Q |
| 103 | 学习路线图 | 下一步：Web/数据/自动化/CPython 源码，附资源清单 | — |

**合计：14 + 17 + 22 + 20 + 23 + 7 = 103 课。**

### 4.7 阶段与官方五组的关系

官方五组不删，降级为**标签**（`official_group` 字段），首页可切换"按阶段 / 按官方分组"两种视图。

| 阶段 | 对应官方分组 | 说明 |
|---|---|---|
| S0 起步 | Beginner | 纯入门 |
| S1 组织 | Beginner → Moderate | 从"能写脚本"过渡到"能组织代码" |
| S2 抽象 | Moderate | OOP 与协议，官方 Tutorial 后半 + Reference 数据模型入门 |
| S3 工程 | Advanced | 打包指南、HOWTOs、并发 |
| S4 深入 | Advanced → Python 3.x Resources | Language Reference 主体 + C 扩展/C API |
| S5 参考 | General → Python 3.x Resources | FAQ、PEP、Glossary、文档导航 |

### 4.8 难度曲线的机器校验

`build.py --check` 除了内容校验，还断言前置依赖满足**单调性**：

1. 每课 `prereq` 里的编号必须小于本课（同阶段内严格递增）；
2. 跨阶段依赖只能指向更早阶段（`stage` 字段比较）；
3. 依赖图无环；
4. 不允许"孤岛课"：除第 1 课外，每课至少有一个前置，或有显式 `standalone: true` 标记（S5 参考课允许）。

违反任一条即构建失败。这样以后加课改课，不会把难度顺序悄悄搞乱。

---

## 5. 覆盖矩阵（审计用）

`docs/COVERAGE.md` 由 `build.py` 从课程 front matter **自动生成**，不手工维护。手工维护的只有本章的口径说明。

### 5.1 已选 17 个官方条目的落点

| 官方条目 | 落地形态 | 覆盖课程 |
|---|---|---|
| Beginner's Guide | 起步与组织两阶段 | 1,3–25（23 课；第 2 课来自 Browse/Search） |
| Using Python | 环境课 | 1 |
| Tutorial | 主干 | 1–53（S0–S2 全部） |
| Library Reference | 模块精讲 + 索引 | 21–24,42–45,51,52,54,56,64–72,79,81,87,88,90；其余进索引页 |
| Language Reference | 拆两轮：入门 + 深入 | 入门 34,37,39,48；深入 74–93 |
| Python HOWTOs | 专题课 | 30,45,49,50,54,55,75,90 |
| Python Packaging User Guide | 工程三课 | 61–63 |
| Extending and Embedding | 只读延伸 | 94,95 |
| Python/C API | 只读延伸 | 96 |
| What's New in 3.15 | 版本课 | 102 |
| PEP Index | 课 + 索引页 | 98 |
| Glossary | 交互术语表 | 97 |
| Python FAQs | 参考课 | 99 |
| Guido's Essays | 参考课 | 100 |
| Browse Python 3.15.2 Docs | 并入文档地图 | 2 |
| Search the online docs | 并入文档地图 | 2 |
| Module Index | 独立索引页 | 不占课时（`/modules` 路由） |

> Language Reference 从"一段 30 课"改成两轮，是这次重排的核心收益：数据模型入门（34/37/39/48）在 S2 就要讲，否则 dataclass、with、装饰器全是黑箱；而描述符/元类留在 S4 才讲得透。

### 5.2 未纳入的 8 项（缺口声明）

| 条目 | 后果 | 如后续要补 |
|---|---|---|
| Developer's Guide | 不讲"如何参与 CPython / 读 CPython 源码"，2 只提一句 | +2 课：源码结构、编译与提 PR |
| Porting 2→3 | 不讲旧代码识别（`print` 语句、`str`/`bytes` 混用） | +1 课：读 2.x 代码 |
| In-development Docs | 不覆盖未发布版本，最新只到 3.15 | +1 课：版本前瞻 |
| Periodicals / Books / Videos | 不建资源页，首页无外链区 | 纯外链，不占课时 |
| Download Current Docs | 不提供"离线文档包"指引 | 资源页一句话 |
| Documentation Releases | 无版本归档入口 | 资源页一句话 |

### 5.3 Language Reference 章节覆盖

| Reference 章节 | 入门轮（S2） | 深入轮（S4） |
|---|---|---|
| §2 词法分析 | 3,4,6,7 | — |
| §3 数据模型 | 34,37 | 74,75,76,81,93 |
| §4 执行模型 | 16 | 83,84 |
| §5 导入系统 | 18,19 | 84 |
| §6 表达式 | 10,13 | 80 |
| §7 简单语句 | 12,16,18 | 28,85 |
| §8 复合语句 | 11,25,32,33,39 | 77,78 |
| §9 顶层组件 | 18,29 | — |
| §10 完整语法 | 附录速查页（不单独成课） | — |

### 5.4 标准库 50 模块覆盖

| 域 | 模块 | 课程 |
|---|---|---|
| 语言设施 | `sys` `builtins` `types` `inspect` | 1,14,22,91 |
| 文本与数据 | `re` `json` `csv` `tomllib` `configparser` `textwrap` `string` `difflib` `unicodedata` | 24,49,50 |
| 文件与路径 | `os` `os.path` `pathlib` `shutil` `glob` `tempfile` | 21,22,23 |
| 时间与数值 | `datetime` `zoneinfo` `time` `math` `statistics` `decimal` `fractions` | 4,5,51 |
| 容器与函数式 | `collections` `itertools` `functools` `operator` | 42,43,44,45 |
| 类型与抽象 | `typing` `dataclasses` `enum` `abc` `contextlib` | 35,38,39,46,47,48,86 |
| 错误与调试 | `traceback` `warnings` `pdb` `logging` | 26,54,85,99 |
| 进程与并发 | `subprocess` `threading` `multiprocessing` `concurrent.futures` `asyncio` `queue` | 56,67,68,70,71 |
| 序列化与安全 | `pickle` `copy` `weakref` `hashlib` `secrets` | 52,82,88 |

### 5.5 自检规则

1. 1–103 编号连续无空洞，且每课 `doc_refs` 至少一条指向已选条目；
2. 5.1 表里 17 个条目全部被至少一门课引用（`source_item` 字段反查）；
3. 5.4 表里 50 个模块每个都至少出现在一门课的 `modules` 字段；
4. 任一课程不得引用 5.2 中未纳入的条目——防止范围蔓延；
5. 4.8 的前置依赖单调性四条。

---

## 6. 里程碑与验收

按依赖顺序推进，每个里程碑都有"过了才能进下一个"的门槛。不给天数估计，以交付物和验收条件为准。

### M0 · 契约与骨架
交付：目录结构、`schema.py`、`build.py`、`COVERAGE.md` 骨架、3 门样板课（S0/S2/S4 各一门）、启动版本前置检查、`README`。
门槛：在 3.15 下 `python app.py` 能打开首页；在 3.13 下给出明确的版本拒绝信息（不是报错堆栈）；3 门课能读、能跑；`python build.py --check` 通过（含 4.8 的依赖单调性校验）。

### M1 · 执行内核
交付：`runner.py` + `launcher.py` + SSE + 虚拟 stdin + 超时/限额/进程树清理 + 错误行映射 + `/api/health` 能力探测。
门槛：`while True: pass` 5 秒被杀且 UI 可恢复；`input()` 可交互；`multiprocessing` 示例留下无孤儿进程；stdout 大量输出不卡 UI。

### M2 · 阅读与运行体验
交付：Markdown 渲染器（全块型）、自研编辑器、终端面板、主题切换、搜索、快捷键、路由。
门槛：103 课全部能渲染（此时内容可先占位）；编辑器输入无卡顿（1 万字符）；切换课程无内存泄漏。

### M3 · 判题与记忆
交付：exercise 判定协议、提示阶梯、XP/streak、进度落盘、薄弱点、导出/导入。
门槛：判题结果准确（含超时、异常、部分通过三种情形）；刷新/重启后进度不丢；连续天数边界正确（跨月、跨年、宽限）。

### M4 · 可视化
交付：`tracer.py`、单步 UI、对象内存图、递归/可变对象专项课。
门槛：`fib(5)` 递归栈与对象图正确；列表 append 动画不丢帧；3000 步上限下首帧 < 500 ms；不支持的场景（asyncio/线程）有明确降级提示。

### M5 · 内容冲刺（3 批）
批次 1：S0 1–14（14 课）→ 批次 2：S1 15–31（17 课）→ 批次 3：S2 32–53（22 课）→ 批次 4：S3 54–73（20 课）→ 批次 5：S4 74–96（23 课）→ 批次 6：S5 97–103（7 课）。
门槛（每批）：`build.py --check` 全绿（所有 run 块可执行、所有 exercise 的 solution 通过）、无占位文本、每课至少 1 个互动单元、人工抽检 3 课。

### M6 · 加固与交付
交付：跨平台验证（Windows / macOS / Linux）、无障碍（键盘全通路、ARIA、对比度）、性能优化、`AUTHORING.md`、`NOTICE.md`。
门槛：干净环境（仅 Python 3.15+）零依赖启动；断网全功能；`tests/` 全绿；首屏 < 300 ms。

### 总体验收（DoD）

1. `python app.py` 一条命令启动，无需 `pip install`，无需 Node。
2. 103 课全部可读、可运行、可判题；覆盖矩阵无"空缺"行。
3. 四类互动全部可用：运行、判题（含提示）、单步+对象图、测验。
4. 进度、XP、streak、薄弱点、知识地图均可用且持久化。
5. 断网可用；不发起任何外部请求。
6. 全部自动化测试通过；内容校验可复现。

---

## 7. 风险与对策

| 风险 | 概率 | 影响 | 对策 |
|---|---|---|---|
| **内容量是真正的工作量瓶颈**（103 课 × 讲解 + 3–5 题） | 高 | 高 | 课程模板化（固定 7 段结构）；`build.py` 强制校验；按 10 课一批推进，每批可交付；先写"特性清单"再写正文，避免返工 |
| 单步可视化复杂度失控 | 高 | 中 | 独立成层 + 特性开关；只支持教学必需子集；限额硬编码；若延期不阻塞其他里程碑 |
| Windows 进程树清理 / 内存限制差异 | 中 | 中 | M1 就把 `taskkill /T` 与 POSIX `killpg` 都写成测试用例；内存限制在 Windows 降级为"仅超时"，界面标注 |
| 用户误以为这是安全沙箱 | 中 | 高 | README、首次启动提示、界面页脚三处声明；默认禁网 + 限时限内存作为兜底 |
| Markdown 子集解析器出边界 bug | 中 | 中 | 严格子集 + 快照测试；编译期全量校验；渲染异常降级为 `<pre>` |
| "全覆盖"被质疑 | 中 | 中 | 用 COVERAGE.md 显式定义边界与延伸阅读；非目标写在 README 首屏 |
| 教程代码与解释器版本不一致 | 低 | 中 | 启动即校验 `≥ 3.15`，不提供降级；CI 固定 3.15 跑内容校验，保证"文档写的 = 实际跑的" |
| 版权争议 | 低 | 中 | 原创中文 + 引用链接；NOTICE.md 标注 PSF License 来源 |

---

## 8. 已设默认值（如不反对即按此执行）

这些是上一轮四个问题之外、仍需要拍板的小项。我按最合理的方式先定，评审时可直接推翻：

| 项 | 默认值 | 理由 |
|---|---|---|
| 最低 Python 版本 | **3.15** | 用户指定；启动即校验，低于 3.15 拒绝运行，不做降级 |
| 目标行为基准 | CPython 3.15.2 | 与官方稳定文档版本一致；本机现为 3.13.14，需先装 3.15 |
| UI 语言 | 中文（术语保留英文） | 与 D3 一致 |
| 主题 | 深色默认，可切浅色 | 当前 IDE 为深色 |
| 移动端 | 桌面优先，移动可读 | 编辑器+终端在窄屏体验有限 |
| 项目实战 | 2 个（CLI 待办、可测试 CLI 工具） | 覆盖"综合运用"，不额外增加课程数 |
| 代码编辑器 | 自研轻量版 | 保住"零构建、零依赖" |
| 版本控制 | `git init`，默认分支 `main`，`.data/` 与 `__pycache__` 忽略 | 工程惯例 |
| CI | 可选 GitHub Actions（仅跑 `tests/`） | 本地优先，不强制 |
| 进度存储 | `.data/progress.json`，原子写 + 上次备份 | 跨浏览器一致，比 localStorage 稳 |

---

## 9. 下一步

范围已定稿：17 项纳入、8 项排除，课程大纲重排为 **103 课**（第 4 章），覆盖矩阵按条目、Reference 章节、标准库模块三个维度重新对齐（第 5 章）。

你说"开始"，我就按 M0 → M1 → M2 → M3 → M4 → M5 → M6 顺序执行，每个里程碑结束给你一个可运行的中间产物，而不是等全部做完再交付。第一个交付物是 M0 的骨架 + 3 门样板课，用来先把"课程长什么样"钉死。

还有两处如果要改，现在成本最低：

- 第 8 节的 10 个默认值（最低 Python 3.15、深色默认、自研编辑器、`git init` 等）；
- 103 课里某几课的增删或调序，尤其 94–96 这组只读延伸课——它们不能跑代码，如果你觉得没必要，去掉后是 100 课。
