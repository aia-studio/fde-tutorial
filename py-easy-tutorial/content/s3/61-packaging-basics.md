+++
id = "s3-61-packaging-basics"
order = 61
stage = "s3"
official_group = "moderate"
title = "打包基础：pyproject 与项目布局"
concepts = ["pyproject", "src layout", "dependencies", "build-system"]
prereq = [60]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python Packaging User Guide：pyproject.toml"
url = "https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"

[[doc_refs]]
title = "Packaging：src 布局与扁平布局"
url = "https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/"
+++

# `pyproject.toml` 是项目的身份证

从 2021 年起，Python 打包的入口只有一个文件：`pyproject.toml`。它声明三件事——**怎么构建**（build-system）、**项目是什么**（project）、**工具怎么配置**（tool.*）。setup.py 时代可以翻篇了。

## 一个最小的 `pyproject.toml`

```python
import tomllib

pyproject = tomllib.loads("""
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "mytool"
version = "0.1.0"
requires-python = ">=3.15"
dependencies = ["rich>=13"]

[project.scripts]
mytool = "mytool.cli:main"
""")

print(pyproject["build-system"]["build-backend"])
print(pyproject["project"]["name"])
print(pyproject["project"]["scripts"])
```

```expect
setuptools.build_meta
mytool
{'mytool': 'mytool.cli:main'}
```

- `build-system`：用什么后端把项目变成可安装的包（还有 hatchling、flit 等）。
- `project`：名字、版本、Python 版本下限、依赖清单。
- `project.scripts`：装完后生成 `mytool` 命令，指向 `mytool/cli.py` 的 `main`。

## 两种布局，差别在"测试谁"

```text
扁平布局（flat）          src 布局（推荐发布用）
mytool/                   mytool/
├── pyproject.toml        ├── pyproject.toml
├── mytool/               ├── src/
│   ├── __init__.py       │   └── mytool/
│   └── cli.py            │       ├── __init__.py
└── tests/                │       └── cli.py
                          └── tests/
```

扁平布局里，在仓库根目录跑测试时 `import mytool` 拿到的是**源码目录**，而不是安装后的包——"本地能跑、装完就坏"的问题大多源于此。`src/` 布局强制先安装再测试，测的就是用户会拿到的东西。

## 依赖怎么写

| 写法 | 含义 | 例子 |
|---|---|---|
| `rich>=13` | 至少 13 | 库的最常见写法 |
| `rich>=13,<14` | 锁定大版本 | 应用锁定依赖 |
| `rich` | 任何版本 | 基本不用 |

> [!tip] 库与应用的策略相反
> **库**（给别人装的）依赖写得宽松（`>=13`），让使用者自己解冲突；**应用**（自己部署的）依赖锁死（精确版本或 lock 文件），保证部署可复现。把库的依赖写成 `==` 是发布时的常见事故。

```quiz
question = "为什么要用 `src/` 布局？"
options = [
  "import 更快",
  "强制测试运行「安装后的包」而不是仓库里的源码目录",
  "setuptools 只支持 src 布局",
  "避免 pyproject.toml 和代码混淆"
]
answer = 1
explain = "扁平布局下，仓库根目录在 sys.path 里，import mytool 拿到的是当前目录的源码。src/ 布局让根目录下没有 mytool，必须先安装（pip install -e .）才能导入，测试环境更接近用户。"
```

## 小结

- `pyproject.toml` 三段：build-system / project / tool 配置。
- `project.scripts` 生成命令行入口，指向 `模块:函数`。
- `src/` 布局强制"先安装再测试"，消灭本地假阳性。
- 库依赖宽松、应用依赖锁死，策略相反。
