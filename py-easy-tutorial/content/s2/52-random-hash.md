+++
id = "s2-52-random-hash"
order = 52
stage = "s2"
official_group = "moderate"
title = "随机、哈希与密钥"
concepts = ["random", "seed", "secrets", "hashlib", "uuid"]
prereq = [50]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：random"
url = "https://docs.python.org/3/library/random.html"

[[doc_refs]]
title = "Library Reference：secrets"
url = "https://docs.python.org/3/library/secrets.html"
+++

# 两种"随机"，用途完全不同

`random` 是**伪随机**：给定种子，序列完全可复现。这对测试是优点，对密码是灾难。安全场景一律用 `secrets`，这条线划清了两者边界。

## `random`：可复现，可测试

```python
import random

random.seed(42)
print(random.randint(1, 10))
print(random.choice(["a", "b", "c"]))
print(round(random.random(), 4))
```

```expect
2
a
0.7416
```

`seed(42)` 之后，三个调用的结果**永远一样**。测试里需要"随机但可复现"的数据就靠这个：种子固定，断言才能写死。

不设种子时，默认从系统熵源取种——每次运行都不同。

## `shuffle` 与 `sample`

```python
import random

random.seed(7)
deck = list(range(5))
random.shuffle(deck)
print(deck)

print(random.sample(deck, 2))
```

```expect
[4, 0, 3, 1, 2]
[4, 2]
```

`shuffle` 原地打乱；`sample` 无放回抽样，不会重复取同一个元素。抽卡、抽奖名单用 `sample` 而不是循环 `choice`。

## `secrets`：安全随机

```python
import secrets

token = secrets.token_hex(16)
print(len(token))
print(secrets.compare_digest(token, token))
```

```expect
32
True
```

`token_hex(16)` 生成 32 个十六进制字符（16 字节熵）。`compare_digest` 做**常数时间比较**，防止通过比较耗时推断内容——校验令牌用它，别用 `==`。

## 哈希：不可逆的指纹

```python
import hashlib

h = hashlib.sha256(b"abc")
print(h.hexdigest()[:16])
print(h.digest_size)
```

```expect
ba7816bf8f01cfea
32
```

输入差一个字节，输出完全不同；无法从哈希反推输入。密码存储用 `hashlib.pbkdf2_hmac` 加盐迭代，**绝不存明文**，也别用普通 `sha256` 存密码（没有盐，可被彩虹表破解）。

> [!warn] 什么时候用哪个
> 测试造数据、随机抽样、洗牌 → `random`；令牌、密钥、密码重置链接 → `secrets`；指纹、文件校验 → `hashlib`；全局唯一 ID → `uuid.uuid4()`。选错的前一个字节就是安全事故。

```quiz
question = "生成用户密码重置链接里的随机令牌，应该用哪个？"
options = [
  "random.random()",
  "random.seed(时间戳) 后取值",
  "secrets.token_urlsafe(32)",
  "hashlib.md5(用户名).hexdigest()"
]
answer = 2
explain = "重置令牌必须不可预测：random 是可复现的伪随机（知道种子就能推算），md5 可被穷举。secrets 从操作系统熵源取数，专门为安全用途设计。"
```

## 小结

- `random` 伪随机可复现（`seed` 固定），适合测试与模拟。
- `shuffle` 原地打乱，`sample` 无放回抽样。
- 安全令牌、密钥一律 `secrets`，比较用 `compare_digest`。
- 密码存储用 `pbkdf2_hmac` 加盐，指纹校验用 `sha256`。
