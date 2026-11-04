+++
id = "s3-54-logging"
order = 54
stage = "s3"
official_group = "moderate"
title = "日志"
concepts = ["logging", "level", "logger", "handler", "propagation"]
prereq = [53]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：logging"
url = "https://docs.python.org/3/library/logging.html"

[[doc_refs]]
title = "HOWTO：logging 教程"
url = "https://docs.python.org/3/howto/logging.html"
+++

# print 会在三个月后背叛你

`print` 的输出没有级别、没有来源、没有时间，也无法关闭。`logging` 解决的就是这三件事：**分级**（能不能关）、**命名**（谁说的）、**输出目标**（去控制台还是文件）。写库代码的第一天就该用 logging。

## 级别：从低到高，可过滤

```python
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("app")

log.info("启动")
log.warning("磁盘快满")
log.error("连不上")
```

```expect
INFO app: 启动
WARNING app: 磁盘快满
ERROR app: 连不上
```

级别依次是 DEBUG / INFO / WARNING / ERROR / CRITICAL。`basicConfig(level=...)` 设定**全局开关**，低于它的直接丢弃：

```python
import logging
import sys

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("app")

log.info("这条不会出现")
log.warning("这条会出现")
```

```expect
WARNING: 这条会出现
```

调试时把级别调到 DEBUG，生产环境保持 INFO——代码不用改。

> [!warn] logging 默认写到 stderr
> `basicConfig` 不指定 `stream` 时输出到 `sys.stderr`。stderr 和 stdout 是两条流，
> 重定向时（`app.py > log.txt`）日志不会进文件——这是新手最常见的困惑之一。
> 本课示例显式传 `stream=sys.stdout`，真实项目里通常会传一个日志文件。

## Logger 层级：按模块命名

```python
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s", stream=sys.stdout)
app_log = logging.getLogger("app")
db_log = logging.getLogger("app.db")

db_log.info("数据库就绪")
print(db_log.parent is app_log)
```

```expect
INFO app.db: 数据库就绪
True
```

用 `logging.getLogger(__name__)` 取 logger，名字自动按模块层级组织。子 logger 的记录会**向上传播**到根 logger 的 handler，所以配置一次、全程序生效。

> [!warn] 别在库里调 basicConfig
> 库代码只 `getLogger(__name__)` 并发记录；`basicConfig` 是**应用程序入口**的事。库里调它等于抢走了应用的配置权，这是 logging 的头号禁忌。

## 异常要带栈

```python
import logging
import sys

logging.basicConfig(format="%(levelname)s %(message)s", stream=sys.stdout)
log = logging.getLogger("app")

try:
    1 / 0
except ZeroDivisionError:
    log.error("计算失败", exc_info=True)
```

这块不设预期输出：`exc_info=True` 会把**完整 traceback**写进日志（默认到 stderr），包括出错的文件与行号。生产日志里每一条 ERROR 都应该带它——没有栈的报错等于没报。


`exc_info=True` 把完整 traceback 附进日志。没有它，你只知道"失败了"，不知道在哪一行——这正是第 26 课"看清再动手"的前置条件。

```quiz
question = "写一个第三方库，正确的日志用法是？"
options = [
  "在库的 __init__.py 里调 basicConfig(level=INFO)",
  "每个模块 getLogger(__name__)，只发记录不配置输出",
  "用 print 输出，避免配置冲突",
  "把所有日志都发到根 logger"
]
answer = 1
explain = "库只产生日志记录（ getLogger(__name__) ），格式、级别、输出目标全部由使用它的应用决定。库里调 basicConfig 会抢走应用的配置权。"
```

## 小结

- 五个级别从 DEBUG 到 CRITICAL，`level` 是全局开关。
- `getLogger(__name__)` 建立层级，记录向上传播。
- 异常日志带 `exc_info=True`，否则丢失定位线索。
- 库只发记录，应用才配置 basicConfig。
