#!/usr/bin/env python3
"""dep_brief.py —— 生成上游摘要包 `dep-brief/chNN.md`。

只读三样东西：
1. `.book/dag.json` 的 `requires`（哪些章是上游）
2. `.book/contracts/chNN.json`（上游的定义、模块签名、hook）
3. 章纲的「与相邻章的边界」段（本章不重复什么）

**不读上游全文。** 这是上下文控制，也是一致性的来源。

缺上游合同时，在摘要里写明确的警告块，并以退出码 1 结束——
"没有合同就自己补定义"是分叉的起点，必须显式阻断。

用法:
    python scripts/dep_brief.py --book <书目录>
    python scripts/dep_brief.py --book <书目录> --chapter ch05
    python scripts/dep_brief.py --book <书目录> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("需要 pyyaml：python -m pip install pyyaml")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _fm(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


def _section(text: str, title: str) -> str:
    """取 `## <title>` 到下一个 `## ` 之间的正文。"""
    m = re.search(rf"^##\s+{re.escape(title)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s+", rest, re.M)
    return (rest[:nxt.start()] if nxt else rest).strip()


def _load_dag(book_dir: Path, book: dict) -> dict[str, list[str]]:
    p = book_dir / ".book" / "dag.json"
    if p.exists():
        try:
            data = json.loads(_read(p))
            return {k: list(v.get("requires", [])) for k, v in data.get("nodes", {}).items()}
        except json.JSONDecodeError:
            pass
    plan_dir = book_dir / book.get("paths", {}).get("plans", "04-chapter-plans")
    dag: dict[str, list[str]] = {}
    for f in sorted(plan_dir.glob("ch*.md")):
        meta = _fm(_read(f))
        no = str(meta.get("chapter") or f.stem.replace("ch", "")).zfill(2)
        dag[f"ch{no}"] = [f"ch{str(x).zfill(2)}" for x in (meta.get("requires") or [])]
    return dag


def _render(name: str, title: str, reqs: list[str],
            defines: list[tuple], provides: list[tuple], hooks: list[tuple],
            boundary: str, missing: list[str]) -> str:
    lines = [
        f"# {name.upper()} 上游摘要包",
        "",
        "> 自动生成，**勿手改**。只含上游合同与签名，不含上游全文。",
        "> 消费者：本章写手。只信这里，不要回头读上游正文。",
        "",
    ]
    if missing:
        lines += ["> ⚠ 合同缺失，**暂停开写**：", ">"]
        for m in missing:
            lines.append(f"> - {m}")
        lines.append(">")

    if not reqs:
        lines += ["本章是根节点，无上游合同。", ""]
    else:
        lines += [f"上游：{'、'.join(reqs)}", ""]

    lines += ["## 一、可以无解释使用的定义", "",
              "| 概念 id | 中文 | English | 定义 | 来自 |",
              "| --- | --- | --- | --- | --- |"]
    if defines:
        for cid, zh, en, d, up in defines:
            lines.append(f"| {cid} | {zh} | {en} | {d} | {up} |")
    else:
        lines.append("| — | （无） | | | |")

    lines += ["", "## 二、可以 import 的模块", "",
              "| 模块 | 签名 | 来自 |", "| --- | --- | --- |"]
    if provides:
        for mod, api, up in provides:
            lines.append(f"| `{mod}` | `{api}` | {up} |")
    else:
        lines.append("| — | （无） | |")

    lines += ["", "## 三、上游结论（可直接引用，不必复述推导）", ""]
    if hooks:
        for h, up in hooks:
            lines.append(f"- {h}（来自 {up}）")
    else:
        lines.append("- （无）")

    lines += ["", "## 四、本章的边界", ""]
    if boundary:
        lines += [boundary, ""]
    else:
        lines += ["- 章纲未写「与相邻章的边界」，建议补上。", ""]

    lines += [
        "## 五、缺合同时的处理", "",
        "上游合同缺失、或签名与实际代码对不齐 → **停下报告，不要自己补定义**。",
        "自己补的定义会与上游分叉，缝合阶段要动代码而不是动文字。", "",
    ]
    return "\n".join(lines)


def build(book_dir: Path, only: str | None) -> tuple[list[str], list[str]]:
    book = yaml.safe_load(_read(book_dir / "book.yaml")) or {}
    dag = _load_dag(book_dir, book)
    if not dag:
        sys.exit("没有章纲，无法生成 dep-brief")

    plans = book_dir / book.get("paths", {}).get("plans", "04-chapter-plans")
    contracts = book_dir / ".book" / "contracts"
    out_dir = book_dir / "dep-brief"
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [only] if only else sorted(dag)
    all_missing: list[str] = []
    written: list[str] = []

    for name in targets:
        if name not in dag:
            sys.exit(f"未知章节：{name}")
        reqs = dag[name]
        defines: list[tuple] = []
        provides: list[tuple] = []
        hooks: list[tuple] = []
        missing: list[str] = []

        for up in reqs:
            c = contracts / f"{up}.json"
            if not c.exists():
                msg = f"{name} 的上游 {up} 缺合同（.book/contracts/{up}.json）"
                missing.append(msg)
                all_missing.append(msg)
                continue
            try:
                data = json.loads(_read(c))
            except json.JSONDecodeError:
                msg = f"{up} 的合同不是合法 JSON"
                missing.append(msg)
                all_missing.append(msg)
                continue
            for d in data.get("defines", []) or []:
                defines.append((d.get("id", ""), d.get("zh", ""), d.get("en", ""),
                                d.get("def", ""), up))
            for m in data.get("provides", []) or []:
                provides.append((m.get("module", ""), m.get("api", ""), up))
            if data.get("hook"):
                hooks.append((str(data["hook"]), up))

        plan_text = _read(plans / f"{name}.md")
        plan = _fm(plan_text)
        boundary = _section(plan_text, "与相邻章的边界")
        title = str(plan.get("title", ""))

        (out_dir / f"{name}.md").write_text(
            _render(name, title, reqs, defines, provides, hooks, boundary, missing),
            encoding="utf-8")
        written.append(name)

    return written, all_missing


def main() -> int:
    ap = argparse.ArgumentParser(description="生成上游摘要包 dep-brief/")
    ap.add_argument("--book", required=True)
    ap.add_argument("--chapter", help="只生成指定章")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.book).resolve()
    if not (root / "book.yaml").exists():
        sys.exit(f"找不到 {root / 'book.yaml'}")

    written, missing = build(root, args.chapter)

    if args.json:
        print(json.dumps({"book": str(root), "written": written, "missing": missing},
                         ensure_ascii=False, indent=2))
    else:
        print(f"已生成 {len(written)} 份上游摘要 → {root / 'dep-brief'}")
        for m in missing:
            print(f"  ✗ {m}")
        if not missing:
            print("  ✓ 所有上游合同齐全")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
