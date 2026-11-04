+++
id = "s5-97-glossary"
order = 97
stage = "s5"
official_group = "general"
title = "交互式术语表"
concepts = ["glossary", "terminology"]
prereq = []
standalone = true
requires_python = "3.15"
allow_network = false
xp = 10

[[doc_refs]]
title = "Python Glossary（官方术语表）"
url = "https://docs.python.org/3/glossary.html"
+++

# 全程术语速查

60 个术语按课程脉络排列。**输入即可筛选**，右侧「第 N 课」可跳回讲解处。背不下来的术语都该回到课程里重跑一遍代码——这才是术语表的正确用法。

```glossary
terms = [
  ["绑定 (binding)", "名字与对象的关联。赋值就是绑定，不是复制。", 3],
  ["不可变 (immutable)", "创建后不能原地修改：int / str / tuple。", 8],
  ["可变 (mutable)", "可以原地修改：list / dict / set，修改对所有引用可见。", 8],
  ["切片 (slice)", "seq[start:stop:step]，含头不含尾。", 6],
  ["f-string", "f\"...{表达式}...\" 格式化字符串字面量，格式说明在冒号后。", 6],
  ["真值 (truthiness)", "空容器、0、None、False 为假；\"0\"、[0] 为真。", 10],
  ["鸭子类型 (duck typing)", "只看行为（有没有这个方法），不看继承关系。", 60],
  ["海象运算符 (:=)", "在表达式内部赋值，常见于循环条件。", 11],
  ["match/case", "结构化模式匹配，匹配形状而非相等。", 11],
  ["EAFP", "Easier to Ask Forgiveness than Permission：先做，出异常再处理。", 29],
  ["生成器 (generator)", "带 yield 的函数，惰性产出、只能遍历一次。", 28],
  ["生成器表达式", "(x for x in seq)：推导式的惰性版本。", 13],
  ["惰性求值 (lazy)", "用到才计算，不预先建整块数据。", 13],
  ["闭包 (closure)", "函数 + 它捕获的外层变量；变量活在 cell 里。", 17],
  ["晚绑定 (late binding)", "闭包捕获的是变量而非值，调用时才读取。", 17],
  ["LEGB", "作用域查找顺序：Local → Enclosing → Global → Builtin。", 16],
  ["nonlocal", "声明“修改外层函数的变量”。", 16],
  ["UnboundLocalError", "在函数内读“已赋值”的局部名之前——通常是忘了 global。", 16],
  ["装饰器 (decorator)", "@deco ≡ func = deco(func)，在定义时包装函数。", 40],
  ["functools.wraps", "装饰器必备，保留被装饰函数的名字与文档。", 40],
  ["lru_cache", "按参数缓存函数结果；只适合纯函数。", 43],
  ["partial", "预填一部分参数，生成新函数。", 43],
  ["singledispatch", "按参数类型分发到不同实现。", 43],
  ["Counter", "计数容器，缺键返回 0，自带 most_common。", 44],
  ["defaultdict", "缺键时调用工厂函数补默认值。", 44],
  ["deque", "两端操作 O(1) 的队列，maxlen 可自动滑窗。", 44],
  ["dataclass", "按字段注解生成 __init__/__repr__/__eq__。", 35],
  ["frozen", "不可变 dataclass，实例可哈希。", 35],
  ["property", "把方法伪装成属性，读取即计算。", 36],
  ["__slots__", "固定属性槽位，省内存、禁动态属性。", 36],
  ["描述符 (descriptor)", "实现 __get__/__set__ 的协议，property 与方法绑定的基础。", 75],
  ["元类 (metaclass)", "创建类的类；99% 的需求用 __init_subclass__ 就够。", 77],
  ["__init_subclass__", "子类定义时自动触发的钩子，注册表首选。", 77],
  ["MRO", "方法解析顺序（C3 线性化），__mro__ 可查。", 78],
  ["Mixin", "小而正交、不独立实例化的能力类。", 78],
  ["泛型 (generic)", "class Stack[T]：类型参数随容器传递。", 79],
  ["协变/逆变", "只读容器协变（Sequence）、可写容器不变（list）。", 79],
  ["Protocol", "结构化子类型：长得像就算，不必显式继承。", 48],
  ["ABC", "抽象基类：名义契约，实例化时强制检查抽象方法。", 48],
  ["类型收窄 (narrowing)", "is None 判断后，分支内类型确定。", 58],
  ["ExceptionGroup", "一组异常，except* 按类型分支处理。", 85],
  ["GIL", "全局解释器锁：同一时刻一个线程执行字节码。", 67],
  ["事件循环 (event loop)", "asyncio 的调度器，在 await 处切换任务。", 70],
  ["协作式调度", "任务只在 await 处让出控制权。", 70],
  ["TaskGroup", "结构化并发：全部等完、一败俱败。", 71],
  ["Semaphore", "限制同时运行的并发数。", 71],
  ["ContextVar", "按任务隔离的“全局变量”，日志注入 request-id 的标准做法。", 72],
  ["字节码 (bytecode)", "源码编译后的虚拟机指令，dis 可查看。", 83],
  ["常量折叠 (folding)", "编译期算好常量表达式。", 83],
  ["循环导入 (circular import)", "互相 import 读到半成品模块，报错点在半成品属性。", 84],
  ["__all__", "import * 的白名单声明。", 84],
  ["venv", "每个项目独立的 site-packages。", 30],
  ["wheel", "预构建的安装包，pip 优先安装。", 62],
  ["入口点 (entry point)", "安装后生成的命令，指向 模块:函数。", 62],
  ["竞态条件 (race condition)", "多线程时序导致的错误结果，用 Lock 消除。", 67],
  ["cProfile", "函数级热点分析，tottime 排序找瓶颈。", 65],
  ["timeit", "关 GC 的微基准，量级对比用。", 64],
  ["深拷贝 (deepcopy)", "递归复制整棵对象图，防止内层穿透。", 53],
  ["弃用 (deprecation)", "功能标记为将移除，用 warnings.warn 提醒。", 92]
]
```

> [!tip] 用法建议
> 筛选框支持拼音外的一切子串（术语、定义都搜）。碰到陌生术语，先筛选、跳课程、重跑代码——比背定义有效得多。
