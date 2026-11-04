"""Ch01 数据读取：先 utf-8-sig，再 gbk。"""

import csv


def load(path: str) -> list[dict]:
    for enc in ("utf-8-sig", "gbk"):
        try:
            with open(path, encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError("编码不支持")
