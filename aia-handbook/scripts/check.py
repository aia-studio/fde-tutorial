#!/usr/bin/env python3
"""check.py —— 闸门执行器。

实现 SPEC §8 的五组闸门：
    structure(S) / reference(R) / code(C) / facts(F) / consistency(X)

分组原则：
- 单章级闸门按章跑，可 --chapter 指定；
- 全书级闸门（跨章重复、import 子图、ladder 单调、promises open）在未指定
  --chapter 时额外跑一次，作为装配前的阻断项。

账本（.book/）不存在时，依赖账本的闸门优雅跳过——没有账本不等于违规，
但会在输出里标注 skipped，避免"全绿"掩盖"根本没查"。

用法:
    python scripts/check.py --book ../my-book
    python scripts/check.py --book ../my-book --chapter ch03
    python scripts/check.py --book ../my-book --json
    python scripts/check.py --book ../my-book --gates structure,reference

退出码：有 error 返回 1，否则 0。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("需要 pyyaml：python -m pip install pyyaml")

HAN = re.compile(r"[\u4e00-\u9fff]")
ANNOT = re.compile(r"【([^】]{1,8})】")
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
SRC_REF = re.compile(r"src/[A-Za-z0-9_\-./]+")
CH_REF = re.compile(r"Ch\s*(\d{2})", re.IGNORECASE)
BAD_XREF_1 = re.compile(r"第\s*[0-9一二三四五六七八九十]+\s*章")
BAD_XREF_2 = re.compile(r"\d+\.\d+\s*节")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ORDER_PREFIX = re.compile(r"^(\d+[.、)]|[一二三四五六七八九十]+[、.]|第[一二三四五六七八九十\d]+[章节])\s*")
PATH_MARK = re.compile(r"^>\s*路径[：:]\s*(必读|选读|参考)\s*$")
NUM_UNIT = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|倍|ms|QPS|万元|亿|GB|MB|TB|人天)")
# 裸统计数字：带小数（0.37）或 ≥3 位整数（1200）。只在同段出现断言词时才要求登记。
BARE_STAT = re.compile(r"(?<![\d.])\d+\.\d+(?![\d])|(?<![\d.])\d{3,}(?![\d])")
SECRET = re.compile(
    r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{8,}|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"
    r"|api[_-]?key\s*[=:]\s*['\"][^'\"]{6,})"
)
SECRET_PLACEHOLDER = re.compile(r"sk-xxx|your-api-key|<[^>]+>|\$\{|os\.environ|getenv|示例|placeholder")

# SPEC §8.1 ② 内置通用断言词表；与 genre / book 的 assertion_words 取并集
BUILTIN_ASSERTION_WORDS = ["提升", "下降", "占比", "市场规模", "薪酬", "失败率", "准确率",
                           "召回率", "延迟", "吞吐", "成本", "命中率", "成功率", "增长",
                           "错误率", "可用性", "拒答率", "点击率", "转化率", "覆盖率",
                           "精确率", "漏检", "误报", "耗时", "花费", "上限", "下限"]
PROMISE_TRIGGERS = ["后面会", "接下来", "稍后", "下一章", "留到"]

# 结构型数字（章号/图号/表号/节号/年份/列表序号）不是断言，扫描前剔除
STRUCT_NUM = re.compile(
    r"(?:Ch|ch)\d{2,}"
    r"|图\s*\d+[-–—]\d+"
    r"|表\s*\d+[-–—]\d+"
    r"|式\s*\d+[-–—]?\d*"
    r"|第\s*\d+\s*[章节步层次类档]"
    r"|\b(?:19|20)\d{2}\s*年?"
    r"|\b\d+\.\d+\s*[节小]"
    r"|^\s*\d+[.、)]"
    r"|\d+\s*/\s*\d+"
)

# 汉字数字：零点三七 / 百分之三十五
CN_DEC = re.compile(r"零点[零一二三四五六七八九]+")
CN_PCT = re.compile(r"百分之[零一二三四五六七八九十百]+")
CN_DIGIT = {c: i for i, c in enumerate("零一二三四五六七八九")}


def _cn_int(s: str) -> int | None:
    """把「三十五」「一百二十」这类整数读法转成 int。"""
    if not s:
        return None
    total, cur = 0, 0
    for ch in s:
        if ch in CN_DIGIT:
            cur = CN_DIGIT[ch]
        elif ch == "十":
            total += (cur or 1) * 10
            cur = 0
        elif ch == "百":
            total += (cur or 1) * 100
            cur = 0
        else:
            return None
    return total + cur


def _cn2num(text: str) -> tuple[str, list[tuple[float, str]]]:
    """把一段文字里的汉字数字换成阿拉伯数字，返回 (新文本, [(数值, 单位)])。

    支持「零点三七」「负零点一二」「百分之三十五」，并带出单位，
    否则 -0.125 会被读成 +0.12、35% 会被读成 35，与账本对不上。
    """
    found: list[tuple[float, str]] = []

    def dec(m: re.Match) -> str:
        digits = "".join(str(CN_DIGIT[c]) for c in m.group(0)[2:])
        v = float("0." + digits) if digits else 0.0
        neg = m.string[max(0, m.start() - 1):m.start()] == "负"
        if neg:
            v = -v
        found.append((v, ""))
        return f"-{v:g}" if neg else f"{v:g}"

    def pct(m: re.Match) -> str:
        n = _cn_int(m.group(0)[3:])
        if n is None:
            return m.group(0)
        found.append((float(n), "%"))
        return f"{n}"

    return CN_PCT.sub(pct, CN_DEC.sub(dec, text)), found

GENRE_DIR = Path(__file__).resolve().parent.parent / "genres"


# ---------------------------------------------------------------- 数据模型

@dataclass
class Finding:
    level: str          # error | warn | info
    gate: str           # structure | reference | code | facts | consistency
    code: str           # S01
    chapter: str
    msg: str
    hint: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "gate": self.gate, "code": self.code,
                "chapter": self.chapter, "msg": self.msg, "hint": self.hint}


@dataclass
class Section:
    title: str
    line: int
    body: list[str] = field(default_factory=list)


@dataclass
class Chapter:
    path: Path
    name: str
    fm: dict = field(default_factory=dict)       # 正文 front-matter
    h1: str = ""
    h2: list[Section] = field(default_factory=list)
    h3: list[Section] = field(default_factory=list)
    countable: str = ""          # 计入字数的文本（正文 + 表格）
    prose: str = ""              # 仅正文，用于句长/段长
    code_blocks: list[list[str]] = field(default_factory=list)
    tables: list[list[str]] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)
    annotations: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    @property
    def han_count(self) -> int:
        return len(HAN.findall(self.countable))


@dataclass
class Repo:
    """一本书的解析结果。"""
    root: Path
    book: dict[str, Any]
    cfg: dict[str, Any]
    core: dict[str, Any]
    plans: dict[str, dict] = field(default_factory=dict)
    ledger: dict[str, Any] = field(default_factory=dict)

    def plan(self, ch: str) -> dict:
        return self.plans.get(ch, {})


# ---------------------------------------------------------------- 配置解析

def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _ch_range(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    """字数区间取交集；交集为空时取更严的一侧（由调用方提示）。"""
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    return (lo, hi) if lo <= hi else (max(a[0], b[0]), min(a[1], b[1]))


def _load_ledger(book_dir: Path) -> dict[str, Any]:
    """读 .book 账本；不存在则 exists=False，依赖账本的闸门会跳过。"""
    b = book_dir / ".book"
    led: dict[str, Any] = {"exists": b.is_dir(), "glossary": [],
                           "claims": [], "promises": [], "ladder": []}
    if not b.is_dir():
        return led
    g = b / "glossary.json"
    if g.exists():
        try:
            data = json.loads(g.read_text(encoding="utf-8"))
            led["glossary"] = data.get("terms", []) if isinstance(data, dict) else data
        except (OSError, json.JSONDecodeError):
            pass
    for fname, key in [("claims.jsonl", "claims"), ("promises.jsonl", "promises"),
                       ("ladder.jsonl", "ladder")]:
        p = b / fname
        if p.exists():
            for ln in p.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    led[key].append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    sf = b / "style-fingerprint.json"
    if sf.exists():
        try:
            led["style"] = json.loads(sf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            led["style"] = {}
    return led


def load_repo(book_dir: Path) -> Repo:
    book = _load_yaml(book_dir / "book.yaml")
    genres = book.get("genre") or []
    if isinstance(genres, str):
        genres = [genres]
    if not genres:
        sys.exit("book.yaml 缺少 genre")

    core = _load_yaml(GENRE_DIR / "_core.yaml")

    main = _load_yaml(GENRE_DIR / f"{genres[0]}.yaml")
    cfg: dict[str, Any] = {
        "genre_list": genres,
        "main_genre": genres[0],
        "skeleton": main.get("skeleton", []),
        "exclusive": main.get("exclusive", {}),
        "annotations": list(main.get("stackable", {}).get("annotations", [])),
        "defaults": dict(main.get("defaults", {})),
        "code_required": bool(main.get("stackable", {}).get("code_required", False)),
        "anti_patterns": list(main.get("anti_patterns", [])),
        "fingerprint": dict(main.get("fingerprint", {})),
        "plan_required_fields": list(main.get("plan_required_fields", [])),
        "assertion_words": list(BUILTIN_ASSERTION_WORDS),
        "tolerance": 0.005,
    }
    for w in main.get("assertion_words", []) or book.get("claims", {}).get("assertion_words", []):
        if w not in cfg["assertion_words"]:
            cfg["assertion_words"].append(w)

    # 副类型：只贡献可叠加维度（取并 / 取严）
    for g in genres[1:]:
        sub = _load_yaml(GENRE_DIR / f"{g}.yaml")
        for a in sub.get("stackable", {}).get("annotations", []):
            if a not in cfg["annotations"]:
                cfg["annotations"].append(a)
        cfg["code_required"] = cfg["code_required"] or bool(
            sub.get("stackable", {}).get("code_required", False))
        d = sub.get("defaults", {})
        if "words_per_chapter" in d:
            cfg["defaults"]["words_per_chapter"] = _ch_range(
                tuple(cfg["defaults"].get("words_per_chapter", d["words_per_chapter"])),
                tuple(d["words_per_chapter"]))
        if "figures_min" in d:
            cfg["defaults"]["figures_min"] = max(
                cfg["defaults"].get("figures_min", 0), d["figures_min"])
        if "tables_min" in d:
            cfg["defaults"]["tables_min"] = max(
                cfg["defaults"].get("tables_min", 0), d["tables_min"])
        if "info_density_min" in d:
            cfg["defaults"]["info_density_min"] = max(
                cfg["defaults"].get("info_density_min", 0), d["info_density_min"])
        for p in sub.get("anti_patterns", []):
            if p not in cfg["anti_patterns"]:
                cfg["anti_patterns"].append(p)
        for w in sub.get("assertion_words", []):
            if w not in cfg["assertion_words"]:
                cfg["assertion_words"].append(w)
        if sub.get("exclusive", {}).get("skeleton") != cfg["exclusive"].get("skeleton"):
            print(f"! 排他维度冲突：{cfg['main_genre']}={cfg['exclusive'].get('skeleton')} "
                  f"vs {g}={sub.get('exclusive', {}).get('skeleton')}（已按主类型处理）",
                  file=sys.stderr)

    # book.yaml 覆盖
    lim = book.get("limits", {})
    defaults = cfg["defaults"]
    if "code_block_max_lines" in lim:
        defaults["code_block_max_lines"] = lim["code_block_max_lines"]
    if "info_density_min" in lim:
        defaults["info_density_min"] = lim["info_density_min"]
    if "tolerance" in book.get("claims", {}):
        cfg["tolerance"] = book["claims"]["tolerance"]
    for w in book.get("claims", {}).get("assertion_words", []):
        if w not in cfg["assertion_words"]:
            cfg["assertion_words"].append(w)

    scale = book.get("scale", {})
    if scale.get("words_per_chapter"):
        defaults["words_per_chapter"] = tuple(scale["words_per_chapter"])
    if scale.get("chapters"):
        cfg["chapters"] = scale["chapters"]

    cfg["book"] = book
    plans = {}
    plan_dir = book_dir / book.get("paths", {}).get("plans", "04-chapter-plans")
    if plan_dir.is_dir():
        for p in sorted(plan_dir.glob("ch*.md")):
            plans[p.stem] = parse_front_matter(p.read_text(encoding="utf-8"))
    return Repo(root=book_dir, book=book, cfg=cfg, core=core,
                plans=plans, ledger=_load_ledger(book_dir))


def parse_front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


# ---------------------------------------------------------------- 章节解析

def parse_chapter(path: Path) -> Chapter:
    raw = path.read_text(encoding="utf-8")
    fm: dict = {}
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end > 0:
            fm = parse_front_matter(raw)
            body = raw[end + 4:]

    ch = Chapter(path=path, name=path.stem, fm=fm)
    lines = body.splitlines()
    ch.lines = lines

    in_fence = False
    fence_buf: list[str] = []
    countable: list[str] = []
    prose: list[str] = []
    table_buf: list[str] = []

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            ch.tables.append(table_buf)
            countable.extend(table_buf)
            table_buf = []

    for i, line in enumerate(lines):
        if FENCE.match(line):
            if in_fence:
                ch.code_blocks.append(fence_buf)
                fence_buf = []
                in_fence = False
            else:
                flush_table()
                in_fence = True
            continue
        if in_fence:
            fence_buf.append(line)
            continue

        m = HEADING.match(line)
        if m:
            flush_table()
            level, title = len(m.group(1)), m.group(2)
            sec = Section(title=title, line=i)
            if level == 1:
                ch.h1 = title
            elif level == 2:
                ch.h2.append(sec)
            elif level == 3:
                ch.h3.append(sec)
            continue

        if line.lstrip().startswith(">"):
            flush_table()
            ch.quotes.append(line.lstrip("> ").strip())
            continue

        if line.strip().startswith("|"):
            table_buf.append(line)
            continue
        flush_table()

        if line.strip().startswith("!["):
            for m2 in IMAGE.finditer(line):
                ch.images.append(m2.group(1))
            continue

        countable.append(line)
        prose.append(line)
        ch.annotations.extend(ANNOT.findall(line))

    flush_table()
    if in_fence and fence_buf:
        ch.code_blocks.append(fence_buf)

    ch.countable = "\n".join(countable)
    ch.prose = "\n".join(prose)

    marks = sorted([(s.line, 2, idx) for idx, s in enumerate(ch.h2)] +
                   [(s.line, 3, idx) for idx, s in enumerate(ch.h3)])
    for pos, (line_no, level, idx) in enumerate(marks):
        # 段内容止于下一个任意标题：H2 骨架段不含其后的 H3 正文小节，
        # 否则 opening 的 max_lines 会把整章正文都算进去。
        end = marks[pos + 1][0] if pos + 1 < len(marks) else len(lines)
        target = ch.h2[idx] if level == 2 else ch.h3[idx]
        target.body = lines[line_no + 1:end]
    return ch


def _norm(t: str) -> str:
    t = ORDER_PREFIX.sub("", t.strip())
    return re.sub(r"[\s*`：:]+", "", t)


def _count_in(body: Iterable[str], pattern: str) -> int:
    return sum(1 for ln in body if re.search(pattern, ln))


def _count_entries(lines: Iterable[str]) -> int:
    """段内条目数：编号/项目符号列表项，或表格数据行（排除表头与分隔行）。"""
    n = 0
    in_table = False
    row_idx = 0
    for ln in lines:
        s = ln.strip()
        if re.match(r"^([-*+] |\d+[.)] )", s):
            n += 1
            in_table = False
            row_idx = 0
            continue
        if s.startswith("|"):
            if not in_table:
                in_table = True
                row_idx = 0
            row_idx += 1
            if row_idx <= 2:                       # 表头、分隔行
                continue
            if re.match(r"^\|[\s:\-|]+\|?$", s):  # 兜底：额外分隔行
                continue
            n += 1
        else:
            in_table = False
            row_idx = 0
    return n


def _count_actionable(ch: Chapter) -> int:
    """SPEC §16.1 可操作单元数。"""
    n = 0
    for b in ch.code_blocks:                       # 代码块
        n += 2 if len([x for x in b if x.strip()]) > 30 else 1
    n += sum(1 for t in ch.tables if len(t) >= 3)  # ≥3 行表格
    n += len(ch.images)                            # 图
    runs = 0                                       # 连续 ≥2 步的编号列表
    run = 0
    for ln in ch.countable.splitlines():
        if re.match(r"^\s*\d+[.)]\s", ln):
            run += 1
        else:
            if run >= 2:
                runs += 1
            run = 0
    if run >= 2:
        runs += 1
    n += runs
    n += sum(1 for ln in ch.countable.splitlines()  # 带验收标准的练习
             if re.match(r"^\s*\d+[.)]\s", ln) and "验收" in ln)
    return n


def _ngrams(text: str, n: int = 5) -> list[str]:
    s = "".join(HAN.findall(text))
    return [s[i:i + n] for i in range(len(s) - n + 1)] if len(s) >= n else []


UNIT_FAMILY = {
    "%": "pct", "％": "pct", "百分比": "pct", "percent": "pct",
    "倍": "times", "times": "times",
    "ms": "ms", "毫秒": "ms",
    "qps": "qps",
    "人天": "manday", "万元": "cny", "亿": "cny",
}


def _unit_family(u: str) -> str:
    u = (u or "").strip()
    return UNIT_FAMILY.get(u.lower(), UNIT_FAMILY.get(u, "other"))


def _unit_ok(claim: dict, text_unit: str) -> bool:
    """单位不同就不能互相顶替：0.95 的 ratio 不该认领正文里的 1%。

    只有正文没写单位时才放宽（表格里裸写 928，单位在表头）。
    """
    if not text_unit:
        return True
    cu = str(claim.get("unit") or "")
    if not cu:
        return True
    return _unit_family(cu) == _unit_family(text_unit)


def _val_claimed(claims: list[dict], numstr: str, tol: float, unit: str = "") -> bool:
    """SPEC §8.1 ③：按「显示精度」记账，而不是固定 0.5 绝对容差。

    正文常把 0.223 写成「零点二二」，把 928 写成「928」。
    判据是「登记值四舍五入到正文的位数后与之相等」：
    容差 = max(|v|*tol, 半个末位)。旧实现用 max(0.5, |v|*tol)，
    会让 0.37 与 0.00–0.87 的任何登记值互相顶替，事实校验在小数区间等于失效。
    另加单位一致性判断，避免 0.95 认领 1%。
    """
    txt = str(numstr).strip().rstrip("%％")
    try:
        v = float(txt)
    except (TypeError, ValueError):
        return False
    dec = len(txt.split(".")[1]) if "." in txt else 0
    half_ulp = 0.5 * (10 ** -dec) * 1.001
    for c in claims:
        if not _unit_ok(c, unit):
            continue
        try:
            cv = float(c.get("value"))
        except (TypeError, ValueError):
            cv = None
        vals = [cv] if cv is not None else []
        try:
            vals += [float(x) for x in c.get("values", []) or []]
        except (TypeError, ValueError):
            pass
        for cand in vals:
            if abs(cand - v) <= max(abs(v) * tol, half_ulp):
                return True
    return False


# ---------------------------------------------------------------- 文风指纹

def chapter_metrics(ch: Chapter) -> dict[str, float]:
    """一章的可量化文风指标，口径与 style-fingerprint.json 的 metrics 一一对应。"""
    sents = [s for s in re.split(r"[。！？；]", ch.prose) if len(HAN.findall(s)) >= 3]
    paras = [p for p in re.split(r"\n\s*\n", ch.prose) if p.strip()]
    kchars = ch.han_count / 1000 if ch.han_count else 1e-9
    secs = len(ch.h3) or len(ch.h2) or 1
    return {
        "avg_sentence_len": sum(len(HAN.findall(s)) for s in sents) / len(sents) if sents else 0.0,
        "avg_paragraph_len": sum(len(HAN.findall(p)) for p in paras) / len(paras) if paras else 0.0,
        "annotation_per_kchar": len(ch.annotations) / kchars,
        "figures_per_section": len(ch.images) / secs,
        "code_block_lines": (sum(len(b) for b in ch.code_blocks) / len(ch.code_blocks)
                             if ch.code_blocks else 0.0),
    }


def _fingerprint(ch: Chapter, repo: Repo) -> list[Finding]:
    """S20：本章指标落在指纹带宽外就提示，说明文风漂移。

    未校准（calibrated_at 为空）只给 info，校准后给 warn——
    避免刚立项的书被 genre 默认值刷屏。
    """
    fp = (repo.ledger or {}).get("style") or {}
    metrics = (fp.get("metrics") or {})
    if not metrics:
        return []
    calibrated = bool(fp.get("calibrated_at"))
    cur = chapter_metrics(ch)
    out: list[Finding] = []
    drift: list[str] = []
    for key, spec in metrics.items():
        if not isinstance(spec, dict) or key not in cur:
            continue
        mean, band = spec.get("mean"), spec.get("band")
        if mean is None or band is None:
            continue
        if abs(cur[key] - float(mean)) > float(band):
            drift.append(f"{key} {cur[key]:.1f}（基准 {mean}±{band}）")
    if drift:
        # 单项偏离常见于"这章本来图少/代码少"，属正常起伏；
        # 两项以上同时偏，才是文风真的跑偏。所以只在 ≥2 项时升为 warn。
        level = "warn" if (calibrated and len(drift) >= 2) else "info"
        out.append(Finding(level, "structure", "S20", ch.name,
                           f"文风偏离指纹：{'；'.join(drift)}",
                           "对齐基准章，或确认本章有意变化后重新校准"))
    return out


# ---------------------------------------------------------------- 结构组

def gate_structure(ch: Chapter, repo: Repo) -> list[Finding]:
    out: list[Finding] = []
    d = repo.cfg["defaults"]
    core = repo.core
    plan = repo.plan(ch.name)

    target = plan.get("target_words") or d.get("words_per_chapter", (0, 0))[0]
    lo_ratio = 0.75

    # S01 汉字数
    if target:
        need = int(target * lo_ratio)
        if ch.han_count < need:
            out.append(Finding("error", "structure", "S01", ch.name,
                               f"汉字数 {ch.han_count} < {need}（target {target} × 0.75）",
                               "补实质内容，不要靠拆句凑数"))

    # S02 骨架顺序与齐全
    skel = repo.cfg["skeleton"]
    matched: list[tuple[str, int]] = []
    matched_sec: dict[str, Section] = {}
    cursor = 0
    for item in skel:
        detect = item.get("detect")
        if detect == "keys":
            keys = item.get("keys", [])
            head = " ".join(ch.quotes[:8])
            missing = [k for k in keys if k not in head]
            if missing:
                out.append(Finding("error", "structure", "S02", ch.name,
                                   f"头块缺少字段：{'、'.join(missing)}",
                                   f"头块需为引用块并含 {' / '.join(keys)}"))
            else:
                matched.append((item["id"], 0))
            # S13 头块字段长度上限（如 interview 一句话答案 ≤30 字）
            for k, lim in (item.get("max_chars") or {}).items():
                mm = re.search(re.escape(k) + r"[：:]\s*(.+)", head)
                if mm and len(mm.group(1).strip()) > lim:
                    out.append(Finding("error", "structure", "S13", ch.name,
                                       f"头块「{k}」{len(mm.group(1).strip())} 字 > {lim}",
                                       "压缩到规定长度"))
        elif detect == "heading":
            aliases = [_norm(a) for a in item.get("aliases", [])]
            found = None
            for idx in range(cursor, len(ch.h2)):
                if _norm(ch.h2[idx].title) in aliases:
                    found = ch.h2[idx]
                    matched.append((item["id"], ch.h2[idx].line))
                    matched_sec[item["id"]] = found
                    cursor = idx + 1
                    break
            if not found:
                out.append(Finding("error", "structure", "S02", ch.name,
                                   f"缺少骨架段「{item['id']}」",
                                   f"用其一作为 H2：{' / '.join(item.get('aliases', []))}"))
                matched.append((item["id"], -1))
        elif detect == "h3_range":
            matched.append((item["id"], -2))

    # S03 乱序检测
    lines_seq = [ln for _, ln in matched if ln >= 0]
    if lines_seq != sorted(lines_seq):
        out.append(Finding("error", "structure", "S03", ch.name,
                           "骨架段顺序与声明不一致", "按 genre 定义的顺序排列 H2"))

    # S16 未知骨架段：H2 只接受命中别名表的段（SPEC §12）
    known = {id(s) for s in matched_sec.values()}
    for s in ch.h2:
        if id(s) not in known:
            out.append(Finding("error", "structure", "S16", ch.name,
                               f"未知骨架段 H2「{s.title}」",
                               "H2 必须命中 genre 别名表；正文小节一律用 H3，不要套 ## 正文"))

    # S04 小节数范围 + S13 require_triad
    for i, (sid, flag) in enumerate(matched):
        if flag != -2:
            continue
        prev_ln = max([ln for _, ln in matched[:i] if ln >= 0], default=-1)
        nxt_ln = min([ln for _, ln in matched[i + 1:] if ln >= 0], default=len(ch.lines))
        item = next(s for s in skel if s["id"] == sid)
        lo, hi = item.get("min", 0), item.get("max", 99)
        cnt = sum(1 for s in ch.h3 if prev_ln < s.line < nxt_ln)
        if not (lo <= cnt <= hi):
            out.append(Finding("error", "structure", "S04", ch.name,
                               f"小节数 {cnt} 不在 [{lo},{hi}]", "调整节结构，或修章纲"))
        triad = item.get("require_triad")
        if triad:
            for s in ch.h3:
                if prev_ln < s.line < nxt_ln:
                    t = "\n".join(s.body)
                    miss = [kw for kw in triad if kw not in t]
                    if miss:
                        out.append(Finding("error", "structure", "S13", ch.name,
                                           f"小节「{s.title}」缺决策结构：{'、'.join(miss)}",
                                           "每节按 决策 → 实施 → 验证 组织"))

    # S13 段级增强约束（genre yaml 已声明，此前未消费）
    for item in skel:
        sec = matched_sec.get(item["id"])
        if sec is None:
            continue
        bl = sec.body
        text = "\n".join(bl)
        ml = item.get("max_lines")
        if ml is not None:
            content = [ln for ln in bl if ln.strip()]
            if len(content) > ml:
                out.append(Finding("error", "structure", "S13", ch.name,
                                   f"「{item['id']}」{len(content)} 行 > {ml}", "压缩到规定行数"))
        cr = item.get("count_range")
        if cr:
            n = _count_entries(bl)
            if not (cr[0] <= n <= cr[1]):
                out.append(Finding("error", "structure", "S13", ch.name,
                                   f"「{item['id']}」条目 {n} 不在 [{cr[0]},{cr[1]}]", "增减条目"))
        mi = item.get("max_items")
        if mi is not None and _count_entries(bl) > mi:
            out.append(Finding("error", "structure", "S13", ch.name,
                               f"「{item['id']}」条目超过 {mi}", "精简条目"))
        if item.get("require_table") and not any(ln.strip().startswith("|") for ln in bl):
            out.append(Finding("error", "structure", "S13", ch.name,
                               f"「{item['id']}」缺少表格", "补一张表"))
        rc = item.get("require_columns")
        if rc:
            header = next((ln for ln in bl if ln.strip().startswith("|")), "")
            miss = [c for c in rc if c not in header]
            if miss:
                out.append(Finding("error", "structure", "S13", ch.name,
                                   f"「{item['id']}」表头缺列：{'、'.join(miss)}", "补齐列"))
        rp = item.get("require_parts")
        if rp:
            miss = [p for p in rp if p not in text]
            if miss:
                out.append(Finding("error", "structure", "S13", ch.name,
                                   f"「{item['id']}」缺段落：{'、'.join(miss)}", "补齐结构"))
        rl = item.get("require_levels")
        if rl:
            miss = [lv for lv in rl if lv not in text]
            if miss:
                out.append(Finding("error", "structure", "S13", ch.name,
                                   f"「{item['id']}」缺档位：{'、'.join(miss)}", "补齐分层"))
        if item.get("require_scoring") and not re.search(r"评分|档|得分", text):
            out.append(Finding("error", "structure", "S13", ch.name,
                               f"「{item['id']}」缺评分标准", "给三档评分标准"))

    # S05 每节至少 1 图或表或代码
    for sec in ch.h3:
        body = "\n".join(sec.body)
        if not (re.search(r"!\[", body) or "|" in body or "```" in body):
            out.append(Finding("warn", "structure", "S05", ch.name,
                               f"小节「{sec.title}」通篇散文，没有图/表/代码", "补一张图、表或一段代码"))

    # S06 章首导图
    mind_aliases = {_norm(a) for it in skel if it.get("id") in ("mindmap", "map", "overview")
                    for a in it.get("aliases", [])}
    mind = next((s for s in ch.h2 if _norm(s.title) in mind_aliases), None)
    if mind and not any(re.search(r"!\[", ln) for ln in mind.body):
        out.append(Finding("error", "structure", "S06", ch.name,
                           "章首导图段没有图片", "插入渲染产物"))

    # S07 / S08 标注
    allowed = set(repo.cfg["annotations"])
    bad = sorted({a for a in ch.annotations if a not in allowed})
    if bad:
        out.append(Finding("error", "structure", "S07", ch.name,
                           f"非白名单标注：{'、'.join('【' + b + '】' for b in bad)}",
                           f"允许：{' '.join(sorted(allowed))}"))
    cap_sec = core.get("annotation", {}).get("max_per_section", 2)
    cap_ch = core.get("annotation", {}).get("max_per_chapter", 8)
    if len(ch.annotations) > cap_ch:
        out.append(Finding("warn", "structure", "S08", ch.name,
                           f"标注 {len(ch.annotations)} 处 > {cap_ch}", "合并或删减"))
    for sec in ch.h3:
        per = sum(1 for ln in sec.body for a in ANNOT.findall(ln) if a in allowed)
        if per > cap_sec:
            out.append(Finding("warn", "structure", "S08", ch.name,
                               f"小节「{sec.title}」标注 {per} 处 > {cap_sec}", "每节 ≤2 处"))

    # S09 禁用词（含 _core.yaml 的 person.forbidden：大家/笔者/本文…）
    # 「只要……就」这类带省略号的短语按字面永远匹配不上，转成正则
    banned = list(core.get("banned_words", [])) + list(core.get("banned_phrases", []))
    banned += list(core.get("person", {}).get("forbidden", []))
    hits: list[str] = []
    for w in banned:
        if "…" in w:
            pat = "[^。！？]{0,12}".join(re.escape(seg) for seg in re.split(r"…+", w))
            if re.search(pat, ch.prose):
                hits.append(w)
        elif w in ch.prose:
            hits.append(w)
    if hits:
        out.append(Finding("error", "structure", "S09", ch.name,
                           f"禁用表达：{'、'.join(sorted(set(hits)))}", "换成具体陈述"))

    # S17 半成品标记（_core.yaml anti_pattern_keywords；跳过单字「略」以免误伤「策略/忽略」）
    leftovers = sorted({w for w in core.get("anti_pattern_keywords", [])
                        if len(w) > 1 and w in ch.prose})
    if leftovers:
        out.append(Finding("error", "structure", "S17", ch.name,
                           f"半成品标记：{'、'.join(leftovers)}", "补完内容或删掉占位"))

    # S18 规定人称（person.required，缺省「你」）
    req = core.get("person", {}).get("required", [])
    if req and not any(w in ch.prose for w in req):
        out.append(Finding("warn", "structure", "S18", ch.name,
                           f"未出现规定人称 {'/'.join(req)}", "用第二人称称呼读者"))

    # S10 句长 / S11 段长
    typo = core.get("typography", {})
    sents = [s for s in re.split(r"[。！？；]", ch.prose) if len(HAN.findall(s)) >= 3]
    if sents:
        over = [s for s in sents if len(HAN.findall(s)) > typo.get("max_sentence_chars", 40)]
        if len(over) > len(sents) * 0.15:
            out.append(Finding("warn", "structure", "S10", ch.name,
                               f"超长句 {len(over)}/{len(sents)}", "单句 ≤40 字"))
    paras = [p for p in re.split(r"\n\s*\n", ch.prose) if p.strip()]
    if paras:
        limit = typo.get("hard_max_paragraph_chars", 160)
        over = [p for p in paras if len(HAN.findall(p)) > limit]
        if len(over) > len(paras) * 0.2:
            out.append(Finding("warn", "structure", "S11", ch.name,
                               f"超长段 {len(over)}/{len(paras)}", "拆段，一段一个意思"))

    # S21 连续超限段（_core.yaml typography.max_paragraph_chars + consecutive_over_limit）
    soft = typo.get("max_paragraph_chars")
    run_cap = typo.get("consecutive_over_limit")
    if soft and run_cap and paras:
        run, worst = 0, 0
        for p in paras:
            if len(HAN.findall(p)) > soft:
                run += 1
                worst = max(worst, run)
            else:
                run = 0
        if worst > int(run_cap):
            out.append(Finding("warn", "structure", "S21", ch.name,
                               f"连续 {worst} 段超过 {soft} 字（容忍 {run_cap}）",
                               "中间插短段落换气，别让读者一直啃长段"))

    # S22 标注必须就地（_core.yaml annotation.must_be_inline）
    # 只抓「成堆堆在末尾」：章末 15% 内 ≥3 处，且占全章一半以上
    if core.get("annotation", {}).get("must_be_inline") and len(ch.annotations) >= 3:
        lines_total = max(len(ch.lines), 1)
        tail = [ln for ln in ch.lines[int(lines_total * 0.85):] if ANNOT.match(ln.strip())]
        if len(tail) >= 3 and len(tail) * 2 >= len(ch.annotations):
            out.append(Finding("warn", "structure", "S22", ch.name,
                               f"{len(tail)}/{len(ch.annotations)} 处标注堆在章末",
                               "标注要跟所修饰的段落在一起，不要集中放末尾"))

    # S20 文风指纹比对（SPEC §7.2）：与 .book/style-fingerprint.json 的带宽比较
    out.extend(_fingerprint(ch, repo))

    # S12 信息密度
    dens_min = d.get("info_density_min")
    if dens_min and ch.han_count:
        units = _count_actionable(ch)
        density = units / ch.han_count * 1000
        if density < dens_min:
            out.append(Finding("error", "structure", "S12", ch.name,
                               f"信息密度 {density:.2f} < {dens_min}（每千字可操作单元）",
                               "补步骤/表/图/代码/练习，不要注水"))

    # S14 difficulty 与章纲一致
    if ch.fm.get("difficulty") is not None and plan.get("difficulty") is not None:
        try:
            if int(ch.fm["difficulty"]) != int(plan["difficulty"]):
                out.append(Finding("error", "structure", "S14", ch.name,
                                   f"正文 difficulty {ch.fm['difficulty']} ≠ 章纲 {plan['difficulty']}",
                                   "以章纲为准统一"))
        except (TypeError, ValueError):
            pass

    # S15 阅读路径标注（SPEC §16.5）
    marks = [m.group(1) for ln in ch.lines for m in [PATH_MARK.match(ln)] if m]
    if ch.h3 and not marks:
        out.append(Finding("warn", "structure", "S15", ch.name,
                           "小节缺少 > 路径：必读/选读/参考 标注", "每节 H3 后第一行标注"))
    elif marks:
        ratio = marks.count("必读") / max(len(ch.h3), 1)
        if not (0.5 <= ratio <= 0.8):
            out.append(Finding("warn", "structure", "S15", ch.name,
                               f"必读占比 {ratio:.0%} 不在 [0.5, 0.8]", "调整选读/参考配比"))

    return out


# ---------------------------------------------------------------- 引用组

def gate_reference(ch: Chapter, repo: Repo) -> list[Finding]:
    out: list[Finding] = []
    plan = repo.plan(ch.name)
    this_no = int(re.sub(r"\D", "", ch.name) or 0)

    # R01 图产物存在
    for img in ch.images:
        if img.startswith(("http://", "https://")):
            continue
        p = (ch.path.parent / img).resolve()
        if not p.exists():
            out.append(Finding("error", "reference", "R01", ch.name,
                               f"图不存在：{img}", "先渲染 figures/ 再检查"))

    # R02 src 路径存在
    seen = set()
    for m in SRC_REF.finditer(ch.countable + "\n" + "\n".join(ch.quotes)):
        ref = m.group(0).rstrip(".,)")
        if ref in seen:
            continue
        seen.add(ref)
        if not (repo.root / ref).exists():
            out.append(Finding("error", "reference", "R02", ch.name,
                               f"代码路径不存在：{ref}", "补齐 src/ 或改引用"))

    # R03 无前向 requires
    for r in plan.get("requires", []) or []:
        try:
            n = int(str(r))
        except ValueError:
            continue
        if n > this_no:
            out.append(Finding("error", "reference", "R03", ch.name,
                               f"requires 指向更大的章：{r}", "改成 references，或调整章序"))

    # R04 交叉引用只到章级
    bad = BAD_XREF_1.findall(ch.prose) + BAD_XREF_2.findall(ch.prose)
    if bad:
        out.append(Finding("error", "reference", "R04", ch.name,
                           f"越级交叉引用：{'、'.join(bad[:3])}", "只写 ChNN"))

    # R05 / R06 声明与使用一致
    declared = {str(x) for x in (plan.get("requires", []) or []) +
                (plan.get("references", []) or [])}
    haystack = ch.prose + "\n" + "\n".join(ch.quotes)
    used = {m.group(1) for m in CH_REF.finditer(haystack)}
    unused = declared - used
    undeclared = {u for u in used - declared if u != f"{this_no:02d}"}
    if unused:
        out.append(Finding("warn", "reference", "R05", ch.name,
                           f"声明了但没引用：{'、'.join(sorted(unused))}", "删声明或补引用"))
    if undeclared:
        out.append(Finding("error", "reference", "R06", ch.name,
                           f"引用了未声明的章：{'、'.join('Ch' + u for u in sorted(undeclared))}",
                           "在章纲 front-matter 补 requires/references"))
    out.extend(_figure_license(ch, repo))
    return out


# ---------------------------------------------------------------- 代码组

def gate_code(ch: Chapter, repo: Repo) -> list[Finding]:
    out: list[Finding] = []
    d = repo.cfg["defaults"]
    max_lines = d.get("code_block_max_lines", 30)

    # C01 代码块行数
    for b in ch.code_blocks:
        n = len([x for x in b if x.strip()])
        if n > max_lines:
            out.append(Finding("error", "code", "C01", ch.name,
                               f"代码块 {n} 行 > {max_lines}", "拆块或移到 src/ 只引用路径"))

    # C02 密钥扫描（占位符不算）
    for b in ch.code_blocks:
        for ln in b:
            if SECRET.search(ln) and not SECRET_PLACEHOLDER.search(ln):
                out.append(Finding("error", "code", "C02", ch.name,
                                   "代码块疑似硬编码密钥", "改用占位符或环境变量"))
                break

    # C03 README 运行命令（仅当该章存在 src/chNN/ 时检查）
    src_ch = repo.root / "src" / ch.name
    if src_ch.is_dir():
        readme = src_ch / "README.md"
        if not readme.exists():
            out.append(Finding("error", "code", "C03", ch.name,
                               f"{src_ch.name}/README.md 缺失", "写明运行命令与实测输出"))
        elif not re.search(r"python|运行|命令|uv |pip ", readme.read_text(encoding="utf-8", errors="ignore")):
            out.append(Finding("warn", "code", "C03", ch.name,
                               "README 未给出运行命令", "补三条命令跑起来"))
    out.extend(_version_lock(ch, repo))
    return out


# ---------------------------------------------------------------- 事实组

def gate_facts(ch: Chapter, repo: Repo) -> list[Finding]:
    out: list[Finding] = []
    led = repo.ledger
    if not led["exists"]:
        return out
    tol = repo.cfg["tolerance"]
    aw = repo.cfg["assertion_words"]
    claims = led["claims"]

    # F01 断言数字登记：SPEC §8.1 ② 是「或」——带单位 **或** 与断言词同段，都产生登记义务。
    # 旧实现要求两个条件同时成立，且每段 break 只报第一个，等于两条豁免通道。
    reported: set[str] = set()
    for para in re.split(r"\n\s*\n", ch.countable):
        if not para.strip():
            continue
        probe = STRUCT_NUM.sub(" ", para)            # 去掉章号/图号/年份等结构数字
        norm, cn_hits = _cn2num(probe)               # 汉字数字归一化
        has_assert = any(w in para for w in aw)

        cands: list[tuple[str, str, float, str]] = []   # (显示文本, 数值文本, 数值, 单位)
        for m in NUM_UNIT.finditer(norm):
            raw = m.group(0).strip()
            numtxt = re.match(r"\d+(?:\.\d+)?", raw).group(0)
            unit = raw[len(numtxt):].strip()
            cands.append((raw, numtxt, float(numtxt), unit))
        for v, unit in cn_hits:
            numtxt = f"{v:g}"
            if not any(abs(v - c[2]) <= max(abs(v) * tol, 1e-9) for c in cands):
                cands.append((f"汉字数字 {numtxt}", numtxt, v, unit))
        if has_assert:                                # 同段有断言词：裸统计数字也要登记
            for m in BARE_STAT.finditer(norm):
                numtxt = m.group(0)
                v = float(numtxt)
                if not any(abs(v - c[2]) <= max(abs(v) * tol, 1e-9) for c in cands):
                    cands.append((numtxt, numtxt, v, ""))

        for raw, numtxt, v, unit in cands:
            if not _val_claimed(claims, numtxt, tol, unit):
                key = numtxt
                if key in reported:
                    continue
                reported.add(key)
                out.append(Finding("error", "facts", "F01", ch.name,
                                   f"断言数字 {raw} 未在 claims.jsonl 登记",
                                   "补登 value/source/date，或去掉无出处的数字"))

    # F02 本章 claim 必须有 source + date
    for c in claims:
        if c.get("chapter") == ch.name and (not c.get("source") or not c.get("date")):
            out.append(Finding("error", "facts", "F02", ch.name,
                               f"claim {c.get('id', '?')} 缺 source/date", "补齐出处与日期"))

    # F03 claim 的 source 若写了路径，文件必须存在（防"出处"是编的）
    for c in claims:
        src = str(c.get("source") or "")
        m = re.search(r"[\w./\\-]+\.(?:py|json|jsonl|csv|md|log|txt)", src)
        if not m:
            continue
        cand = repo.root / m.group(0)
        if not cand.exists():
            out.append(Finding("warn", "facts", "F03", c.get("chapter", "-"),
                               f"claim {c.get('id', '?')} 的 source 路径不存在：{m.group(0)}",
                               "改成真实路径，或写清这是外部来源"))
    return out


# ---------------------------------------------------------------- 一致性组

def gate_consistency(ch: Chapter, repo: Repo) -> list[Finding]:
    out: list[Finding] = []
    led = repo.ledger
    if not led["exists"]:
        return out
    zs = {t.get("zh") for t in led["glossary"] if isinstance(t, dict)}

    # X01 首现格式术语未登记（zh 与别名都算已登记：半角括号、纯缩写都放行）
    alias_all: set[str] = set()
    for t in led["glossary"]:
        if not isinstance(t, dict):
            continue
        alias_all.add(str(t.get("zh") or ""))
        alias_all |= {str(a) for a in t.get("aliases", []) or []}
    for m in re.finditer(r"([\u4e00-\u9fff]{2,8})\s*[（(]\s*([A-Za-z][A-Za-z \-]{2,40})",
                         ch.countable):
        if m.group(1) not in zs and m.group(1) not in alias_all:
            out.append(Finding("error", "consistency", "X01", ch.name,
                               f"术语「{m.group(1)}」首现但未登记 glossary", "登记或去掉英文全称格式"))

    # X02 承诺登记：触发词，或「下一章」骨架段里的前向引用。
    # 旧实现只看触发词，而「下一章」段的写法是「Ch05 补一条字面检索通道」，
    # 一个触发词都不含——于是整章最明确的一条承诺永远不入账，账本长期为空。
    hits = [t for t in PROMISE_TRIGGERS if t in ch.countable]
    next_aliases = {_norm(a) for it in repo.cfg["skeleton"]
                    if it.get("id") == "next" for a in it.get("aliases", []) or []}
    pending: list[str] = []
    for sec in ch.h2:
        if _norm(sec.title) not in next_aliases:
            continue
        body = " ".join(sec.body)
        # 只认向前指的 ChNN：大于本章号
        for m in re.finditer(r"Ch(\d{2})", body):
            if int(m.group(1)) > int(re.sub(r"\D", "", ch.name) or 0):
                pending.append(m.group(0))
    if (hits or pending):
        opened = [p for p in led["promises"] if p.get("opened_in") == ch.name]
        need = len(dict.fromkeys(pending)) or 1
        if len(opened) < need:
            what = "、".join(dict.fromkeys(pending)) or "、".join(hits)
            out.append(Finding("error", "consistency", "X02", ch.name,
                               f"承诺未入账：{what}（需 {need} 条，实有 {len(opened)} 条）",
                               "在 promises.jsonl 登记 opened_in=本章 的条目"))
    return out


# ---------------------------------------------------------------- 全书级闸门

def gate_book_level(repo: Repo, chapters: list[Chapter]) -> list[Finding]:
    out: list[Finding] = []
    led = repo.ledger

    # R07 import 图 ⊆ 章依赖图
    src = repo.root / "src"
    if src.is_dir():
        for chdir in sorted(src.glob("ch*")):
            if not chdir.is_dir():
                continue
            owner = chdir.name.replace("ch", "")
            reqs = {str(x).zfill(2) for x in (repo.plan("ch" + owner).get("requires") or [])}
            for py in chdir.rglob("*.py"):
                txt = py.read_text(encoding="utf-8", errors="ignore")
                for mm in set(re.findall(r"\bch(\d{2})\b", txt)):
                    if mm != owner and mm not in reqs:
                        out.append(Finding("error", "reference", "R07", "ch" + owner,
                                           f"{py.name} import 了 ch{mm} 但未声明 requires",
                                           "补 requires，或把公共代码抽到 src/common/"))

    # X03 ladder 单调递增
    prev = None
    for e in led["ladder"]:
        after = set(e.get("after", []) or [])
        if prev is not None and not prev.issubset(after):
            out.append(Finding("error", "consistency", "X03", e.get("chapter", "?"),
                               "能力阶梯 after 未包含上一章 after", "能力不倒退，补齐 after"))
        prev = after

    # X04 跨章重复（warn，不阻断）
    # 旧实现数「共享 5-gram 的个数」，会把「这一节解决…」「按这个顺序」这类套话碎片
    # 累积成告警，却对真正的整段复制不敏感（复制一段 200 字，共享 5-gram 也就一百来个）。
    # 改成量「最长连续重复」：连续 20 字以上才可能是复制。
    # 刻意复用请写 `> 复用 Ch03 案例` 声明，闸门据此豁免这一对。
    declared_reuse: set[tuple[str, str]] = set()
    for ch in chapters:
        for m in re.finditer(r"复用\s*Ch(\d{2})", ch.prose + "\n" + "\n".join(ch.quotes)):
            declared_reuse.add((ch.name, f"ch{m.group(1)}"))
            declared_reuse.add((f"ch{m.group(1)}", ch.name))

    KS = (20, 30, 45, 60)
    grams: dict[str, dict[int, set[str]]] = {}
    for ch in chapters:
        s = "".join(HAN.findall(ch.prose))
        grams[ch.name] = {k: {s[i:i + k] for i in range(len(s) - k + 1)}
                          for k in KS if len(s) >= k}

    seen: dict[str, set[str]] = {}
    for ch in chapters:
        for other, ogr in seen.items():
            if (ch.name, other) in declared_reuse:
                continue
            longest = 0
            for k in reversed(KS):
                if grams[ch.name].get(k, set()) & ogr.get(k, set()):
                    longest = k
                    break
            if longest >= 20:
                out.append(Finding("warn", "consistency", "X04", ch.name,
                                   f"与 {other} 有 ≥{longest} 字的连续重复",
                                   "改写这段；确实要复用就写 `> 复用 ChNN 案例`"))
        seen[ch.name] = {k: v for k, v in grams[ch.name].items()}

    # X07 别名上限（_core.yaml glossary.max_aliases）：别名太多说明概念没收敛
    cap_alias = repo.core.get("glossary", {}).get("max_aliases")
    if cap_alias:
        for t in led["glossary"]:
            if not isinstance(t, dict):
                continue
            n = len(t.get("aliases", []) or [])
            if n > int(cap_alias):
                out.append(Finding("warn", "consistency", "X07", "-",
                                   f"术语「{t.get('zh')}」有 {n} 个别名 > {cap_alias}",
                                   "统一叫法，别名只留读者会用到的"))

    # X08 同一别名挂在两个术语上（glossary.forbid_synonym_swap）
    if repo.core.get("glossary", {}).get("forbid_synonym_swap"):
        owner: dict[str, str] = {}
        for t in led["glossary"]:
            if not isinstance(t, dict):
                continue
            for name in [str(t.get("zh") or "")] + [str(a) for a in t.get("aliases", []) or []]:
                if not name:
                    continue
                if name in owner and owner[name] != str(t.get("id")):
                    out.append(Finding("error", "consistency", "X08", "-",
                                       f"「{name}」同时指向 {owner[name]} 与 {t.get('id')}",
                                       "合并术语，或改掉重名别名"))
                owner[name] = str(t.get("id"))

    # X05 同一术语 id 多种定义
    by_id: dict[str, set[str]] = {}
    for t in led["glossary"]:
        if isinstance(t, dict) and t.get("id") and t.get("def"):
            by_id.setdefault(t["id"], set()).add(t["def"])
    for tid, defs in by_id.items():
        if len(defs) > 1:
            out.append(Finding("error", "consistency", "X05", "-",
                               f"术语 {tid} 有 {len(defs)} 种定义", "合并为权威定义"))

    # X06 promises open 阻断装配
    opens = [p for p in led["promises"] if p.get("status") == "open"]
    if opens:
        out.append(Finding("error", "consistency", "X06", "-",
                           f"承诺账本仍有 {len(opens)} 条 open，阻断装配",
                           "结清或标记 dropped 并写 reason"))

    out.extend(_capstone_snapshots(repo))
    out.extend(_data_repro(repo))
    out.extend(_difficulty_curve(repo))
    out.extend(_contracts(repo))
    out.extend(_preface(repo))
    out.extend(_param_overrides(repo))
    out.extend(_lock_missing(repo))
    return out


def _lock_missing(repo: Repo) -> list[Finding]:
    """C04：有章级代码却没有 versions.lock，版本锁校验会整段跳过。"""
    src = repo.root / "src"
    if not src.is_dir():
        return []
    if not any(re.fullmatch(r"ch\d{2}", p.name) for p in src.iterdir() if p.is_dir()):
        return []
    if (repo.root / "versions.lock").exists():
        return []
    return [Finding("warn", "code", "C04", "-",
                    "有 src/chNN/ 但没有 versions.lock，版本锁校验已跳过",
                    "跑 assemble.py 生成，或手写依赖与版本")]


def _contracts(repo: Repo) -> list[Finding]:
    """C06：.book/contracts/*.json 按 schemas/contract.schema.json 校验。

    这三份 schema 此前只是文档，没有任何消费者；写手产出的合同可以随便长什么样。
    """
    cdir = repo.root / ".book" / "contracts"
    if not cdir.is_dir():
        return []
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import schema_check
    except ImportError:
        return []
    out: list[Finding] = []
    for p in sorted(cdir.glob("*.json")):
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            out.append(Finding("error", "code", "C06", p.stem,
                               f"合同不是合法 JSON：{e}", "修好或用 dep_brief 重新生成"))
            continue
        problems, status = schema_check.validate("contract", payload)
        if status == "unavailable":
            out.append(Finding("info", "code", "C06", "-",
                               "未安装 jsonschema，合同契约校验已跳过",
                               "pip install jsonschema"))
            break
        if problems:
            out.append(Finding("error", "code", "C06", p.stem,
                               f"合同不符契约：{problems[0]}", "按 contract.schema.json 补齐字段"))
    return out


def _preface(repo: Repo) -> list[Finding]:
    """P01–P05：前言必须含的五项（references/07-assembly.md §前言）。

    文档写着「闸门会查」，但此前 check.py 从不读 final/ 与前言的任何文件。
    """
    cand = [repo.root / "final" / "00-preface.md", repo.root / "00-preface.md"]
    p = next((x for x in cand if x.exists()), None)
    if p is None:
        return [Finding("info", "structure", "P00", "-",
                        "没有前言（final/00-preface.md 或 00-preface.md），前言闸门已跳过",
                        "装配后重跑，或先把前言草稿放进书根")]
    txt = p.read_text(encoding="utf-8", errors="ignore")
    # 五项口径见 references/07-assembly.md「前言必须含的五项」
    need = [
        ("P01", ["给谁看", "读者画像", "目标读者"], "写明读者画像与前置知识"),
        ("P02", ["快速路径"], "三条阅读路径要齐全（快速 / 完整 / 复习）"),
        ("P03", ["不讲"], "写明本书不讲什么，与 00-positioning 的范围边界一致"),
        ("P04", ["标注"], "书里每种【】都要解释，自定义标记不解释等于噪音"),
        ("P05", ["代码"], "写明代码运行约定：命令、依赖、Mock 模式"),
    ]
    out: list[Finding] = []
    for code, kws, hint in need:
        if not any(k in txt for k in kws):
            out.append(Finding("warn", "structure", code, "-",
                               f"前言缺「{kws[0]}」", hint))
    if "快速路径" in txt:
        miss = [k for k in ("完整路径", "复习路径") if k not in txt]
        if miss:
            out.append(Finding("warn", "structure", "P02", "-",
                               f"阅读路径不全，缺 {'、'.join(miss)}", "三条路径都要给"))
    return out


def _param_overrides(repo: Repo) -> list[Finding]:
    """P11：书级参数覆盖 genre 默认值时留痕，避免「改闸门迁就内容」无人察觉。"""
    out: list[Finding] = []
    mine = (repo.book.get("limits") or {})
    default = (repo.cfg.get("genre_fingerprint_limits") or {})
    # genre yaml 里可能声明 defaults，这里以 genre 的 limits 为基准
    genre = _load_yaml(GENRE_DIR / f"{repo.cfg['main_genre']}.yaml")
    gd = (genre.get("defaults") or {})
    for k, v in mine.items():
        if k in gd and gd[k] != v:
            out.append(Finding("info", "structure", "P11", "-",
                               f"{k} 由书级覆盖为 {v}（类型默认 {gd[k]}）",
                               "确认这是有意的取舍，并在 SPEC 或 03-style-guide 写明理由"))
    return out


# ---------------------------------------------------------------- 资产级（B 组增量）

FIG_META = re.compile(r"^%%\s*(source|credit|license)\s*:\s*(.+)$", re.M)
# 标准库用解释器自己的名单，别手写——漏一个就会把 zlib 当成第三方依赖要求锁版本
_STDLIB = set(getattr(sys, "stdlib_module_names", ())) or {
    "os", "sys", "re", "json", "typing", "pathlib", "dataclasses", "collections",
    "itertools", "math", "random", "time", "datetime", "functools", "abc", "enum",
    "csv", "sqlite3", "subprocess", "hashlib", "logging", "unittest", "shutil",
    "argparse", "contextlib", "io", "textwrap", "urllib", "http", "socket", "zlib",
    "__future__",
}


def _figure_license(ch: Chapter, repo: Repo) -> list[Finding]:
    """16.6 图许可：.mmd 头部 source/credit/license。"""
    out: list[Finding] = []
    fig_dir = repo.root / "figures" / ch.name
    if not fig_dir.is_dir():
        return out
    adapted = False
    for mmd in sorted(fig_dir.glob("*.mmd")):
        head = mmd.read_text(encoding="utf-8", errors="ignore")[:2000]
        meta = {m.group(1): m.group(2).strip() for m in FIG_META.finditer(head)}
        src = meta.get("source", "")
        if src in ("adapted", "external"):
            adapted = True
            miss = [k for k in ("credit", "license") if not meta.get(k)]
            if miss:
                out.append(Finding("error", "reference", "G01", ch.name,
                                   f"{mmd.name} source={src} 缺 {'、'.join(miss)}",
                                   "补 %% credit 与 %% license"))
    if adapted:
        caps = "\n".join(q for q in ch.quotes if q.startswith("图"))
        if caps and not re.search(r"（(?:改编自|来源：)", caps):
            out.append(Finding("warn", "reference", "G02", ch.name,
                               "有 adapted/external 图，但图注未写「（改编自 …）」或「（来源：…）」",
                               "在图注末尾补来源"))
    return out


def _version_lock(ch: Chapter, repo: Repo) -> list[Finding]:
    """16.7 版本锁：import 的包主版本必须与 versions.lock 一致。"""
    out: list[Finding] = []
    lock = repo.root / "versions.lock"
    src_ch = repo.root / "src" / ch.name
    if not src_ch.is_dir() or not lock.exists():
        return out
    try:
        deps = (yaml.safe_load(lock.read_text(encoding="utf-8")) or {}).get("dependencies", {}) or {}
    except yaml.YAMLError:
        return out
    imports: set[str] = set()
    for py in src_ch.rglob("*.py"):
        txt = py.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", txt, re.M):
            imports.add(m.group(1))

    def mm(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in re.findall(r"\d+", str(v))[:2])

    for pkg in sorted(imports - _STDLIB):
        if re.fullmatch(r"ch\d{2}", pkg) or pkg in ("common", "src"):
            continue                                  # 包内互引，不是第三方依赖
        if pkg not in deps:
            out.append(Finding("warn", "code", "C04", ch.name,
                               f"import {pkg} 未在 versions.lock 锁定", "补版本号"))
            continue
        try:
            import importlib.metadata as md
            installed = md.version(pkg)
        except Exception:  # noqa: BLE001
            continue
        if mm(installed) != mm(deps[pkg]):
            out.append(Finding("error", "code", "C04", ch.name,
                               f"{pkg} 实际 {installed} 与 lock {deps[pkg]} 主版本不一致",
                               "锁版本或升级代码"))
    return out


def _capstone_snapshots(repo: Repo) -> list[Finding]:
    """16.8 capstone 里程碑快照：每 snapshot_every 章一个 git tag。"""
    out: list[Finding] = []
    if repo.book.get("spine") != "capstone":
        return out
    if not (repo.root / ".git").exists():
        # 静默跳过会让"没查"看起来像"通过"，必须显式说明
        out.append(Finding("info", "reference", "G03", "-",
                           "capstone 快照检查已跳过：书目录不是 git 仓库",
                           "git init 并打 capstone/chNN tag，或改用 snapshots/chNN/ 目录约定"))
        return out
    try:
        r = subprocess.run(["git", "-C", str(repo.root), "tag", "--list", "capstone/*"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return out
    if r.returncode != 0:
        return out
    existing = set(r.stdout.split())
    every = int(repo.book.get("limits", {}).get("snapshot_every", 5) or 5)
    for i, name in enumerate(sorted(repo.plans), 1):
        if i % every == 0 and f"capstone/{name}" not in existing:
            out.append(Finding("warn", "reference", "G03", name,
                               f"缺 capstone 快照 tag capstone/{name}",
                               "按 snapshot_every 打 tag，并保证该 tag 可运行"))
    return out


def _data_repro(repo: Repo) -> list[Finding]:
    """16.9 示例数据可复现：SEED 固定 + src/data/README。"""
    out: list[Finding] = []
    d = repo.root / "src" / "data"
    if not d.is_dir():
        return out
    if not (d / "README.md").exists():
        out.append(Finding("warn", "code", "C05", "-",
                           "src/data/README.md 缺失", "列脚本→产物→大小→用途"))
    for py in sorted(d.glob("*.py")):
        txt = py.read_text(encoding="utf-8", errors="ignore")
        if "SEED" not in txt:
            out.append(Finding("warn", "code", "C05", "-",
                               f"{py.name} 缺 SEED=42 常量", "数据必须可复现"))
        elif not re.search(r"(?:random|np\.random)\.seed\(\s*SEED\s*\)", txt):
            out.append(Finding("warn", "code", "C05", "-",
                               f"{py.name} 未调用 random.seed(SEED)", "开头固定种子"))
    return out


def _difficulty_curve(repo: Repo) -> list[Finding]:
    """16.2 难度曲线：首章 ≤2、连续高难度、跃升。"""
    out: list[Finding] = []
    names = sorted(repo.plans)
    diffs: list[int] = []
    for n in names:
        try:
            diffs.append(int(repo.plans[n].get("difficulty")))
        except (TypeError, ValueError):
            diffs.append(0)
    if diffs and diffs[0] > 2:
        out.append(Finding("error", "structure", "S19", names[0],
                           f"首章 difficulty {diffs[0]} > 2", "首章降到 ≤2"))
    maxrun = int(repo.book.get("limits", {}).get("difficulty_max_run", 3) or 3)
    run = 0
    for n, d in zip(names, diffs):
        if d >= 4:
            run += 1
            if run > maxrun:
                out.append(Finding("error", "structure", "S19", n,
                                   f"连续 {run} 章 difficulty ≥4 > {maxrun}", "插缓冲章或降难度"))
        else:
            run = 0
    for i in range(1, len(diffs)):
        if diffs[i] - diffs[i - 1] > 2:
            out.append(Finding("warn", "structure", "S19", names[i],
                               f"难度从 {diffs[i - 1]} 跃升到 {diffs[i]}", "中间插过渡章"))
    return out


GATES = {
    "structure": gate_structure,
    "reference": gate_reference,
    "code": gate_code,
    "facts": gate_facts,
    "consistency": gate_consistency,
}
DEFAULT_GATES = "structure,reference,code,facts,consistency"


# ---------------------------------------------------------------- 输出

def _suggest_promises(repo: Repo, ch_dir: Path, names: list[str]) -> int:
    """X02 报出的缺口，直接给成可粘贴的 JSONL——比让写手手写 JSON 省事且不出格式错。"""
    next_aliases = {_norm(a) for it in repo.cfg["skeleton"]
                    if it.get("id") == "next" for a in it.get("aliases", []) or []}
    opened = {p.get("opened_in") for p in repo.ledger.get("promises", [])}
    rows: list[str] = []
    for name in names:
        ch = parse_chapter(ch_dir / f"{name}.md")
        want: list[str] = []
        for sec in ch.h2:
            if _norm(sec.title) not in next_aliases:
                continue
            body = " ".join(sec.body)
            for m in re.finditer(r"Ch(\d{2})", body):
                if int(m.group(1)) > int(re.sub(r"\D", "", name) or 0):
                    want.append((f"ch{m.group(1)}", body[:100]))
        if not want or name in opened:
            continue
        for i, (target, text) in enumerate(want, 1):
            rows.append(json.dumps({
                "id": f"P-{name}-{i}", "opened_in": name, "text": text,
                "kind": "forward", "target": target, "status": "kept",
                "closed_in": target,
            }, ensure_ascii=False))
    if not rows:
        print("没有待登记的承诺。", file=sys.stderr)
        return 0
    print("\n".join(rows))
    print(f"\n↑ {len(rows)} 条草稿。status 默认 kept，若实际没兑现请改成 dropped 并写 reason。",
          file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="书稿闸门检查")
    ap.add_argument("--book", required=True, help="书项目根目录")
    ap.add_argument("--chapter", action="append", help="只查指定章，可重复")
    ap.add_argument("--gates", default=DEFAULT_GATES,
                    help=f"逗号分隔，默认 {DEFAULT_GATES}")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--quiet", action="store_true", help="只输出问题")
    ap.add_argument("--suggest", action="store_true",
                    help="按缺口生成 promises.jsonl 草稿（粘贴后请人工确认）")
    args = ap.parse_args()

    root = Path(args.book).resolve()
    if not (root / "book.yaml").exists():
        sys.exit(f"找不到 {root / 'book.yaml'}")

    repo = load_repo(root)
    gates = [g.strip() for g in args.gates.split(",") if g.strip() in GATES]
    ch_dir = root / repo.book.get("paths", {}).get("chapters", "chapters")

    names = args.chapter or sorted(p.stem for p in ch_dir.glob("ch*.md"))
    if not names:
        sys.exit(f"{ch_dir} 下没有章节文件")

    if args.suggest:
        return _suggest_promises(repo, ch_dir, names)

    results: dict[str, list[Finding]] = {}
    chapters: list[Chapter] = []
    for name in names:
        p = ch_dir / f"{name}.md"
        if not p.exists():
            sys.exit(f"找不到章节 {p}")
        ch = parse_chapter(p)
        chapters.append(ch)
        found: list[Finding] = []
        for g in gates:
            found.extend(GATES[g](ch, repo))
        results[name] = found

    book_findings: list[Finding] = []
    if not args.chapter:                       # 全书模式才跑全书级闸门
        book_findings = gate_book_level(repo, chapters)

    if not repo.ledger["exists"] and any(g in gates for g in ("facts", "consistency")):
        book_findings.append(Finding("info", "consistency", "X00", "-",
                                     "未发现 .book/ 账本，事实/一致性闸门已跳过",
                                     "先跑 init_book.py 初始化账本"))

    errs = sum(1 for v in results.values() for f in v if f.level == "error")
    warns = sum(1 for v in results.values() for f in v if f.level == "warn")
    errs += sum(1 for f in book_findings if f.level == "error")
    warns += sum(1 for f in book_findings if f.level == "warn")

    if args.json:
        print(json.dumps({
            "book": str(root),
            "genre": repo.cfg["genre_list"],
            "results": {k: [f.as_dict() for f in v] for k, v in results.items()},
            "book_level": [f.as_dict() for f in book_findings],
            "summary": {"error": errs, "warn": warns},
        }, ensure_ascii=False, indent=2))
        return 1 if errs else 0

    print(f"检查 {root}")
    print(f"  genre: {'+'.join(repo.cfg['genre_list'])}   闸门: {','.join(gates)}")
    print()
    for name, found in results.items():
        flag = "✗" if any(f.level == "error" for f in found) else ("!" if found else "✓")
        print(f"{flag} {name}")
        if not args.quiet:
            if not found:
                print("    通过")
            for f in found:
                mark = "✗" if f.level == "error" else "!"
                print(f"    {mark} [{f.code}] {f.msg}")
                if f.hint:
                    print(f"        → {f.hint}")
    if book_findings:
        print()
        print("全书级检查")
        for f in book_findings:
            mark = {"error": "✗", "warn": "!", "info": "i"}[f.level]
            # 归属章要打出来：只说「与 ch02 重叠」不说是谁，等于没法定位
            where = f"[{f.code}]" if f.chapter in ("", "-") else f"[{f.code}] {f.chapter}"
            print(f"  {mark} {where} {f.msg}")
            if f.hint:
                print(f"      → {f.hint}")
    print()
    print(f"汇总: {errs} error, {warns} warn")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
