"""纯文本工具：分词、切句、重合长度。各章共用，不含业务语义。"""

from __future__ import annotations

import re

LATIN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
HAN_RUN = re.compile(r"[\u4e00-\u9fff]+")
SENT_END = re.compile(r"(?<=[。！？；])")


def tokens(text: str) -> list[str]:
    """中文取双字，英文与数字整词，保证型号与错误码不被拆碎。"""
    out = [m.group(0).lower() for m in LATIN.finditer(text)]
    for run in HAN_RUN.findall(text):
        if len(run) == 1:
            out.append(run)
        out.extend(run[i:i + 2] for i in range(len(run) - 1))
    return out


def split_sentences(text: str) -> list[str]:
    """按中文句末标点切句，保留标点。"""
    return [s.strip() for s in SENT_END.split(text) if s.strip()]


def overlap_chars(a: str, b: str) -> int:
    """最长公共子串长度，用来判断两段文字讲的是不是同一句。"""
    best = 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best
