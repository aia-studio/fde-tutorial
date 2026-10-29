#!/usr/bin/env python3
"""plan.py —— 依赖图编译器。

读 04-chapter-plans/*.md 的 front-matter，编译成 DAG，切波次，算四个质量指标。
禁止手画依赖图：图必须由声明编译得到，否则一定和正文脱节。

用法:
    python scripts/plan.py --book ../my-book
    python scripts/plan.py --book ../my-book --json

退出码：有致命问题（成环 / 未知章号）返回 1。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：python -m pip install pyyaml")

CRITICAL_PATH_MAX = 8
FANOUT_RATIO = 1 / 3


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


def load(book_dir: Path):
    book = yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8")) or {}
    plan_dir = book_dir / book.get("paths", {}).get("plans", "04-chapter-plans")
    nodes: dict[str, dict] = {}
    if plan_dir.is_dir():
        for p in sorted(plan_dir.glob("ch*.md")):
            meta = read_plan(p)
            if not meta:
                continue
            ch = str(meta.get("chapter") or p.stem.replace("ch", "")).zfill(2)
            nodes[f"ch{ch}"] = meta
    return book, nodes


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
    # 孤立 = 既没有上游 requires，也没有下游引用
    isolated = [n for n in nodes if not dag.get(n) and not children.get(n)]
    return {
        "chapters": len(nodes),
        "edges": sum(len(v) for v in children.values()),
        "waves": len(wave_list),
        "max_wave_width": max((len(w) for w in wave_list), default=0),
        "max_fanout": {"chapter": top[0], "count": top[1]},
        "isolated": sorted(isolated),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="章节依赖图编译与质量评估")
    ap.add_argument("--book", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.book).resolve()
    book, nodes = load(root)
    if not nodes:
        sys.exit(f"{root} 下没有章纲（04-chapter-plans/ch*.md）")

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
    }
    out_dir = root / ".book"
    out_dir.mkdir(parents=True, exist_ok=True)
    # 写盘前按契约自检：dag.json 有 schema 就得对得上，不能只当文档摆着
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import schema_check
        problems, status = schema_check.validate("dag", payload)
        if status == "unavailable":
            print("! 未安装 jsonschema，本次未做 dag 契约校验", file=sys.stderr)
        elif problems:
            print(f"! dag 与契约有 {len(problems)} 处不符：{problems[:3]}", file=sys.stderr)
    except ImportError:
        pass
    (out_dir / "dag.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "waves.json").write_text(
        json.dumps({"waves": wave_list, "critical_path": len(wave_list)},
                   ensure_ascii=False, indent=2), encoding="utf-8")

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
    print("波次")
    for i, w in enumerate(wave_list, 1):
        print(f"  {i}: {' '.join(w)}")
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
