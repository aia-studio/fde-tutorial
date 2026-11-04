"""切分：按业务结构切，不按固定长度切。

运行：python src/ch03/chunk.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SECTIONS = ("现象", "处理", "结论")
MIN_CHARS = 16
MAX_CHARS = 90
SENT = re.compile(r"(?<=。)")

DOCS: list[dict[str, str]] = [
    {"ticket_no": "HY-1001", "title": "设备无法开机",
     "body": "现象：通电后指示灯不亮，电源线已确认插紧。\n"
             "处理：检查急停开关与门锁回路，复位后重新上电。\n"
             "结论：急停未复位，复位后设备正常启动。"},
    {"ticket_no": "HY-1002", "title": "主轴异响",
     "body": "现象：运行半小时后出现周期性异响，转速越高越明显。\n"
             "处理：停机检查轴承润滑，补加润滑脂并空跑十分钟。\n"
             "结论：轴承缺油，补脂后异响消失。"},
    {"ticket_no": "HY-1003", "title": "报错 E-204",
     "body": "现象：面板显示 E-204，加工中自动停机。\n"
             "处理：按手册查为过热保护，清理散热滤网并静置降温。\n"
             "结论：滤网堵塞导致散热不良，清理后未再复现。"},
    {"ticket_no": "HY-1004", "title": "换刀卡顿",
     "body": "现象：换第二把刀时停顿约两秒，之后动作恢复。\n"
             "处理：检查刀库气压与传感器信号，发现气压低于设定值。\n"
             "结论：气路接头漏气，更换接头后换刀顺畅。"},
    {"ticket_no": "HY-1005", "title": "精度漂移",
     "body": "现象：连续加工八小时后尺寸偏大，重新对刀即恢复。\n"
             "处理：检查丝杠热伸长，增加预热程序并修正补偿参数。\n"
             "结论：热变形引起漂移，加入预热后尺寸收敛。"},
    {"ticket_no": "HY-1006", "title": "远程连不上",
     "body": "现象：客户内网封禁 443 端口，远程诊断工具无法建连。\n"
             "处理：改用客户跳板机做端口转发，申请临时账号。\n"
             "结论：端口策略限制，走跳板机后诊断可用。"},
    {"ticket_no": "HY-1007", "title": "冷却液报警",
     "body": "现象：液位显示正常，但面板持续报警。\n"
             "处理：拆检浮子开关，发现铁屑卡住浮子。\n"
             "结论：铁屑导致误报，清理并加装滤网后报警消除。"},
    {"ticket_no": "HY-1008", "title": "系统升级失败",
     "body": "现象：升级包校验不通过，进度停在三成左右。\n"
             "处理：重新下载升级包，核对摘要值后再安装。\n"
             "结论：安装包传输损坏，换包后升级成功。"},
]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    ticket_no: str
    title: str
    section: str
    text: str


def split_sections(body: str) -> list[tuple[str, str]]:
    """按「现象 / 处理 / 结论」三段切，段名不在正文里出现就丢掉。"""
    parts: list[tuple[str, str]] = []
    for line in body.splitlines():
        line = line.strip()
        for name in SECTIONS:
            prefix = f"{name}："
            if line.startswith(prefix):
                parts.append((name, line[len(prefix):].strip()))
                break
    return parts


def split_long(section: str, text: str) -> list[tuple[str, str]]:
    """一段超过上限时按句号断开，不硬切。"""
    if len(text) <= MAX_CHARS:
        return [(section, text)]
    out: list[tuple[str, str]] = []
    buf = ""
    for sent in SENT.split(text):
        if not sent:
            continue
        if buf and len(buf) + len(sent) > MAX_CHARS:
            out.append((section, buf))
            buf = sent
        else:
            buf += sent
    if buf:
        out.append((section, buf))
    return out


def chunk_doc(doc: dict[str, str]) -> list[Chunk]:
    chunks: list[Chunk] = []
    seq = 0
    for section, text in split_sections(doc["body"]):
        for name, piece in split_long(section, text):
            if len(piece) < MIN_CHARS:
                continue
            seq += 1
            chunks.append(Chunk(
                chunk_id=f"{doc['ticket_no']}#{seq}",
                ticket_no=doc["ticket_no"],
                title=doc["title"],
                section=name,
                text=piece,
            ))
    return chunks


def chunk_docs(docs: list[dict[str, str]]) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_doc(doc))
    return out


def main() -> None:
    chunks = chunk_docs(DOCS)
    print(f"文档 {len(DOCS)} 篇，切成 {len(chunks)} 块")
    print(f"{'块 id':<14}{'段':<6}{'字数':>4}  正文")
    for c in chunks[:6]:
        print(f"{c.chunk_id:<14}{c.section:<6}{len(c.text):>4}  {c.text[:28]}…")
    print("…")
    by_section: dict[str, int] = {}
    for c in chunks:
        by_section[c.section] = by_section.get(c.section, 0) + 1
    print("按段落分布：" + "，".join(f"{k} {v}" for k, v in by_section.items()))
    lens = [len(c.text) for c in chunks]
    print(f"块长：最短 {min(lens)}，最长 {max(lens)}，均 {sum(lens) // len(lens)}")


if __name__ == "__main__":
    main()
