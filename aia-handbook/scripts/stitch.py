#!/usr/bin/env python3
"""stitch.py —— 波次缝合工具化（评审 B4）。

此前 `06-review.md` 描述了缝合流程、`templates/patch.md` 给了清单格式，
但没有任何脚本生成清单骨架，也没有度量「20% 改动预算」的手段。

本脚本做两件事：
1. 把 `check.py --json` 的 error/warn 转成可逐条落地的 patch 清单骨架；
2. 用 difflib 度量单章改动比例，超过预算即打回（默认 20%）。

用法:
    python scripts/stitch.py --book ../my-book --wave 3
    python scripts/stitch.py --book ../my-book --wave 3 --out patches/wave-3.md
    python scripts/stitch.py --book ../my-book --json
    python scripts/stitch.py --budget --before chapters/ch08.md --after /tmp/ch08.new.md
    python scripts/stitch.py --budget --before A --after B --limit 15
"""

from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 会进入缝合清单的错误码：结构/引用/事实/一致性类。
# 代码类（C*）与闸门组错误通常要回写手，不交给缝合 agent 顺手改。
STITCH_GATES = {"structure", "reference", "facts", "consistency"}
# 这些 finding 的修法在章纲 / book.yaml，缝合 agent 无权改（权责边界表），
# 收进清单只会诱导它越权，直接排除。
NON_STITCH_CODES = {"G4", "P12", "B01", "S19", "S24", "X00", "C00"}


def collect_findings(book_dir: Path) -> list[dict]:
    r = subprocess.run([sys.executable, str(HERE / "check.py"),
                        "--book", str(book_dir), "--json"],
                       capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"check.py 输出不可读：{(r.stderr or '')[:200]}")
    out: list[dict] = []
    def keep(f: dict) -> bool:
        return (f.get("level") in ("error", "warn")
                and f.get("gate") in STITCH_GATES
                and f.get("code") not in NON_STITCH_CODES)

    for ch, findings in (data.get("results") or {}).items():
        for f in findings:
            if keep(f):
                out.append({"chapter": ch, **f})
    for f in data.get("book_level") or []:
        if keep(f):
            out.append({"chapter": f.get("chapter", "-") or "-", **f})
    return out


def make_patch(findings: list[dict], wave: int) -> str:
    by_ch: dict[str, list[dict]] = {}
    for f in findings:
        by_ch.setdefault(f["chapter"], []).append(f)
    lines = [f"# 波次 {wave} 缝合清单", "",
             "> 由 `scripts/stitch.py` 从 `check.py --json` 生成，先出清单再逐条落地。",
             "> 缝合 agent 的权责边界见 SPEC §7.3 / 06-review.md：",
             "> 可改术语措辞、衔接句、与账本冲突的数字、重复段落、交叉引用编号；",
             "> 不可改章纲、宪法、章节结论、事实账本 source/date、依赖声明。",
             "> 事实性错误必须回源（查 claims.jsonl），不许自造正确值。", ""]
    if not findings:
        lines += ["本波次机检没有需要缝合的 error / warn。", ""]
        return "\n".join(lines)
    for ch in sorted(by_ch):
        lines += [f"## {ch}", ""]
        for i, f in enumerate(by_ch[ch], 1):
            mark = "P1" if f["level"] == "error" else "P2"
            hint = f.get("hint") or "按检查码说明修"
            lines.append(f"- {mark} [{f['code']} / {f['gate']}] {f['msg']} → {hint}")
        lines.append("")
    lines += ["## 落地前核对", "",
              "- [ ] 每条都有依据（术语查 glossary、数字查 claims、重复段落查原文）",
              "- [ ] 单章改动未超预算：`stitch.py --budget --before <旧稿> --after <新稿>`",
              "- [ ] 未触及结论段与章纲；每波一个 commit，可整体回滚", ""]
    return "\n".join(lines)


def budget(before: Path, after: Path, limit: float) -> dict:
    """用 difflib 量「改动了多少行」：非 equal 的 opcode 段按两侧最大行数计。"""
    a = before.read_text(encoding="utf-8", errors="ignore").splitlines()
    b = after.read_text(encoding="utf-8", errors="ignore").splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            changed += max(i2 - i1, j2 - j1)
    denom = max(len(a), 1)
    ratio = changed / denom * 100
    return {"before_lines": len(a), "after_lines": len(b),
            "changed_lines": changed, "ratio": round(ratio, 1),
            "limit": limit, "over_budget": ratio > limit,
            "similarity": round(sm.ratio() * 100, 1)}


def main() -> int:
    ap = argparse.ArgumentParser(description="缝合清单骨架与 20% 改动预算")
    ap.add_argument("--book", help="书项目根目录")
    ap.add_argument("--wave", type=int, default=0, help="波次号，只写进清单标题")
    ap.add_argument("--out", help="清单写入文件（缺省打印到 stdout）")
    ap.add_argument("--json", action="store_true", help="输出 findings + patch 的 JSON")
    ap.add_argument("--budget", action="store_true", help="度量单章改动比例")
    ap.add_argument("--before", help="配合 --budget：旧稿路径")
    ap.add_argument("--after", help="配合 --budget：新稿路径")
    ap.add_argument("--limit", type=float, default=20.0,
                    help="改动预算百分比，默认 20（SPEC §7.3）")
    args = ap.parse_args()

    if args.budget:
        if not args.before or not args.after:
            ap.error("--budget 需要 --before 与 --after")
        before, after = Path(args.before), Path(args.after)
        if not before.exists() or not after.exists():
            sys.exit("旧稿或新稿不存在")
        r = budget(before, after, args.limit)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(f"改动预算 {before.name} → {after.name}")
            print(f"  {r['changed_lines']} 行变更 / {r['before_lines']} 行原文 "
                  f"= {r['ratio']}%（预算 {r['limit']}%；相似度 {r['similarity']}%）")
            print("  " + ("✗ 超预算：打回原写手重跑，缝合 agent 不做大改"
                          if r["over_budget"] else "✓ 在预算内"))
        return 1 if r["over_budget"] else 0

    if not args.book:
        ap.error("需要 --book，或用 --budget")
    root = Path(args.book).resolve()
    findings = collect_findings(root)
    patch = make_patch(findings, args.wave)
    if args.json:
        print(json.dumps({"book": str(root), "wave": args.wave,
                          "findings": findings, "patch": patch},
                         ensure_ascii=False, indent=2))
    elif args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(patch, encoding="utf-8")
        print(f"已生成 {out}（{len(findings)} 条待落地）")
    else:
        print(patch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
