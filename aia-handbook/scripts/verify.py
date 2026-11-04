#!/usr/bin/env python3
"""verify.py —— 一条命令跑完一本书的全链路，供 CI / 交付前自检。

顺序：plan → check → dep_brief → assemble → 产物扫描 → state 报告。
任何一步失败都继续跑完（否则只能看到一个错），最后按退出码聚合。

用法:
    python scripts/verify.py --book ../my-book
    python scripts/verify.py --book ../my-book --strict     # warn 也算失败
    python scripts/verify.py --book ../my-book --exec       # 实跑 src README 命令（C07）
    python scripts/verify.py --self-test                    # 跑闸门回归台
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: str, *args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(HERE / script), *args],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def tail(text: str, n: int = 6) -> str:
    lines = [x for x in text.strip().splitlines() if x.strip()]
    return "\n".join("    " + x for x in lines[-n:])


def verify(book: Path, strict: bool, exec_samples: bool = False) -> int:
    steps: list[tuple[str, bool, str]] = []

    code, out = run("plan.py", "--book", str(book), "--json")
    plan_ok = code == 0
    if plan_ok:                                    # 顺手读一眼有没有环
        try:
            dag = json.loads(out)
            plan_ok = not dag.get("problems")
        except json.JSONDecodeError:
            plan_ok = False
    steps.append(("plan 依赖图", plan_ok, out))

    check_args = ["--book", str(book), "--json"] + (["--exec"] if exec_samples else [])
    code, out = run("check.py", *check_args)
    errs = warns = 0
    try:
        summary = json.loads(out)["summary"]
        errs, warns = summary["error"], summary["warn"]
    except (json.JSONDecodeError, KeyError):
        pass
    check_ok = code == 0 and errs == 0 and (warns == 0 if strict else True)
    steps.append((f"check 闸门（{errs}E / {warns}W）", check_ok, out))

    code, out = run("dep_brief.py", "--book", str(book), "--json")
    missing = []
    mismatches = []
    try:
        payload = json.loads(out)
        missing = payload.get("missing", [])
        mismatches = payload.get("signature_mismatches", [])
    except json.JSONDecodeError:
        missing = ["无法解析 dep_brief 输出"]
    steps.append((f"dep_brief 摘要（缺 {len(missing)} / 签名不符 {len(mismatches)}）",
                  not missing and not mismatches, out))

    code, out = run("assemble.py", "--book", str(book), "--quiet")
    steps.append(("assemble 装配", code == 0, out))

    # 产物扫描：final/ 必须自包含，且不许有占位
    final = book / "final"
    problems: list[str] = []
    if not final.is_dir():
        problems.append("final/ 不存在")
    else:
        if not (final / "assets").is_dir():
            problems.append("final/assets 缺失（不是自包含）")
        for md in final.glob("*.md"):
            txt = md.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\]\((\.\./)", txt):
                problems.append(f"{md.name} 仍有 ../ 相对路径")
            for kw in ("（待补", "TODO", "FIXME"):
                if kw in txt:
                    problems.append(f"{md.name} 残留占位 {kw}")
                    break
    steps.append(("final 产物扫描", not problems, "\n".join(problems)))

    code, out = run("state.py", "--book", str(book), "--report", "--json")
    drift = []
    try:
        drift = json.loads(out).get("drift", [])
    except json.JSONDecodeError:
        drift = []
    steps.append((f"state 账本一致（{len(drift)} 处漂移）", not drift,
                  "\n".join(drift)))

    print(f"verify {book}")
    print()
    for name, ok, detail in steps:
        print(f"  {'✓' if ok else '✗'} {name}")
        if not ok:
            print(tail(detail))
    failed = [n for n, ok, _ in steps if not ok]
    print()
    if failed:
        print(f"✗ {len(failed)} 步未通过：{'、'.join(failed)}")
        return 1
    print("✓ 全链路通过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="一本书的全链路校验")
    ap.add_argument("--book")
    ap.add_argument("--strict", action="store_true", help="warn 也视为失败")
    ap.add_argument("--exec", dest="exec_samples", action="store_true",
                    help="透传给 check.py：实跑 src README 的运行命令并比对实测输出")
    ap.add_argument("--self-test", action="store_true", help="跑闸门回归台")
    args = ap.parse_args()

    if args.self_test:
        r = subprocess.run([sys.executable, str(HERE.parent / "tests" / "run_tests.py")],
                           text=True)
        return r.returncode

    if not args.book:
        ap.error("需要 --book，或用 --self-test")
    book = Path(args.book).resolve()
    if not (book / "book.yaml").exists():
        sys.exit(f"找不到 {book / 'book.yaml'}")
    return verify(book, args.strict, args.exec_samples)


if __name__ == "__main__":
    sys.exit(main())
