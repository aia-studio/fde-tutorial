+++
id = "s0-09-dict-set"
order = 9
stage = "s0"
official_group = "beginner"
title = "字典与集合"
concepts = ["dict", "set", "hash", "get", "setdefault"]
prereq = [8]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Tutorial 5.5：字典"
url = "https://docs.python.org/3/tutorial/datastructures.html#dictionaries"

[[doc_refs]]
title = "Library Reference：映射类型 dict"
url = "https://docs.python.org/3/library/stdtypes.html#mapping-types-dict"
+++

# 靠哈希找东西，快到可以当常数

字典和集合是 Python 里唯一两个**基于哈希**的内置容器。理解"为什么键必须可哈希"，就理解了它们的全部约束。

## 字典：键值对，按键取

```python
user = {"name": "Ada", "lang": "Python"}

print(user["name"])
print(user.get("age", "未知"))
print(sorted(user))
```

```expect
Ada
未知
['lang', 'name']
```

`user["age"]` 会抛 `KeyError`，`user.get("age")` 返回 `None` 或你给的后备值。**不确定键在不在，就用 `get`**。

统计词频是最典型的写法：

```python
counts = {}
for word in ["a", "b", "a", "c", "a"]:
    counts[word] = counts.get(word, 0) + 1

print(counts)
print(counts["a"])
```

```expect
{'a': 3, 'b': 1, 'c': 1}
3
```

字典保持**插入顺序**（3.7 起的语言保证），所以打印结果每次一致。但这不意味着字典是"有序容器"——它是映射，别依赖顺序做逻辑。

## 集合：只关心"在不在"

```python
a = {1, 2, 3}
b = {2, 3, 4}

print(sorted(a & b))
print(sorted(a | b))
print(sorted(a - b))
print(2 in a)
```

```expect
[2, 3]
[1, 2, 3, 4]
[1]
True
```

集合的价值在 `in`：判断元素是否存在，列表要一个个比（O(n)），集合直接算哈希（O(1)）。数据量大时这是数量级的差别——第 53 课会用 `timeit` 量给你看。

> [!tip] 去重最快的写法
> `list(set(items))` 一行去重。但注意它会打乱顺序；要保序用 `dict.fromkeys(items)`。

## 为什么键必须可哈希

```python
try:
    mapping = {[1, 2]: "值"}
except TypeError as exc:
    print(type(exc).__name__, exc)
```

```expect
TypeError cannot use 'list' as a dict key (unhashable type: 'list')
```

哈希表的原理是：用键算出桶的位置，把值放进去。如果键能变，它的哈希值也会变，之后按原来的键就找不到那个桶了——表结构直接失效。

所以规则很简单：**可变对象不能当键**（`list`、`dict`、`set`），不可变对象可以（`int`、`str`、`tuple`，前提是元组里每个元素也可哈希）。

```python
print({(1, 2): "元组可以"})
print({"a": 1, "b": 2}.keys())
```

```expect
{(1, 2): '元组可以'}
dict_keys(['a', 'b'])
```

```quiz
question = "下面哪个**不能**作为字典的键？"
options = ["(1, 2)", "\"abc\"", "[1, 2]", "42"]
answer = 2
explain = "列表可变，哈希值会随内容变化，破坏哈希表结构，所以不可哈希。元组不可变，只要元素都可哈希就能当键。"
```

## 小结

- `d[k]` 缺键抛 `KeyError`，`d.get(k, default)` 不抛。
- 字典保持插入顺序，但它是映射不是序列。
- 集合的 `in` 是 O(1)，列表是 O(n)。
- 键必须可哈希：可变对象不行，元组行（元素也得可哈希）。
