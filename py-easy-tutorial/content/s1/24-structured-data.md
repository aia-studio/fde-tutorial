+++
id = "s1-24-structured-data"
order = 24
stage = "s1"
official_group = "beginner"
title = "结构化数据：json、csv、toml"
concepts = ["json", "csv", "tomllib", "configparser", "serialization"]
prereq = [23]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：json"
url = "https://docs.python.org/3/library/json.html"

[[doc_refs]]
title = "Library Reference：csv"
url = "https://docs.python.org/3/library/csv.html"
+++

# 三种格式，三种脾气

配置文件、数据交换、日志导出——日常遇到的格式基本就这几类。选错格式会让代码变复杂：JSON 存不了注释，CSV 表达不了嵌套，TOML 不适合流式写入。

## JSON：默认的交换格式

```python
import json

raw = '{"name": "Ada", "age": 36, "langs": ["Python"]}'
data = json.loads(raw)

print(data["name"], data["age"])
print(json.dumps(data, ensure_ascii=False))
```

```expect
Ada 36
{"name": "Ada", "age": 36, "langs": ["Python"]}
```

`loads` / `dumps` 在字符串上操作，`load` / `dump` 直接对文件。记住 s 代表 string。

JSON 的类型映射很窄：Python 的 `tuple` 变成 `list`，`datetime` 根本不能直接序列化，`dict` 的键必须是字符串。所以"能 dump"不等于"能无损往返"。

## CSV：表格，但别手写分割

```python
import csv
import io

buf = io.StringIO()
writer = csv.writer(buf, lineterminator="\n")
writer.writerow(["name", "score"])
writer.writerow(["Ada", 90])

print(buf.getvalue().strip())

rows = list(csv.DictReader(io.StringIO(buf.getvalue())))
print(rows[0]["name"], rows[0]["score"])
```

```expect
name,score
Ada,90
Ada 90
```

`csv` 会正确处理引号、逗号、换行——手写 `line.split(",")` 在字段含逗号时立刻失效。`DictReader` 用首行当表头，读起来更直观。

## TOML：配置文件的现代选择

```python
import tomllib

config = tomllib.loads("""
[db]
host = "localhost"
port = 5432

[db.pool]
size = 5
""")

print(config["db"]["port"] + 1)
print(sorted(config["db"]))
print(config["db"]["pool"]["size"])
```

```expect
5433
['host', 'pool', 'port']
5
```

`tomllib` 是**只读**的：标准库只提供解析，写 TOML 要装 `tomli-w`。这是有意的设计——配置文件通常由人写，程序只读。

> [!tip] 怎么选
> 与外部系统交换用 JSON；给人看的配置用 TOML；表格数据（Excel 导出）用 CSV。别用 JSON 存配置——不能写注释，改一次要翻半天。

```quiz
question = "把含 `datetime` 的对象直接 `json.dumps` 会怎样？"
options = [
  "自动转成 ISO 字符串",
  "抛 TypeError：not JSON serializable",
  "转成时间戳数字",
  "静默丢弃该字段"
]
answer = 1
explain = "json 只认 dict/list/str/int/float/bool/None。日期要先自己转成字符串（如 isoformat()），或者用 default= 参数指定转换函数。"
```

## 小结

- `json.loads/dumps` 操作字符串，`load/dump` 操作文件。
- JSON 类型窄：元组变列表、日期不能直接序列化、键必须是字符串。
- CSV 用 `csv` 模块，别手工 split；`DictReader` 按表头取值。
- TOML 标准库只读不写，适合人写的配置。
