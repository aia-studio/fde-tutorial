# 示例数据

只放生成脚本，不放数据本体。每个脚本固定 SEED，并在开头 `random.seed(SEED)`。

| 脚本 | 产物 | 规模 | 用途 |
| --- | --- | --- | --- |
| `gen_tickets.py` | `data/tickets.csv` | 48 行 / 约 12 KB | 全书唯一的语料：客服工单，字段为工单号、产品、类别、渠道、日期、现象、处理 |

生成命令：

```bash
cd src
python -m data.gen_tickets
```

`SEED = 42`，日期与渠道由它决定，重复运行结果完全一致。评测集
`data/eval/questions.jsonl` 是人写的标注，不由脚本生成，改了语料要人工复核。
