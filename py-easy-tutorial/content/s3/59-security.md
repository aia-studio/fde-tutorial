+++
id = "s3-59-security"
order = 59
stage = "s3"
official_group = "moderate"
title = "安全编程"
concepts = ["eval", "pickle", "shell injection", "path traversal"]
prereq = [58]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：security considerations"
url = "https://docs.python.org/3/library/security.html"

[[doc_refs]]
title = "Tutorial：常见安全问题"
url = "https://docs.python.org/3/library/security.html"
+++

# 四种把服务器送走的写法

这一课没有新语法，只有四个"看起来无害的 API + 一点用户输入 = 事故"的组合。每个都在沙箱里复现给你看——看清楚危害长什么样，戒掉它们才不是口号。

## `eval`：等于把键盘交给用户

```python
expression = "__import__('os').getcwd()"

result = eval(expression)
print("eval 真的执行了：", isinstance(result, str) and "pytut-build" in result)
```

```expect
eval 真的执行了： True
```

`eval("2 + 3")` 用于计算器演示没问题；一旦表达式来自用户，`__import__` 就能执行任意代码。上面的输出在实际环境里就是**当前工作目录**——本教程的沙箱把它拦住了，真实服务器上没人拦。

需要计算表达式用 `ast.literal_eval`（只允许字面量）：

```python
import ast

print(ast.literal_eval("[1, 2, 3]"))

try:
    ast.literal_eval("__import__('os')")
except ValueError as exc:
    print("拒绝：", type(exc).__name__)
```

```expect
[1, 2, 3]
拒绝： ValueError
```

## `pickle`：反序列化即代码执行

```python
import pickle

data = {"user": "Ada"}
blob = pickle.dumps(data)
print(pickle.loads(blob))
```

```expect
{'user': 'Ada'}
```

自己 `dumps` 再 `loads` 没问题；**加载来路不明的 pickle 文件**等于执行任意构造的代码。pickle 的文档第一句就写着"从不信任来源"。跨进程传数据用 JSON，持久化自己的对象用 `dataclass` + JSON。

## 路径穿越：`../` 就是钥匙

```python
from pathlib import Path

BASE = Path("/tmp/pytut-demo") / "uploads"
filename = "../../etc/hostname"

target = (BASE / filename).resolve()
print(str(target).startswith(str(BASE)))
```

```expect
False
```

用户上传名叫 `../../etc/hostname` 的文件，`BASE / filename` 直接逃出上传目录。修复：resolve 之后**校验仍在 BASE 下**，不满足就拒绝——这个模式背下来。

## `shell=True`：第 56 课的坑，这里复盘

```python
import shlex

filename = "notes.txt; rm -rf ~"
print(shlex.split(f"git log {filename}"))
```

```expect
['git', 'log', 'notes.txt;', 'rm', '-rf', '~']
```

`shlex` 不会执行命令，但它展示了 shell 会怎么拆这条字符串：分号把"看日志"和"删库"接成两条命令。列表参数（不经 shell）从一开始就没有这个问题。

```quiz
question = "需要把用户上传的文件存到 `/srv/uploads` 下，正确的做法是？"
options = [
  "target = f'/srv/uploads/{filename}'",
  "target = Path('/srv/uploads') / filename，然后校验 resolve() 结果在 uploads 下",
  "把文件内容 base64 后当文件名",
  "用 os.system(f'mv {filename} /srv/uploads/')"
]
answer = 1
explain = "resolve() 展开所有 ../ 与符号链接，之后断言路径在白名单目录内，不满足即拒绝。字符串拼接和 shell 移动都把攻击面完全交给用户输入。"
```

## 小结

- 表达式来自用户 → `ast.literal_eval`，永远不用 `eval`。
- pickle 只加载自己写的文件；跨系统交换用 JSON。
- 外部路径先 `resolve()` 再校验前缀，拒绝越界。
- 子进程一律列表参数；`shell=True` 遇用户输入即注入。
