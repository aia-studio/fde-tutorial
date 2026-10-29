"""引用：答案里的话必须能点回原文的那一句。

运行：python src/ch04/cite.py
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

URL_TEMPLATE = "https://ticket.huayang.example/t/{ticket_no}#{anchor}"
MAX_QUOTE = 40

SOURCE = (
    "现象：运行半小时后出现周期性异响，转速越高越明显。"
    "处理：停机检查轴承润滑，补加润滑脂并空跑十分钟。"
    "结论：轴承缺油，补脂后异响消失。"
)

SECTIONS = {"现象": 1, "处理": 2, "结论": 3}


@dataclass(frozen=True)
class Citation:
    ticket_no: str
    section: str
    quote: str
    start: int
    url: str

    @property
    def length(self) -> int:
        return len(self.quote)


def key_sentence(text: str, section: str, terms: list[str]) -> tuple[str, int]:
    """在指定段落里挑第一句含关键词的话，不整段搬运。"""
    head = text.index(f"{section}：") + len(section) + 1
    tail = len(text)
    for name in SECTIONS:
        if name == section:
            continue
        pos = text.find(f"{name}：", head)
        if pos != -1:
            tail = min(tail, pos)
    segment = text[head:tail]

    cursor = 0
    first: tuple[str, int] | None = None
    for sent in segment.split("。"):
        if sent.strip():
            quote = sent.strip()[:MAX_QUOTE]
            pos = head + cursor + sent.index(quote)
            if first is None:
                first = (quote, pos)
            if any(term in sent for term in terms):
                return quote, pos
        cursor += len(sent) + 1
    return first if first else ("", head)


def build(ticket_no: str, section: str, terms: list[str], source: str = SOURCE) -> Citation:
    quote, start = key_sentence(source, section, terms)
    return Citation(
        ticket_no=ticket_no,
        section=section,
        quote=quote,
        start=start,
        url=URL_TEMPLATE.format(ticket_no=ticket_no, anchor=f"p{SECTIONS[section]}"),
    )


def render(answer: str, citations: list[Citation]) -> str:
    marks = "".join(f"[{c.ticket_no} · {c.section}]" for c in citations)
    return f"{answer} {marks}"


def verify(citation: Citation, source: str) -> bool:
    """按偏移回切原文，必须与引用逐字相同。"""
    return source[citation.start:citation.start + citation.length] == citation.quote


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text: str, size: int) -> str:
    return text + " " * max(0, size - width(text))


def main() -> None:
    citations = [
        build("HY-1002", "现象", ["异响"]),
        build("HY-1002", "处理", ["轴承", "润滑"]),
        build("HY-1002", "结论", ["缺油"]),
    ]

    print(f"{pad('工单', 10)}{pad('段', 6)}{pad('偏移', 6)}{pad('字数', 6)}回切校验")
    for c in citations:
        print(f"{pad(c.ticket_no, 10)}{pad(c.section, 6)}{pad(str(c.start), 6)}"
              f"{pad(str(c.length), 6)}{'一致' if verify(c, SOURCE) else '不一致'}")

    print()
    answer = "主轴异响多半是轴承缺油，补脂后可以消除。"
    print("渲染结果：")
    print(render(answer, citations))
    print()
    print("链接：")
    for c in citations:
        print(f"  {c.section} → {c.url}")


if __name__ == "__main__":
    main()
