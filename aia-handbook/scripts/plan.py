#!/usr/bin/env python3
"""plan.py —— 依赖图编译器 + G4 章纲闸门。

读 04-chapter-plans/*.md 的 front-matter，编译成 DAG，切波次，算四个质量指标。
禁止手画依赖图：图必须由声明编译得到，否则一定和正文脱节。

同时承担三件此前只写在文档里的事：
- **G4 章纲闸门**（评审 A4）：消费 genre 的 `plan_required_fields`，校章纲数、
  必填字段与类型、「与相邻章的边界」段，并接进 check.py 的 JSON 输出；
- **写作波次表**（评审 B5）：按篇/并发上限产出 .book/writing-waves.json，
  与阅读波次分开，供按篇派活；
- **capstone 项目推进曲线**（评审 A8）：SPEC §10/§11 要求产出，落 .book/project-curve.json。

用法:
    python scripts/plan.py --book ../my-book
    python scripts/plan.py --book ../my-book --json

退出码：有致命问题（成环 / 未知章号 / G4 章纲不合格）返回 1。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：python -m pip install pyyaml")

CRITICAL_PATH_MAX = 8
FANOUT_RATIO = 1 / 3
GENRE_DIR = Path(__file__).resolve().parent.parent / "genres"
BOUNDARY_H2 = re.compile(r"^##\s*与相邻章的边界\s*$", re.M)
OUTLINE_H2 = re.compile(r"^##\s*第\s*[0-9一二三四五六七八九十]+\s*篇.*$", re.M)


def read_plan(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError as e:
        print(f"! {path.name} front-matter 解析失败：{e}", file=sys.stderr)
        return {}


def _genre_docs(book: dict) -> list[dict]:
    genres = book.get("genre") or []
    if isinstance(genres, str):
        genres = [genres]
    out = []
    for g in genres:
        p = GENRE_DIR / f"{g}.yaml"
        if p.exists():
            out.append(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    return out


def _plan_required_fields(book: dict) -> list[str]:
    fields: list[str] = []
    for doc in _genre_docs(book):
        for f in doc.get("plan_required_fields", []) or []:
            if f not in fields:
                fields.append(f)
    return fields or ["chapter", "title", "requires", "references",
                      "target_words", "difficulty", "deliverable"]


def _plan_files(book_dir: Path, book: dict) -> list[Path]:
    plan_dir = book_dir / book.get("paths", {}).get("plans", "04-chapter-plans")
    return sorted(plan_dir.glob("ch*.md")) if plan_dir.is_dir() else []


# ---------------------------------------------------------------- G4 章纲闸门

def validate_plans(book_dir: Path, book: dict | None = None,
                   plans: dict | None = None) -> tuple[list[str], list[str]]:
    """返回 (阻断项, 提示项)。check.py 的 G4 与 plan.py 自身共用这一份口径。

    字段级 / 章数级问题会阻断（章纲是全局调度的输入）；边界段缺失给 warn，
    避免把「写得不够」升级成「整本书编不了图」，但仍然显式报出来。
    """
    book = book or (yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8")) or {})
    files = _plan_files(book_dir, book)
    required = _plan_required_fields(book)
    problems: list[str] = []
    warnings: list[str] = []

    n_declared = ((book.get("scale") or {}).get("chapters"))
    if n_declared is not None and len(files) != int(n_declared):
        problems.append(f"章纲数 {len(files)} ≠ book.yaml scale.chapters {n_declared}"
                        "（章纲必须一次写全，不能写一章发一章）")

    for p in files:
        text = p.read_text(encoding="utf-8")
        meta = (plans or {}).get(p.stem) or read_plan(p)
        if not meta:
            # 评审 D1：此前 `if not meta: continue` 静默漏章，调度无声少一章
            problems.append(f"{p.name} 没有合法的 front-matter，不会被编译进 DAG/state")
            continue
        missing = [f for f in required if f not in meta or meta[f] is None]
        if missing:
            problems.append(f"{p.name} front-matter 缺必填字段：{'、'.join(missing)}"
                            f"（genre 声明的 plan_required_fields）")
        type_errors: list[str] = []
        if "title" in meta and not str(meta["title"] or "").strip():
            type_errors.append("title 不能为空")
        if "deliverable" in meta and not str(meta["deliverable"] or "").strip():
            type_errors.append("deliverable 不能为空（必须是可验收的名词）")
        for k in ("requires", "references"):
            if k in meta and not isinstance(meta[k], (list, tuple)):
                type_errors.append(f"{k} 必须是数组")
        if "target_words" in meta:
            try:
                if int(meta["target_words"]) <= 0:
                    type_errors.append("target_words 必须是正整数")
            except (TypeError, ValueError):
                type_errors.append("target_words 必须是整数")
        if "difficulty" in meta:
            try:
                if not 1 <= int(meta["difficulty"]) <= 5:
                    type_errors.append("difficulty 必须在 1–5")
            except (TypeError, ValueError):
                type_errors.append("difficulty 必须是 1–5 的整数")
        if type_errors:
            problems.append(f"{p.name} 字段类型/取值不合法：{'；'.join(type_errors)}")

        m = BOUNDARY_H2.search(text)
        if not m:
            warnings.append(f"{p.name} 缺「## 与相邻章的边界」段（下游 dep-brief 会没有边界依据）")
        else:
            rest = text[m.end():]
            nxt = re.search(r"^##\s+", rest, re.M)
            body = (rest[:nxt.start()] if nxt else rest).strip()
            if len(body) < 10:
                warnings.append(f"{p.name}「与相邻章的边界」段是空的，等于没写")
    return problems, warnings


# ---------------------------------------------------------------- 调度

def load(book_dir: Path):
    book = yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8")) or {}
    nodes: dict[str, dict] = {}
    broken: list[str] = []
    for p in _plan_files(book_dir, book):
        meta = read_plan(p)
        if not meta:
            broken.append(p.name)                 # 不再静默跳过：G4 会报出来
            continue
        ch = str(meta.get("chapter") or p.stem.replace("ch", "")).zfill(2)
        nodes[f"ch{ch}"] = meta
    return book, nodes, broken


def build(nodes: dict[str, dict]):
    """返回 dag、children、问题列表。"""
    problems: list[str] = []
    dag: dict[str, set[str]] = {}
    children: dict[str, set[str]] = defaultdict(set)

    for name, meta in nodes.items():
        reqs = {f"ch{str(x).zfill(2)}" for x in (meta.get("requires") or [])}
        for r in reqs:
            if r not in nodes:
                problems.append(f"{name} 的 requires 指向不存在的章：{r}")
            elif r >= name:
                problems.append(f"{name} 的 requires 指向更大的章：{r}（前向依赖不允许）")
        dag[name] = {r for r in reqs if r in nodes and r < name}

    for n, reqs in dag.items():
        for r in reqs:
            children[r].add(n)

    # Kahn 拓扑排序
    indeg = {n: len(reqs) for n, reqs in dag.items()}
    q = deque([n for n, d in indeg.items() if d == 0])
    order: list[str] = []
    while q:
        n = q.popleft()
        order.append(n)
        for c in sorted(children[n]):
            indeg[c] -= 1
            if indeg[c] == 0:
                q.append(c)

    cyclic = sorted(set(nodes) - set(order))
    if cyclic:
        problems.append("检测到环，涉及：" + " → ".join(_cycle_chain(dag, cyclic[0])))

    # 波次：层号 = 1 + max(上游层号)
    level: dict[str, int] = {}
    for n in order:
        level[n] = 0 if not dag[n] else 1 + max(level[r] for r in dag[n])
    waves: dict[int, list[str]] = defaultdict(list)
    for n, lv in level.items():
        waves[lv].append(n)
    wave_list = [sorted(waves[i]) for i in sorted(waves)]
    return dag, children, wave_list, cyclic, problems


def _cycle_chain(dag: dict[str, set[str]], start: str, limit: int = 12) -> list[str]:
    seen: list[str] = []
    cur = start
    while cur not in seen and len(seen) < limit:
        seen.append(cur)
        nxt = sorted(dag.get(cur, ()))
        if not nxt:
            break
        cur = nxt[0]
    return seen + [cur]


def metrics(nodes, dag, children, wave_list):
    fanout = {n: len(children.get(n, ())) for n in nodes}
    top = max(fanout.items(), key=lambda kv: kv[1]) if fanout else ("-", 0)
    isolated = [n for n in nodes if not dag.get(n) and not children.get(n)]
    return {
        "chapters": len(nodes),
        "edges": sum(len(v) for v in children.values()),
        "waves": len(wave_list),
        "max_wave_width": max((len(w) for w in wave_list), default=0),
        "max_fanout": {"chapter": top[0], "count": top[1]},
        "isolated": sorted(isolated),
    }


# ---------------------------------------------------------------- 写作波次 / 项目曲线

def writing_waves(book_dir: Path, book: dict, nodes: dict[str, dict]) -> dict:
    """按篇划分写作波次（SPEC §6.1）。篇读不到就按 concurrency 顺序切组。

    与阅读波次的区别：阅读波次要求上游 done，写作波次只要求合同**草案**先行
    （见 dep_brief.py --draft）。这张表只是派活依据，不改变装配/闸门顺序。
    """
    names = sorted(nodes)
    outline = book_dir / "01-outline.md"
    groups: list[list[str]] = []
    basis = "concurrency"
    if outline.exists():
        text = outline.read_text(encoding="utf-8", errors="ignore")
        heads = list(OUTLINE_H2.finditer(text))
        for i, h in enumerate(heads):
            seg = text[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            m = re.search(r"Ch(\d{2})\s*[–—~\-]\s*Ch(\d{2})", seg)
            if not m:
                continue
            lo, hi = int(m.group(1)), int(m.group(2))
            picked = [n for n in names if lo <= int(n[2:]) <= hi]
            if picked:
                groups.append(picked)
        if groups:
            basis = "01-outline.md 的篇"
    if not groups:
        size = max(1, int(book.get("concurrency", 4) or 4))
        groups = [names[i:i + size] for i in range(0, len(names), size)]
        basis = f"concurrency={size}（无篇级大纲，按每组 {size} 章）"
    covered = [n for g in groups for n in g]
    leftover = [n for n in names if n not in covered]
    if leftover:
        groups.append(leftover)
    return {"basis": basis, "waves": groups, "note": "写作波次只用于派活；闸门与装配仍按阅读波次"}


def project_curve(book_dir: Path, book: dict, nodes: dict[str, dict]) -> dict | None:
    """capstone 项目推进曲线：逐章标注推进到哪一步（SPEC §10/§11、评审 A8）。"""
    if book.get("spine") != "capstone":
        return None
    stages = []
    for name in sorted(nodes):
        meta = nodes[name]
        stage = meta.get("project_stage")
        if stage:
            stages.append({"chapter": name, "stage": str(stage),
                           "deliverable": str(meta.get("deliverable") or "")})
    if not stages:
        return None
    return {"spine": "capstone", "stages": stages,
            "note": "来自章纲 front-matter 的 project_stage；连续 3 章不推进由 check.py S24 提示"}


def main() -> int:
    ap = argparse.ArgumentParser(description="章节依赖图编译、G4 章纲闸门与波次评估")
    ap.add_argument("--book", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.book).resolve()
    book, nodes, broken = load(root)
    if not nodes:
        sys.exit(f"{root} 下没有合法章纲（04-chapter-plans/ch*.md）")

    dag, children, wave_list, cyclic, problems = build(nodes)
    m = metrics(nodes, dag, children, wave_list)

    # 质量告警
    warns: list[str] = []
    if m["waves"] > CRITICAL_PATH_MAX:
        warns.append(f"关键路径 {m['waves']} 波 > {CRITICAL_PATH_MAX}：依赖过密，"
                     f"考虑把部分 requires 降级为 references")
    if m["chapters"] >= 6 and m["max_fanout"]["count"] > m["chapters"] * FANOUT_RATIO:
        warns.append(f"最大扇出 {m['max_fanout']['chapter']} 被 "
                     f"{m['max_fanout']['count']} 章依赖 > ⅓：建议拆章或前置")
    if m["isolated"]:
        warns.append("孤立节点（无任何边）：" + "、".join(m["isolated"]) +
                     " —— 它们可能其实是独立文章")
    concurrency = book.get("concurrency", 4)
    if m["max_wave_width"] > concurrency * 2:
        warns.append(f"最大波宽 {m['max_wave_width']} 远超并发上限 {concurrency}：目录失衡")

    # G4：章纲闸门（同一个实现也被 check.py 的 G4 调用）
    g4_problems, g4_warns = validate_plans(root, book, nodes)
    problems.extend(g4_problems)
    warns.extend(g4_warns)
    if broken:
        print(f"! {len(broken)} 份章纲没有 front-matter，已从 DAG 排除：{'、'.join(broken)}",
              file=sys.stderr)

    writing = writing_waves(root, book, nodes)
    curve = project_curve(root, book, nodes)

    # 落盘：SPEC §13 要求 .book/dag.json 与 waves.json 存在，供 state.py / assemble.py 消费
    payload = {
        "book": str(root),
        "genre": book.get("genre"),
        "nodes": {n: {"requires": sorted(dag[n]),
                      "references": nodes[n].get("references", []),
                      "target_words": nodes[n].get("target_words"),
                      "difficulty": nodes[n].get("difficulty")}
                  for n in sorted(nodes)},
        "waves": wave_list,
        "metrics": m,
        "problems": problems,
        "warnings": warns,
        "plan_gates": {"problems": g4_problems, "warnings": g4_warns},
        "writing_waves": writing,
        "project_curve": curve or {"skipped": "章纲未声明 project_stage"},
    }
    out_dir = root / ".book"
    out_dir.mkdir(parents=True, exist_ok=True)
    # 写盘前按契约自检：dag.json 有 schema 就得对得上，不能只当文档摆着
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import schema_check
        schema_problems, status = schema_check.validate("dag", payload)
        if status == "unavailable":
            print("! 未安装 jsonschema，本次未做 dag 契约校验", file=sys.stderr)
        elif schema_problems:
            print(f"! dag 与契约有 {len(schema_problems)} 处不符：{schema_problems[:3]}",
                  file=sys.stderr)
    except ImportError:
        pass
    (out_dir / "dag.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "waves.json").write_text(
        json.dumps({"waves": wave_list, "critical_path": len(wave_list)},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "writing-waves.json").write_text(
        json.dumps(writing, ensure_ascii=False, indent=2), encoding="utf-8")
    if curve:
        (out_dir / "project-curve.json").write_text(
            json.dumps(curve, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        (out_dir / "project-curve.json").unlink(missing_ok=True)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if problems else 0

    print(f"依赖图 {root}")
    print(f"  节点 {m['chapters']}  边 {m['edges']}  "
          f"{'无环' if not cyclic else '成环 ✗'}")
    print(f"  关键路径 {m['waves']} 波  最大波宽 {m['max_wave_width']}  "
          f"最大扇出 {m['max_fanout']['count']} ({m['max_fanout']['chapter']})")
    print(f"  孤立节点 {'无' if not m['isolated'] else '、'.join(m['isolated'])}")
    print()
    print("阅读波次（闸门 / 装配顺序）")
    for i, w in enumerate(wave_list, 1):
        print(f"  {i}: {' '.join(w)}")
    print()
    print(f"写作波次（派活依据：{writing['basis']}）")
    for i, w in enumerate(writing["waves"], 1):
        print(f"  {i}: {' '.join(w)}")
    print()
    print(f"G4 章纲闸门：{len(g4_problems)} 处阻断 / {len(g4_warns)} 处提示")
    if curve:
        print(f"capstone 项目推进曲线：{len(curve['stages'])} 章已声明 project_stage"
              " → .book/project-curve.json")
    elif book.get("spine") == "capstone":
        print("capstone 项目推进曲线：章纲未声明 project_stage，已跳过（不冒充通过）")
    if problems:
        print()
        for p in problems:
            print(f"  ✗ {p}")
    if warns:
        print()
        for w in warns:
            print(f"  ! {w}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
