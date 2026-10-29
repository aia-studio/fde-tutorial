#!/usr/bin/env python3
"""run_tests.py —— 闸门回归台。

两件事：
1. **基线**：每个 fixture 的 error/warn 数量必须与预期一致。数字变了就说明闸门口径动了。
2. **注入**：在临时副本上故意造违规，断言对应错误码真的能抓到。

第 2 件事是重点。账本全空的样本能跑出 0 error，只能证明"不误报"，
证明不了"查过"——F 组和 X 组此前就处在这个状态。

用法:
    python tests/run_tests.py
    python tests/run_tests.py -v
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # aia-handbook/
SCRIPTS = ROOT / "scripts"

# 每个样本的预期：(error, warn)。反例样本本来就该红，正例必须全绿。
BASELINE = {
    "fixture": (8, 2),                  # 刻意反例：结构/引用/禁用词
    "fixture-principle": (0, 0),
    "fixture-project": (0, 0),
    "fixture-interview": (0, 0),
    "fixture-smoke8": (0, 28),          # 同模板生成，X04 跨章重复是预期的
    "fixture-ledger": (0, 0),           # 账本非空的通过样本
}

VERBOSE = False


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          capture_output=True, text=True)


def check_json(book: Path) -> dict:
    r = run("check.py", "--book", str(book), "--json")
    return json.loads(r.stdout)


def codes_of(data: dict, level: str = "error") -> set[str]:
    out = {f["code"] for v in data["results"].values() for f in v if f["level"] == level}
    out |= {f["code"] for f in data["book_level"] if f["level"] == level}
    return out


# ---------------------------------------------------------------- 基线

def test_baseline() -> list[str]:
    fails = []
    for name, (want_e, want_w) in BASELINE.items():
        book = HERE / name
        if not book.exists():
            fails.append(f"{name}: 样本目录不存在")
            continue
        d = check_json(book)
        got_e, got_w = d["summary"]["error"], d["summary"]["warn"]
        ok = (got_e, got_w) == (want_e, want_w)
        if ok:
            print(f"  ✓ {name:20} {got_e}E/{got_w}W")
        else:
            fails.append(f"{name}: 预期 {want_e}E/{want_w}W，实际 {got_e}E/{got_w}W"
                         f"（E={sorted(codes_of(d))}）")
            print(f"  ✗ {name:20} 预期 {want_e}E/{want_w}W，实际 {got_e}E/{got_w}W")
    return fails


# ---------------------------------------------------------------- 注入

def _copy(name: str) -> Path:
    tmp = Path(tempfile.mkdtemp()) / name
    shutil.copytree(HERE / name, tmp)
    return tmp


def _write_jsonl(p: Path, rows: list[dict]) -> None:
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                 encoding="utf-8")


def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def inject_claim_missing() -> tuple[bool, str]:
    """删掉一条 claim，正文里那个数字就该报 F01。"""
    t = _copy("fixture-ledger")
    rows = _read_jsonl(t / ".book" / "claims.jsonl")[1:]      # 去掉 F001（0.42）
    _write_jsonl(t / ".book" / "claims.jsonl", rows)
    codes = codes_of(check_json(t), "error")
    return "F01" in codes, f"F01 in {sorted(codes)}"


def inject_claim_no_source() -> tuple[bool, str]:
    """claim 缺 source/date → F02。"""
    t = _copy("fixture-ledger")
    rows = _read_jsonl(t / ".book" / "claims.jsonl")
    rows[0].pop("source", None)
    _write_jsonl(t / ".book" / "claims.jsonl", rows)
    codes = codes_of(check_json(t), "error")
    return "F02" in codes, f"F02 in {sorted(codes)}"


def inject_promise_open() -> tuple[bool, str]:
    """承诺挂着 open → X06 报错，装配被阻断。"""
    t = _copy("fixture-ledger")
    rows = _read_jsonl(t / ".book" / "promises.jsonl")
    rows[0]["status"] = "open"
    _write_jsonl(t / ".book" / "promises.jsonl", rows)
    codes = codes_of(check_json(t), "error")
    blocked = run("assemble.py", "--book", str(t), "--quiet").returncode != 0
    return ("X06" in codes and blocked), f"X06 in {sorted(codes)}，assemble 阻断={blocked}"


def inject_promise_missing() -> tuple[bool, str]:
    """「下一章」做了前向承诺却没入账 → X02。"""
    t = _copy("fixture-ledger")
    (t / ".book" / "promises.jsonl").write_text("", encoding="utf-8")
    codes = codes_of(check_json(t), "error")
    return "X02" in codes, f"X02 in {sorted(codes)}"


def inject_ladder_regress() -> tuple[bool, str]:
    """能力阶梯倒退 → X03。"""
    t = _copy("fixture-ledger")
    _write_jsonl(t / ".book" / "ladder.jsonl", [
        {"chapter": "ch01", "before": [], "after": ["A", "B"], "covers": []},
        {"chapter": "ch02", "before": ["A"], "after": ["A"], "covers": []},
    ])
    codes = codes_of(check_json(t), "error")
    return "X03" in codes, f"X03 in {sorted(codes)}"


def inject_glossary_alias() -> tuple[bool, str]:
    """同一别名挂在两个术语上 → X08。"""
    t = _copy("fixture-ledger")
    g = json.loads((t / ".book" / "glossary.json").read_text(encoding="utf-8"))
    g["terms"].append({"id": "C003", "zh": "稠密检索", "en": "Dense Retrieval",
                       "def": "另一个说法", "first_chapter": "ch02", "aliases": ["向量检索"]})
    (t / ".book" / "glossary.json").write_text(json.dumps(g, ensure_ascii=False),
                                               encoding="utf-8")
    codes = codes_of(check_json(t), "error")
    return "X08" in codes, f"X08 in {sorted(codes)}"


def inject_term_unregistered() -> tuple[bool, str]:
    """首现术语没登记 glossary → X01。"""
    t = _copy("fixture-ledger")
    p = t / "chapters" / "ch01.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "## 延伸阅读", "这套做法叫倒排索引（Inverted Index），是字面检索的基础。\n\n## 延伸阅读", 1),
        encoding="utf-8")
    codes = codes_of(check_json(t), "error")
    return "X01" in codes, f"X01 in {sorted(codes)}"


def inject_no_version_lock() -> tuple[bool, str]:
    """有 src/ 却没有 versions.lock → C04 提示，不再静默跳过。"""
    t = _copy("fixture-ledger")
    src = t / "src" / "ch01"
    src.mkdir(parents=True)
    (src / "x.py").write_text("import yaml\n", encoding="utf-8")
    (src / "README.md").write_text("运行：python -m ch01.x\n", encoding="utf-8")
    data = check_json(t)
    codes = {f["code"] for v in data["results"].values() for f in v}
    codes |= {f["code"] for f in data["book_level"]}
    return "C04" in codes, f"C04 in {sorted(codes)}"


def inject_contract_broken() -> tuple[bool, str]:
    """合同缺必填字段 → C06 按 contract.schema.json 拦下。"""
    t = _copy("fixture-ledger")
    c = t / ".book" / "contracts"
    c.mkdir(parents=True, exist_ok=True)
    (c / "ch01.json").write_text(json.dumps({"chapter": "ch01"}), encoding="utf-8")
    codes = codes_of(check_json(t), "error")
    return "C06" in codes, f"C06 in {sorted(codes)}"


INJECTIONS = [
    ("删 claim → F01", inject_claim_missing),
    ("claim 缺出处 → F02", inject_claim_no_source),
    ("承诺 open → X06 且阻断装配", inject_promise_open),
    ("承诺未入账 → X02", inject_promise_missing),
    ("阶梯倒退 → X03", inject_ladder_regress),
    ("别名撞车 → X08", inject_glossary_alias),
    ("术语未登记 → X01", inject_term_unregistered),
    ("无版本锁 → C04", inject_no_version_lock),
    ("合同不合契约 → C06", inject_contract_broken),
]


def test_injections() -> list[str]:
    fails = []
    for label, fn in INJECTIONS:
        try:
            ok, detail = fn()
        except Exception as e:                              # noqa: BLE001
            fails.append(f"{label}: 抛异常 {e!r}")
            print(f"  ✗ {label:28} 异常")
            continue
        if ok:
            print(f"  ✓ {label:28}")
            if VERBOSE:
                print(f"      {detail}")
        else:
            fails.append(f"{label}: 没抓到（{detail}）")
            print(f"  ✗ {label:28} 没抓到：{detail}")
    return fails


def main() -> int:
    global VERBOSE
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    VERBOSE = args.verbose

    print("基线（数量必须稳定）")
    f1 = test_baseline()
    print("\n注入（违规必须被抓到）")
    f2 = test_injections()

    fails = f1 + f2
    print()
    if fails:
        print(f"✗ {len(fails)} 项未通过：")
        for x in fails:
            print(f"  - {x}")
        return 1
    print(f"✓ 全部通过（{len(BASELINE)} 个基线 + {len(INJECTIONS)} 个注入）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
