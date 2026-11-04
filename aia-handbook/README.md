# aia-handbook · 技术书生产流水线

一套把"写一本技术书"变成**可调度的构建任务**的 SKILL。

核心思路一句话：**章是节点，依赖是边，拓扑序给波次，同波并行，跨波只传合同。**

不靠"让 agent 一章章往下写"，靠三样东西兜住质量：

1. **冻结的宪法** —— 每本书现场生成，批量写作前锁死
2. **可执行的闸门** —— `scripts/check.py`，不靠 agent 自评
3. **账本** —— 术语 / 事实 / 承诺 / 能力阶梯，跨章一致性由数据保证，不靠记忆

---

## 📖 使用手册

**怎么用、怎么用好、不同场景怎么用 → [GUIDE.md](GUIDE.md)**

（适用判断、七阶段操作、命令参考、场景手册、报错速查、最佳实践全部在手册里。）

## 项目文件

```
SKILL.md                  编排与路由（agent 执行时看这个）
GUIDE.md                  操作手册与最佳实践（人看这个）
SPEC.md                   完整设计规格（调度模型、闸门、错误码全表）
references/               各阶段细则（按阶段读，别一次读完）
genres/                   体裁体系（_core + practical / principle / project / interview；
                          新增体裁见 genres/README.md，可用体裁自动发现）
schemas/                  book / state / dag / contract 四份契约
scripts/                  闸门、DAG、账本、装配、缝合、校验
templates/                book.yaml 注释模板、dep-brief、patch 清单
tests/                    回归台：6 基线 + 29 注入（见 tests/README.md）
```

依赖：`pyyaml` 必需；`jsonschema` 缺失时 schema 校验降级为 info；
渲染图需要 node（`npx -y @mermaid-js/mermaid-cli`）。

```bash
python tests/run_tests.py     # 验证闸门回归台
```
