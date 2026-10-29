"""Markdown 子集 → 块数组（AST）。

刻意只支持写课件真正需要的语法，避免解析器变成半成品 CommonMark：

- 标题 `#`~`####`
- 段落、`**粗体**`、`*斜体*`、`` `行内代码` ``、`[链接](https://...)`
- 无序/有序列表（单层，不嵌套）
- 表格
- 引用，以及 `> [!warn] 标题` 形式的提示块
- 围栏代码块：```python run / ```python norun / ```text
- ```expect 紧跟在代码块后，声明预期输出（构建期会真跑一遍比对）
- ```quiz 内嵌 TOML

不支持的语法不会被静默吞掉：解析器要么降级成段落，要么在构建期报错。
"""

from __future__ import annotations

import html
import re
import tomllib

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
_FENCE_RE = re.compile(r"^\s*```(.*)$")
_HR_RE = re.compile(r"^\s*(?:---+|\*\*\*+)\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:\-|]+\|\s*$")

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def _inline(text: str) -> str:
    """行内格式化。先转义 HTML，再处理标记，避免注入。"""
    text = html.escape(text, quote=False)

    codes: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = _INLINE_CODE_RE.sub(_stash, text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    text = _LINK_RE.sub(
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text
    )
    text = re.sub(
        r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text
    )
    return text


def _starts_block(line: str) -> bool:
    stripped = line.lstrip()
    return bool(
        _FENCE_RE.match(line)
        or _HEADING_RE.match(line)
        or _HR_RE.match(line)
        or stripped.startswith(">")
        or stripped.startswith("|")
        or _LIST_RE.match(line)
    )


def _split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _parse_quiz(body: str, *, line_no: int) -> dict:
    try:
        data = tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"quiz 块 TOML 解析失败（第 {line_no} 行起）：{exc}") from exc

    question = data.get("question")
    options = data.get("options")
    answer = data.get("answer")
    explain = data.get("explain", "")

    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"quiz（第 {line_no} 行起）缺少 question")
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError(f"quiz（第 {line_no} 行起）options 至少需要两项")
    if not all(isinstance(o, str) and o.strip() for o in options):
        raise ValueError(f"quiz（第 {line_no} 行起）options 必须都是非空字符串")
    if not isinstance(answer, int) or isinstance(answer, bool):
        raise ValueError(f"quiz（第 {line_no} 行起）answer 必须是整数下标")
    if not 0 <= answer < len(options):
        raise ValueError(f"quiz（第 {line_no} 行起）answer={answer} 越界")
    if not isinstance(explain, str):
        raise ValueError(f"quiz（第 {line_no} 行起）explain 必须是字符串")

    return {
        "type": "quiz",
        "question": _inline(question),
        "options": [_inline(o) for o in options],
        "answer": answer,
        "explain": _inline(explain) if explain else "",
    }


def _parse_exercise(body: str, *, line_no: int) -> dict:
    try:
        data = tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"exercise 块 TOML 解析失败（第 {line_no} 行起）：{exc}") from exc

    where = f"exercise（第 {line_no} 行起）"
    ex_id = data.get("id")
    prompt = data.get("prompt")
    tests = data.get("tests")
    solution = data.get("solution")

    if not isinstance(ex_id, str) or not ex_id.strip():
        raise ValueError(f"{where} 缺少 id")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"{where} 缺少 prompt")
    if not isinstance(tests, list) or not tests:
        raise ValueError(f"{where} tests 至少需要一条")
    if not all(isinstance(t, str) and t.strip() for t in tests):
        raise ValueError(f"{where} tests 必须都是非空字符串")
    if not isinstance(solution, str) or not solution.strip():
        raise ValueError(f"{where} 缺少 solution（构建期要用它验证题目可解）")

    starter = data.get("starter", "")
    if not isinstance(starter, str):
        raise ValueError(f"{where} starter 必须是字符串")
    hints = data.get("hints", [])
    if not isinstance(hints, list) or not all(isinstance(h, str) for h in hints):
        raise ValueError(f"{where} hints 必须是字符串数组")
    names = data.get("test_names")
    if names is None:
        names = [f"测试 {i + 1}" for i in range(len(tests))]
    elif not isinstance(names, list) or len(names) != len(tests):
        raise ValueError(f"{where} test_names 数量必须与 tests 一致")

    xp = data.get("xp", 10)
    if not isinstance(xp, int) or isinstance(xp, bool) or xp < 0:
        raise ValueError(f"{where} xp 必须是非负整数")

    return {
        "type": "exercise",
        "id": ex_id.strip(),
        "title": _inline(data.get("title", "练习")),
        "prompt": _inline(prompt),
        "starter": starter,
        "solution": solution,
        "tests": [{"name": n, "code": t} for n, t in zip(names, tests)],
        "hints": [_inline(h) for h in hints],
        "xp": xp,
    }


def _parse_step(body: str, *, line_no: int) -> dict:
    try:
        data = tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"step 块 TOML 解析失败（第 {line_no} 行起）：{exc}") from exc

    code = data.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"step（第 {line_no} 行起）缺少 code")
    title = data.get("title", "")
    if not isinstance(title, str):
        raise ValueError(f"step（第 {line_no} 行起）title 必须是字符串")
    if len(code.split("\n")) > 40:
        raise ValueError(f"step（第 {line_no} 行起）超过 40 行，step 块只用于演示短代码")

    return {
        "type": "step",
        "title": _inline(title),
        "code": code,
    }


def _parse_glossary(body: str, *, line_no: int) -> dict:
    try:
        data = tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"glossary 块 TOML 解析失败（第 {line_no} 行起）：{exc}") from exc

    terms = data.get("terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError(f"glossary（第 {line_no} 行起）terms 至少需要一条")
    clean = []
    for item in terms:
        if not isinstance(item, list) or len(item) < 2:
            raise ValueError(f"glossary（第 {line_no} 行起）每条必须是 [术语, 定义, 课程编号?]")
        entry = {"term": _inline(str(item[0])), "definition": _inline(str(item[1]))}
        if len(item) > 2 and item[2] is not None:
            if not isinstance(item[2], int):
                raise ValueError(f"glossary（第 {line_no} 行起）课程编号必须是整数")
            entry["order"] = item[2]
        clean.append(entry)
    return {"type": "glossary", "terms": clean}


def parse(body: str) -> list[dict]:
    """把正文解析成块数组。出错时抛 ValueError，由构建层报告文件与行号。"""
    lines = body.split("\n")
    blocks: list[dict] = []
    code_seq = 0
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # ---- 围栏代码 ----
        fence = _FENCE_RE.match(line)
        if fence:
            info = fence.group(1).strip()
            start_line = i + 1
            j = i + 1
            buf: list[str] = []
            while j < total and not _FENCE_RE.match(lines[j]):
                buf.append(lines[j])
                j += 1
            if j >= total:
                raise ValueError(f"第 {start_line} 行的代码围栏没有闭合")

            code = "\n".join(buf).rstrip("\n")
            i = j + 1
            parts = info.split()
            lang = parts[0].lower() if parts else ""
            flags = {p.lower() for p in parts[1:]}

            if lang == "expect":
                if not blocks or blocks[-1]["type"] != "code":
                    raise ValueError(
                        f"第 {start_line} 行的 expect 块必须紧跟在一个代码块之后"
                    )
                blocks[-1]["expect"] = code
                continue

            if lang == "quiz":
                blocks.append(_parse_quiz(code, line_no=start_line))
                continue

            if lang == "exercise":
                blocks.append(_parse_exercise(code, line_no=start_line))
                continue

            if lang == "step":
                blocks.append(_parse_step(code, line_no=start_line))
                continue

            if lang == "glossary":
                blocks.append(_parse_glossary(code, line_no=start_line))
                continue

            runnable = lang in {"python", "py"} and "norun" not in flags
            code_seq += 1
            blocks.append(
                {
                    "type": "code",
                    "id": f"c{code_seq}",
                    "lang": "python" if lang in {"python", "py", ""} else lang,
                    "code": code,
                    "runnable": runnable,
                    "editable": runnable,
                    "expect": None,
                }
            )
            continue

        # ---- 标题 ----
        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            blocks.append(
                {"type": "heading", "level": level, "html": _inline(heading.group(2))}
            )
            i += 1
            continue

        # ---- 分隔线 ----
        if _HR_RE.match(line):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # ---- 表格 ----
        if stripped.startswith("|") and i + 1 < total and _TABLE_SEP_RE.match(lines[i + 1]):
            head = _split_row(line)
            j = i + 2
            rows: list[list[str]] = []
            while j < total and lines[j].strip().startswith("|"):
                rows.append(_split_row(lines[j]))
                j += 1
            blocks.append(
                {
                    "type": "table",
                    "head": [_inline(c) for c in head],
                    "rows": [[_inline(c) for c in row] for row in rows],
                }
            )
            i = j
            continue

        # ---- 引用 / 提示块 ----
        if stripped.startswith(">"):
            buf = []
            while i < total and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            first = buf[0] if buf else ""
            marker = re.match(r"^\[!(\w+)\]\s*(.*)$", first)
            if marker:
                kind = marker.group(1).lower()
                title = marker.group(2).strip()
                body_text = " ".join(x.strip() for x in buf[1:] if x.strip())
                blocks.append(
                    {
                        "type": "callout",
                        "kind": kind,
                        "title": _inline(title) if title else "",
                        "html": _inline(body_text),
                    }
                )
            else:
                body_text = " ".join(x.strip() for x in buf if x.strip())
                blocks.append({"type": "callout", "kind": "quote", "title": "", "html": _inline(body_text)})
            continue

        # ---- 列表 ----
        list_match = _LIST_RE.match(line)
        if list_match:
            ordered = list_match.group(2).endswith(".")
            items: list[str] = []
            while i < total:
                m = _LIST_RE.match(lines[i])
                if not m:
                    break
                text = m.group(3).strip()
                i += 1
                # 缩进续行并入当前条目
                while i < total and lines[i].strip() and lines[i].startswith(("  ", "\t")):
                    if _LIST_RE.match(lines[i]):
                        break
                    text += " " + lines[i].strip()
                    i += 1
                items.append(_inline(text))
            blocks.append({"type": "list", "ordered": ordered, "items": items})
            continue

        # ---- 段落 ----
        buf = [stripped]
        i += 1
        while i < total and lines[i].strip() and not _starts_block(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        blocks.append({"type": "p", "html": _inline(" ".join(buf))})

    return blocks
