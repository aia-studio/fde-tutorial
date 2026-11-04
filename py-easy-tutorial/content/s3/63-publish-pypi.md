+++
id = "s3-63-publish-pypi"
order = 63
stage = "s3"
official_group = "moderate"
title = "发布到 PyPI"
concepts = ["twine", "trusted publishing", "yank", "semver"]
prereq = [62]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Python Packaging User Guide：发布到 PyPI"
url = "https://packaging.python.org/en/latest/tutorials/packaging-projects/"

[[doc_refs]]
title = "PyPI：项目命名规则"
url = "https://pypi.org/help/#project-name"
+++

# 发布是流程，不是按钮

发布本身只有三条命令，难点全在流程纪律：**版本号怎么定、发之前测什么、发错了怎么办**。这一课把命令和纪律一起讲。

## 三条命令

```bash
python -m pip install --upgrade build twine
python -m build                      # 产出 dist/ 下的 sdist + wheel
python -m twine check dist/*         # 校验元数据
python -m twine upload dist/*        # 正式上传（先去测试索引练手）
```

> [!warn] 先发测试索引
> PyPI **不支持删除重传同名版本**——发错的版本只能被 yank（撤下推荐位）或发新版本覆盖。所以第一次永远用 [TestPyPI](https://test.pypi.org/) 演练：注册、上传、安装、验证，全流程走通再碰正式站。

## Trusted Publishing：不再用密码

老流程要在本地存 API token（泄漏即事故）。现在 PyPI 支持 **Trusted Publishing**：在 PyPI 上绑定 GitHub 仓库与 workflow，CI 发版时凭身份令牌直接上传，**本地不存任何密钥**。

```yaml
# .github/workflows/release.yml 的关键字段
permissions:
  id-token: write          # 生成 OIDC 令牌
# twine upload --skip-existing dist/* 由 action 完成
```

## 版本号：语义化，且只往前走

```text
1.2.3
│ │ └── 补丁：修 bug，不改接口
│ └── 次版本：新功能，向后兼容
└── 主版本：破坏性变更
```

配套两条纪律：

- **发布前**：把版本写在 `pyproject.toml`（单一来源），CI 校验 tag 与版本一致。
- **发布后**：发现严重 bug 时 `yank`（从推荐位撤下）+ 发补丁版本。已发布版本**永不修改**——别人可能锁了精确版本。

## 发布前检查单

- [ ] `python -m build` 无警告，`twine check` 通过
- [ ] 在干净虚拟环境里 `pip install dist/*.whl` 并跑一遍冒烟
- [ ] 版本号、changelog、README 里的安装示例三者一致
- [ ] 依赖上限检查：新依赖没有引入与既有用户的冲突

```quiz
question = "发布 0.2.0 后发现一个严重 bug，正确的处理是？"
options = [
  "删除 PyPI 上的 0.2.0，重新上传修复版",
  "yank 0.2.0 并发布 0.2.1",
  "直接上传同版本号的修复文件",
  "在 GitHub 上删除 tag 即可"
]
answer = 1
explain = "PyPI 禁止重传同名版本（缓存与安全考虑），删版本会让锁定该版本的用户失效。yank 让 pip 默认不再解析到它，已锁定的用户不受影响，再发布补丁版本。"
```

## 小结

- 流程：build → twine check → （TestPyPI 演练）→ 上传。
- Trusted Publishing 用 OIDC 令牌，本地不再存密钥。
- 版本号语义化、只增不减；发错版本 yank + 补丁。
- 发布前在干净环境里装 wheel 冒烟，是最容易省也最不该省的一步。
