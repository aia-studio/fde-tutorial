# tests/fixture · check.py 自测样本

一本 2 章的迷你书，用来验证闸门是否按预期工作。

```bash
python scripts/check.py --book tests/fixture
python scripts/check.py --book tests/fixture --json
```

## 设计：一正一反

| 文件 | 角色 | 预期 |
| --- | --- | --- |
| `chapters/ch01.md` | 正例 | `0 error, 0 warn`，输出「通过」 |
| `chapters/ch02.md` | 反例 | 故意埋了 8 类错误，验证闸门抓得住 |

`04-chapter-plans/` 是两章的依赖声明，`assets/ch01/fig-01-0-map.svg` 是图产物。

## ch02 故意埋的雷（每条对应一条闸门）

| 闸门 | 埋的错 |
| --- | --- |
| S02 | 漏写 `## 自查清单` 骨架段 |
| S16 | 多了个不合规的 `## 正文` H2（正文小节应直接用 H3） |
| S13 | 常见坑只有 2 条，不满足 practical 的 `[3,5]` |
| S07 | 用了白名单外的 `【重要】`（应改为 `【注意】`） |
| S09 | 出现禁用词「很简单」 |
| R02 | 引用了不存在的 `src/ch02/db.py` |
| R04 | 越级引用「第 3 章第 2 节」（应写 `Ch03`） |
| R06 | 引用了未声明的 `Ch07` |
| S15 (warn) | 小节未标 `> 路径：必读/选读/参考` |
| R05 (warn) | 章纲声明了 `references: ["03"]` 却没在正文引用 |

当前预期汇总：`8 error, 2 warn`，退出码 1。**这些错误是刻意保留的，不要"修好" ch02。**

## 账本说明

`.book/` 下四本账目前是**空**的（glossary 无术语，claims/promises/ladder 无记录）。
因此事实组(F)与一致性组(X)没有数据可判，不会误报——但也不代表"检查过"。

想验证 F/X 能抓违规，临时写一条数据再跑即可，例如往 `.book/promises.jsonl`
写 `{"id":"P1","status":"open"}` 会触发 X06「承诺未结清，阻断装配」，
或往正文加「召回率提升 92%」而 claims 无记录会触发 F01。验证后清空账本恢复。
