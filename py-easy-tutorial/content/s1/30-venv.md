+++
id = "s1-30-venv"
order = 30
stage = "s1"
official_group = "moderate"
title = "虚拟环境与依赖"
concepts = ["venv", "pip", "requirements", "sys.prefix", "isolation"]
prereq = [29]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 12：虚拟环境与包"
url = "https://docs.python.org/3/tutorial/venv.html"

[[doc_refs]]
title = "Python Packaging User Guide：管理依赖"
url = "https://packaging.python.org/en/latest/tutorials/managing-dependencies/"
+++

# 每个项目一个干净的房间

A 项目要 `requests==2.28`，B 项目要 `requests==2.31`——装在同一套环境里必然打架。虚拟环境的作用就是给每个项目一套独立的 `site-packages`。

## 判断自己在不在隔离环境里

```python
import os
import sys

is_venv = sys.prefix != sys.base_prefix
is_conda = "CONDA_PREFIX" in os.environ

print("venv 环境：", is_venv)
print("conda 环境：", is_conda)
print("隔离环境：", is_venv or is_conda)
print("解释器：", sys.executable)
```

这块**故意不写预期输出**：结果取决于你在哪种环境里跑。要看的是最后一行——那段路径就是"当前到底用了哪个 Python"的答案。遇到 `ModuleNotFoundError`，第一件事是看这个路径。

`sys.prefix` 是当前环境的根目录，`sys.base_prefix` 是安装 Python 时的原始根目录。**用 `venv` 创建的环境**两者不同（因为存在 `pyvenv.cfg`）；而 **conda 环境没有 `pyvenv.cfg`**，两个值相同，所以要靠 `CONDA_PREFIX` 环境变量判断。这是个常见的误判点。

## 常用命令

```bash
python -m venv .venv              # 创建环境（在项目目录下）
.venv\Scripts\activate            # Windows 激活
source .venv/bin/activate         # macOS / Linux 激活

python -m pip install requests    # 装到当前环境的 site-packages
python -m pip freeze > requirements.txt
python -m pip install -r requirements.txt
```

几个习惯值得从一开始就养成：

- **用 `python -m pip` 而不是直接 `pip`**，避免"pip 指向了另一个解释器"的经典事故。
- 环境目录叫 `.venv`，并写进 `.gitignore`。
- `requirements.txt` 用 `pip freeze` 生成时带精确版本，保证别人装到一样的东西。

> [!warn] 别把虚拟环境提交进仓库
> `.venv` 里有几万个文件，而且和平台绑定。仓库里只放 `requirements.txt` 或 `pyproject.toml`，环境靠命令重建。

## 依赖声明的两种风格

| 文件 | 特点 | 适合 |
|---|---|---|
| `requirements.txt` | 精确版本列表，`pip freeze` 生成 | 应用部署、快速复现 |
| `pyproject.toml` | 声明直接依赖与版本范围 | 库、要发布的项目 |

前者的缺点是分不清"我直接用的"和"依赖的依赖"；后者能表达 `requests>=2.31,<3` 这种范围。

```quiz
question = "在项目里执行 `pip install requests` 后，代码里 `import requests` 仍然失败，最可能的原因是？"
options = [
  "requests 不支持当前 Python 版本",
  "pip 指向的是另一个解释器，装到了别处",
  "需要重启操作系统",
  "requests 只能通过 conda 安装"
]
answer = 1
explain = "机器上常有多个 Python，pip 和 python 可能不是一套。用 python -m pip install 能保证装进当前解释器；排查时看 sys.executable 确认在跑哪个 Python。"
```

## 小结

- 虚拟环境 = 独立的 `site-packages`，避免项目间版本冲突。
- `sys.prefix != sys.base_prefix` 可以判断当前是否在隔离环境。
- 始终用 `python -m pip` 安装，避免 pip 与解释器不匹配。
- 仓库只提交依赖声明，不提交环境目录。
