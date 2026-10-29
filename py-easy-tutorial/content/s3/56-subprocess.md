+++
id = "s3-56-subprocess"
order = 56
stage = "s3"
official_group = "moderate"
title = "子进程与外部命令"
concepts = ["subprocess", "capture_output", "check", "timeout", "shell injection"]
prereq = [55]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：subprocess"
url = "https://docs.python.org/3/library/subprocess.html"

[[doc_refs]]
title = "Tutorial 11.1：subprocess"
url = "https://docs.python.org/3/tutorial/stdlib.html#process-parameters"
+++

# 调用外部程序的唯一正道

调用别的程序（git、ffmpeg、另一个 Python 脚本）只有一种正确姿势：`subprocess.run`。老教程里的 `os.system` 和 `os.popen` 已经没有存在理由——它们拿不到返回值，还默认经过 shell。

## 基本用法与返回值

```python
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-c", "print('来自子进程')"],
    capture_output=True,
    text=True,
)
print(result.returncode)
print(result.stdout.strip())
```

```expect
0
来自子进程
```

参数是**列表**（程序名 + 各参数），不走 shell，不用拼字符串。`capture_output=True` 抓下 stdout/stderr，`text=True` 让它们是 str 而不是 bytes。

## `check=True`：失败要响

```python
import subprocess
import sys

try:
    subprocess.run(
        [sys.executable, "-c", "raise ValueError('子进程失败')"],
        check=True,
        capture_output=True,
        text=True,
    )
except subprocess.CalledProcessError as exc:
    print(type(exc).__name__, exc.returncode)
```

```expect
CalledProcessError 1
```

默认 `check=False`，非零退出码静默通过——**这几乎总是错的**。失败要么抛异常（`check=True`），要么显式检查 `returncode`，二选一。

## `timeout`：别等一个卡死的进程

```python
import subprocess
import sys

try:
    subprocess.run(
        [sys.executable, "-c", "while True: pass"],
        timeout=1,
        capture_output=True,
    )
except subprocess.TimeoutExpired:
    print("超时终止")
```

```expect
超时终止
```

> [!danger] 永远不要用 `shell=True` 拼接用户输入
> `subprocess.run("git log " + filename, shell=True)` 里，文件名叫 `; rm -rf /` 就出事了。规则：**参数列表里出现用户输入是安全的，整条命令字符串里出现用户输入就是漏洞**。第 89 课的安全检查专门复盘这一点。

## 本教程自身的执行引擎也是这么写的

```python
import subprocess
import sys

code = 'print("你好")'
result = subprocess.run(
    [sys.executable, "-s", "-B", "-u", "-c", code],
    capture_output=True,
    text=True,
    timeout=5,
)
print(result.stdout.strip())
```

```expect
你好
```

你现在点「运行」看到的每一段输出，都是教程后端用 `subprocess.run` 起子进程抓回来的——同一个接口，同一套约束。

```quiz
question = "下面哪种写法有命令注入风险（filename 来自用户输入）？"
options = [
  "subprocess.run(['git', 'log', filename])",
  "subprocess.run(f'git log {filename}', shell=True)",
  "subprocess.run(['git', 'log', '--', filename])",
  "subprocess.run(args_list)"
]
answer = 1
explain = "shell=True 时整条字符串交给 shell 解释，分号、反引号都是攻击面。列表形式不经 shell，filename 永远只是第二个参数。"
```

## 小结

- `subprocess.run` + **列表参数**，不用 `os.system`，默认不开 shell。
- `capture_output=True` + `text=True` 拿字符串；`check=True` 让失败抛异常。
- 长任务必须带 `timeout`。
- `shell=True` + 用户输入 = 命令注入，没有例外。
