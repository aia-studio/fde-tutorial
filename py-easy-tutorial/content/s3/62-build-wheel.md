+++
id = "s3-62-build-wheel"
order = 62
stage = "s3"
official_group = "moderate"
title = "构建、wheel 与入口点"
concepts = ["sdist", "wheel", "entry points", "versioning"]
prereq = [61]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python Packaging User Guide：构建分发包"
url = "https://packaging.python.org/en/latest/tutorials/packaging-projects/"

[[doc_refs]]
title = "Library Reference：importlib.metadata"
url = "https://docs.python.org/3/library/importlib.metadata.html"
+++

# 两种产物：源码包和轮子

`python -m build` 会产出两样东西：`*.tar.gz`（**sdist**，源码包）和 `*.whl`（**wheel**，预构建包）。pip 优先装 wheel——不用在用户机器上跑构建，快且不易出错。

## wheel 里装的是什么

```text
mytool-0.1.0-py3-none-any.whl     ← zip 压缩包
├── mytool/
│   ├── __init__.py
│   └── cli.py
├── mytool-0.1.0.dist-info/
│   ├── METADATA                  ← 项目元信息
│   ├── entry_points.txt          ← 命令行入口
│   └── RECORD                    ← 文件清单与哈希
```

`py3-none-any` 的意思是：纯 Python（py3）、不挑平台（none-any）。含 C 扩展的包会是 `cp315-cp315-win_amd64`——按解释器版本和平台各出一个 wheel。

## 入口点：装完就能敲命令

```python
from importlib.metadata import entry_points

eps = list(entry_points(group="console_scripts"))
print(len(eps) > 0)

names = sorted(ep.name for ep in eps)
print("pip" in names)
```

```expect
True
True
```

本机已安装的包全都暴露在 `entry_points` 里——`pip`、`pytest` 这些命令就是这么来的。你自己在 `project.scripts` 里声明的入口，装完之后也会出现在这里，`importlib.metadata` 还能在运行时反查。

## 版本号：语义化 + 上限

```python
class V:
    def __init__(self, s):
        self.parts = tuple(int(x) for x in s.split("."))

    def __lt__(self, other):
        return self.parts < other.parts


print(V("0.10.0") > V("0.9.0"))
print("0.10.0" > "0.9.0")
```

```expect
True
False
```

版本号要**数字比较**而不是字符串比较——字符串比较里 `"0.10.0" < "0.9.0"`，这就是为什么不手写版本比较、也不把版本号当字符串排序。

> [!warn] 构建产物不进仓库
> `dist/`、`*.egg-info/`、`build/` 都写进 `.gitignore`。仓库里只有源码与 `pyproject.toml`，产物每次从源码重新构建——二进制与源码不同步是发布事故的经典来源。

```quiz
question = "pip 优先安装 wheel 而不是 sdist 的主要原因是？"
options = [
  "wheel 体积更小",
  "wheel 是预构建的，不需要在用户机器上执行构建过程",
  "sdist 不包含代码",
  "wheel 支持 Python 2"
]
answer = 1
explain = "装 sdist 要在用户环境执行构建（可能需要编译器、网络下载构建依赖），失败面大；wheel 解压即用。这也是「发布时 wheel 缺失，用户构建失败」问题的根源。"
```

## 小结

- `python -m build` 产出 sdist 与 wheel；pip 优先 wheel。
- wheel 内含 `dist-info`：元数据、入口点、文件清单。
- `importlib.metadata` 运行时可查已安装包与入口点。
- 版本号按数字比较；构建产物不进仓库。
