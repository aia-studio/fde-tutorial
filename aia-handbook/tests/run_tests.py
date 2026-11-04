#!/usr/bin/env python3
"""run_tests.py —— 闸门回归台。

两件事：
1. **基线**：每个 fixture 的 error/warn 数量必须与预期一致。数字变了就说明闸门口径动了。
2. **注入**：在临时副本上故意造违规，断言对应错误码真的能抓到。

第 2 件事是重点。账本全空的样本能跑出 0 error，只能证明"不误报"，
证明不了"查过"——F 组和 X 组此前就处在这个状态。

评审后的回归台补了两类用例：
- 新增闸门的「能抓到」证明（G4 / X09 / X10 / F04 / C02 / C07 / P12 / B01 / C08 …）；
- 机制接线证明（done 前置闸门、冻结/解冻、soft 模式、写作波次、改动预算）。

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


def state(book: Path, *args: str) -> subprocess.CompletedProcess:
    return run("state.py", "--book", str(book), *args)


def check_json(book: Path, *extra: str) -> dict:
    r = run("check.py", "--book", str(book), "--json", *extra)
    return json.loads(r.stdout)


def codes_of(data: dict, level: str = "error") -> set[str]:
    out = {f["code"] for v in data["results"].values() for f in v if f["level"] == level}
    out |= {f["code"] for f in data["book_level"] if f["level"] == level}
    return out


def book_codes(data: dict, level: str = "error") -> set[str]:
    return {f["code"] for f in data["book_level"] if f["level"] == level}


def messages_of(data: dict, code: str) -> list[str]:
    out = [f["msg"] for v in data["results"].values() for f in v if f["code"] == code]
    out += [f["msg"] for f in data["book_level"] if f["code"] == code]
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
                         f"（warn={sorted(codes_of(d, 'warn'))}）")
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


def _book_yaml(t: Path, old: str, new: str) -> None:
    p = t / "book.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")


# ---- 原有 9 个（第 3 个修正了假阳性）

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
    """承诺 open → X06；且 assemble.py 本身必须因 open 阻断（评审 A1）。

    对照实验：把 status 改回 kept 后同一份装配必须成功。
    这排除了「因缺 00-positioning.md 的前言占位而失败」的旧假阳性。
    """
    t = _copy("fixture-ledger")
    p = t / ".book" / "promises.jsonl"
    rows = _read_jsonl(p)
    rows[0]["status"] = "open"
    _write_jsonl(p, rows)
    codes = codes_of(check_json(t), "error")
    r = run("assemble.py", "--book", str(t), "--quiet")
    blocked = r.returncode != 0
    reason = "open" in (r.stdout + r.stderr) and "promises" in (r.stdout + r.stderr)
    rows[0]["status"] = "kept"
    _write_jsonl(p, rows)
    control = run("assemble.py", "--book", str(t), "--quiet")
    ok_control = control.returncode == 0
    ok = "X06" in codes and blocked and reason and ok_control
    return ok, (f"X06={'X06' in codes}, 阻断={blocked}, 归因open={reason}, "
                f"对照装配成功={ok_control}"
                + ("" if ok_control else f"（{control.stdout[-200:]}{control.stderr[-200:]}）"))


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


# ---- 评审新增闸门的「能抓到」证明

def inject_plan_missing_field() -> tuple[bool, str]:
    """章纲缺 genre 声明的必填字段 → G4 error，plan.py 也阻断（评审 A4）。"""
    t = _copy("fixture-ledger")
    p = t / "04-chapter-plans" / "ch01.md"
    txt = p.read_text(encoding="utf-8")
    assert "deliverable:" in txt
    p.write_text("\n".join(ln for ln in txt.splitlines()
                           if not ln.startswith("deliverable:")), encoding="utf-8")
    codes = book_codes(check_json(t))
    rc = run("plan.py", "--book", str(t), "--json").returncode
    return "G4" in codes and rc != 0, f"G4={'G4' in codes}, plan rc={rc}"


def inject_plan_no_frontmatter() -> tuple[bool, str]:
    """章纲无 front-matter 不再被静默跳过：G4 报错且 plan.py 明说漏章（D1）。"""
    t = _copy("fixture-ledger")
    p = t / "04-chapter-plans" / "ch01.md"
    p.write_text("# Ch01 没有 front-matter\n\n正文\n", encoding="utf-8")
    codes = book_codes(check_json(t))
    r = run("plan.py", "--book", str(t), "--json")
    explicit = "front-matter" in (r.stdout + r.stderr)
    return "G4" in codes and explicit, f"G4={'G4' in codes}, 显式报错={explicit}"


def inject_term_alias_swap() -> tuple[bool, str]:
    """正文用别名替代正名 → X09 warn（评审 A3）。"""
    t = _copy("fixture-ledger")
    p = t / "chapters" / "ch02.md"
    p.write_text(p.read_text(encoding="utf-8").replace("向量检索", "稠密检索"),
                 encoding="utf-8")
    codes = codes_of(check_json(t), "warn")
    return "X09" in codes, f"X09 in {sorted(codes)}"


def inject_term_first_chapter_wrong() -> tuple[bool, str]:
    """章序变了但 first_chapter 没跟着改 → X10 error（评审 A2）。"""
    t = _copy("fixture-ledger")
    p = t / ".book" / "glossary.json"
    g = json.loads(p.read_text(encoding="utf-8"))
    g["terms"][0]["first_chapter"] = "ch02"
    p.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    codes = book_codes(check_json(t))
    return "X10" in codes, f"X10 in {sorted(codes)}"


def inject_dead_claim() -> tuple[bool, str]:
    """登记了却没在正文出现的死 claim → F04 warn（评审 D7）。"""
    t = _copy("fixture-ledger")
    p = t / ".book" / "claims.jsonl"
    rows = _read_jsonl(p)
    rows.append({"id": "F099", "chapter": "ch01", "value": 0.99,
                 "source": "凭空构造", "date": "2026-11-05"})
    _write_jsonl(p, rows)
    codes = book_codes(check_json(t), "warn")
    return "F04" in codes, f"F04 in {sorted(codes)}"


def inject_src_secret() -> tuple[bool, str]:
    """密钥藏在 src/** 而不是正文代码块 → C02 也要抓到（评审 B3）。"""
    t = _copy("fixture-ledger")
    src = t / "src" / "ch01"
    src.mkdir(parents=True)
    (src / "client.py").write_text('api_key = "sk-abcdefgh12345678"\n', encoding="utf-8")
    (src / "README.md").write_text("运行：python -m ch01.client\n", encoding="utf-8")
    codes = codes_of(check_json(t))
    return "C02" in codes, f"C02 in {sorted(codes)}"


def inject_done_blocked() -> tuple[bool, str]:
    """--set done 必须先过单章闸门；--force 才能越权且必须留痕（评审 B1）。"""
    t = _copy("fixture")                    # ch02 是刻意反例，有 8 个 error
    state(t, "--set", "ch02", "checking", "--force")
    r = state(t, "--set", "ch02", "done")
    blocked = r.returncode != 0 and "不能置为 done" in (r.stdout + r.stderr)
    rf = state(t, "--set", "ch02", "done", "--force", "--error", "回归台验证留痕")
    st = json.loads((t / ".book" / "state.json").read_text(encoding="utf-8"))
    forced = rf.returncode == 0 and "gate_override" in st["chapters"]["ch02"]
    return blocked and forced, f"拦截={blocked}, --force 留痕={forced}"


def inject_gates_typo() -> tuple[bool, str]:
    """拼错的闸门组名不再被静默丢弃（评审 D2）。"""
    r = run("check.py", "--book", str(HERE / "fixture-ledger"), "--gates", "factsx")
    return r.returncode != 0 and "未知组" in (r.stdout + r.stderr), \
        f"rc={r.returncode}: {(r.stdout + r.stderr)[:120]}"


def inject_gates_soft() -> tuple[bool, str]:
    """book.yaml gates: soft 真的只出报告（评审 A6）。"""
    t = _copy("fixture")                    # 原本 8 error
    _book_yaml(t, "gates: hard", "gates: soft")
    r = run("check.py", "--book", str(t), "--json")
    d = json.loads(r.stdout)
    return (r.returncode == 0 and d["summary"]["error"] == 0
            and d["gate_mode"] == "soft"), f"rc={r.returncode}, {d['summary']}"


def inject_exec_output_mismatch() -> tuple[bool, str]:
    """--exec：README 贴的「实测输出」与真实运行不符 → C07 error（评审 B2）。"""
    t = _copy("fixture-ledger")
    src = t / "src" / "ch01"
    src.mkdir(parents=True)
    (src / "README.md").write_text(
        "# ch01\n\n## 运行\n\n```bash\npython -c \"print(42)\"\n```\n\n"
        "## 实测输出\n\n```text\n999\n```\n", encoding="utf-8")
    d = check_json(t, "--chapter", "ch01", "--exec")
    codes = book_codes(d)
    mismatch = any("不符" in m for m in messages_of(d, "C07"))
    return "C07" in codes and mismatch, f"C07={'C07' in codes}, 输出不符={mismatch}"


def inject_spine_constraint() -> tuple[bool, str]:
    """interview 的 spine_constraint: none 真正执行 → P12（评审 C5）。"""
    t = _copy("fixture-interview")
    _book_yaml(t, "spine: none", "spine: capstone")
    codes = book_codes(check_json(t))
    return "P12" in codes, f"P12 in {sorted(codes)}"


def inject_lang_unsupported() -> tuple[bool, str]:
    """lang=en 不再默默按中文口径统计 → B01（评审 C1）。"""
    t = _copy("fixture-principle")
    _book_yaml(t, "lang: zh-CN", "lang: en")
    codes = book_codes(check_json(t))
    return "B01" in codes, f"B01 in {sorted(codes)}"


def inject_unknown_genre() -> tuple[bool, str]:
    """genre 从目录自动发现，写不存在的体裁会被拦下（评审 C4）。"""
    t = _copy("fixture-principle")
    _book_yaml(t, "genre: principle", "genre: mystery")
    r = run("schema_check.py", "--kind", "book", "--file", str(t / "book.yaml"))
    return r.returncode != 0 and "genre" in r.stdout, f"rc={r.returncode}: {r.stdout[:160]}"


def inject_freeze_flow() -> tuple[bool, str]:
    """冻结/解冻/phase 工具化，解冻列出需重跑章节（评审 A5）。"""
    t = _copy("fixture-ledger")
    r1 = state(t, "--freeze", "constitution")
    r2 = state(t, "--unfreeze", "constitution", "--reason", "术语表改了两条定义")
    r3 = state(t, "--freeze-report")
    r4 = state(t, "--phase", "3-chapter-plan")
    st = json.loads((t / ".book" / "state.json").read_text(encoding="utf-8"))
    ok = (all(r.returncode == 0 for r in (r1, r2, r3, r4))
          and st["phase"] == "3-chapter-plan"
          and len(st.get("freeze_log", [])) == 2
          and "需要重跑闸门" in r2.stdout
          and "冻结状态" in r3.stdout
          and st.get("frozen_meta", {}).get("constitution", {}).get("hash"))
    return ok, f"rc={[r.returncode for r in (r1,r2,r3,r4)]}, phase={st.get('phase')}"


def inject_writing_waves() -> tuple[bool, str]:
    """plan.py 产出写作波次表（评审 B5）。"""
    t = _copy("fixture-smoke8")
    r = run("plan.py", "--book", str(t), "--json")
    d = json.loads(r.stdout)
    waves = d.get("writing_waves", {}).get("waves", [])
    return r.returncode == 0 and len(waves) >= 1, f"rc={r.returncode}, 波数={len(waves)}"


def inject_project_curve() -> tuple[bool, str]:
    """capstone 项目推进曲线从章纲 project_stage 产出（评审 A8）。"""
    t = _copy("fixture-project")
    for i, name in enumerate(sorted((t / "04-chapter-plans").glob("ch*.md")), 1):
        p = name
        txt = p.read_text(encoding="utf-8")
        p.write_text(txt.replace("deliverable:", f"project_stage: 阶段{i}\ndeliverable:", 1),
                     encoding="utf-8")
    r = run("plan.py", "--book", str(t), "--json")
    d = json.loads(r.stdout)
    stages = d.get("project_curve", {}).get("stages", [])
    return r.returncode == 0 and len(stages) == 2, f"rc={r.returncode}, stages={len(stages)}"


def inject_signature_mismatch() -> tuple[bool, str]:
    """终稿合同签名与章纲草案不一致 → C08（评审 B5）。"""
    t = _copy("fixture-ledger")
    p = t / "04-chapter-plans" / "ch01.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "deliverable: 一份失效场景清单",
        "provides:\n  modules:\n    - module: src/ch01/embed.py\n"
        "      api: \"embed(text: str) -> list[float]\"\ndeliverable: 一份失效场景清单", 1),
        encoding="utf-8")
    c = t / ".book" / "contracts" / "ch01.json"
    data = json.loads(c.read_text(encoding="utf-8"))
    data["provides"][0]["api"] = "embed(text: str, model: str) -> list[float]"
    c.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    r = run("dep_brief.py", "--book", str(t), "--check-signatures", "--json")
    d = json.loads(r.stdout)
    return r.returncode == 1 and len(d["signature_mismatches"]) >= 1, \
        f"rc={r.returncode}, 不符={len(d['signature_mismatches'])}"


def inject_draft_contract() -> tuple[bool, str]:
    """缺终稿合同时，章纲 provides 可作草案合同且明确标 [draft]（评审 B5/D3）。"""
    t = _copy("fixture-ledger")
    p = t / "04-chapter-plans" / "ch01.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "deliverable: 一份失效场景清单",
        "provides:\n  modules:\n    - module: src/ch01/embed.py\n"
        "      api: \"embed(text: str) -> list[float]\"\ndeliverable: 一份失效场景清单", 1),
        encoding="utf-8")
    (t / ".book" / "contracts" / "ch01.json").unlink()
    r = run("dep_brief.py", "--book", str(t), "--json")
    d = json.loads(r.stdout)
    brief = (t / "dep-brief" / "ch02.md").read_text(encoding="utf-8")
    return (r.returncode == 0 and not d["missing"] and "[draft]" in brief
            and "草案级合同" in brief), f"rc={r.returncode}, missing={d['missing']}"


def inject_patch_budget() -> tuple[bool, str]:
    """20% 改动预算可度量且会打回（评审 B4）。"""
    t = Path(tempfile.mkdtemp())
    a, b = t / "before.md", t / "after.md"
    a.write_text("\n".join(f"第 {i} 行原文" for i in range(20)), encoding="utf-8")
    b.write_text("\n".join([" rewritten "] * 15 + [f"第 {i} 行原文" for i in range(15, 20)]),
                 encoding="utf-8")
    r = run("stitch.py", "--budget", "--before", str(a), "--after", str(b))
    return r.returncode == 1 and "超预算" in r.stdout, f"rc={r.returncode}: {r.stdout.strip()}"


def inject_faq_by_skeleton_id() -> tuple[bool, str]:
    """FAQ 按骨架段 id 收集，project 的「风险登记」也能进附录 E（评审 C3）。"""
    t = _copy("fixture-project")
    run("assemble.py", "--book", str(t), "--quiet")
    faq = (t / "final" / "appendix-e-faq.md").read_text(encoding="utf-8")
    return "风险登记" in faq, f"FAQ 含风险登记={'风险登记' in faq}"


INJECTIONS = [
    ("删 claim → F01", inject_claim_missing),
    ("claim 缺出处 → F02", inject_claim_no_source),
    ("承诺 open → X06 且装配真阻断", inject_promise_open),
    ("承诺未入账 → X02", inject_promise_missing),
    ("阶梯倒退 → X03", inject_ladder_regress),
    ("别名撞车 → X08", inject_glossary_alias),
    ("术语未登记 → X01", inject_term_unregistered),
    ("无版本锁 → C04", inject_no_version_lock),
    ("合同不合契约 → C06", inject_contract_broken),
    ("章纲缺字段 → G4", inject_plan_missing_field),
    ("章纲无 front-matter → G4", inject_plan_no_frontmatter),
    ("别名替代正名 → X09", inject_term_alias_swap),
    ("术语首现章不符 → X10", inject_term_first_chapter_wrong),
    ("死 claim → F04", inject_dead_claim),
    ("src 里的密钥 → C02", inject_src_secret),
    ("done 未过闸门 → 拒绝", inject_done_blocked),
    ("闸门组拼错 → 显式报错", inject_gates_typo),
    ("gates: soft → 只出报告", inject_gates_soft),
    ("--exec 输出不符 → C07", inject_exec_output_mismatch),
    ("spine 约束 → P12", inject_spine_constraint),
    ("不支持的 lang → B01", inject_lang_unsupported),
    ("未知 genre → 动态校验", inject_unknown_genre),
    ("冻结/解冻/phase → 留痕", inject_freeze_flow),
    ("写作波次表 → plan.py", inject_writing_waves),
    ("capstone 项目曲线 → plan.py", inject_project_curve),
    ("签名不符 → C08", inject_signature_mismatch),
    ("草案合同 → dep-brief [draft]", inject_draft_contract),
    ("超 20% 预算 → 打回", inject_patch_budget),
    ("FAQ 按骨架 id → 附录 E", inject_faq_by_skeleton_id),
]


def test_injections() -> list[str]:
    fails = []
    for label, fn in INJECTIONS:
        try:
            ok, detail = fn()
        except Exception as e:                              # noqa: BLE001
            fails.append(f"{label}: 抛异常 {e!r}")
            print(f"  ✗ {label:32} 异常 {e!r}")
            continue
        if ok:
            print(f"  ✓ {label:32}")
            if VERBOSE:
                print(f"      {detail}")
        else:
            fails.append(f"{label}: 没抓到（{detail}）")
            print(f"  ✗ {label:32} 没抓到：{detail}")
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
