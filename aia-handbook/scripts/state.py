#!/usr/bin/env python3
"""state.py —— 章节状态机与多作者协作。

职责：
1. 加锁读改写 `state.json`，多写手并发安全
2. 章节归属（claim / release）与冲突检测
3. 状态报告：ready / blocked / 下一步
4. repair 旧稿快照与回滚

状态机（SPEC §6）：
    pending → ready → writing → checking → merging → done
                          ↑         │
                          └─ repair ┘  （最多 2 次，第 3 次转 failed）
    blocked：上游 failed / blocked 时

用法:
    python scripts/state.py --book <书目录> --init
    python scripts/state.py --book <书目录> --report
    python scripts/state.py --book <书目录> --claim ch03 --owner agent-a
    python scripts/state.py --book <书目录> --release ch03 --owner agent-a
    python scripts/state.py --book <书目录> --set ch03 writing --owner agent-a
    python scripts/state.py --book <书目录> --set ch03 repair --error "S01 字数不足"
    python scripts/state.py --book <书目录> --rollback ch03
    python scripts/state.py --book <书目录> --report --json

并发约定：
- 所有写操作都经过 `.book/state.lock`（O_CREAT|O_EXCL）串行化
- 每次写 `rev += 1`；`--expect-rev N` 可做乐观并发校验
- 冲突（同一章被两个 owner 同时写）默认拒绝，`--force` 可抢占
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("需要 pyyaml：python -m pip install pyyaml")

STATUSES = ["pending", "ready", "writing", "checking", "repair",
            "merging", "done", "blocked", "failed"]
REPAIR_MAX = 2
LOCK_TIMEOUT = 10.0


# ---------------------------------------------------------------- 基础

def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _book_meta(book_dir: Path) -> dict:
    p = book_dir / "book.yaml"
    if not p.exists():
        sys.exit(f"找不到 {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _paths(book_dir: Path, book: dict) -> dict[str, Path]:
    p = book.get("paths", {})
    return {
        "chapters": book_dir / p.get("chapters", "chapters"),
        "plans": book_dir / p.get("plans", "04-chapter-plans"),
        "book": book_dir / ".book",
    }


@contextmanager
def _lock(book_dir: Path, timeout: float = LOCK_TIMEOUT):
    """跨进程排他锁。进程崩溃留下的 stale lock 需人工确认后删除。"""
    d = book_dir / ".book"
    d.mkdir(parents=True, exist_ok=True)
    lock = d / "state.lock"
    start = time.time()
    fd: int | None = None
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {_now()}".encode("utf-8"))
            break
        except FileExistsError:
            if time.time() - start > timeout:
                sys.exit(f"拿不到 state 锁：{lock}\n"
                         f"确认没有其他写手在改后，删除该文件重试。")
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def _empty_state() -> dict:
    return {
        "version": 2,
        "created": _now()[:10],
        "phase": "0-intake",
        "frozen": {"positioning": False, "toc": False, "constitution": False},
        "writers": {},
        "chapters": {},
    }


def load_state(book_dir: Path) -> dict:
    p = book_dir / ".book" / "state.json"
    if not p.exists():
        return _empty_state()
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        sys.exit(f"{p} 不是合法 JSON")
    st.setdefault("version", 2)
    st.setdefault("chapters", {})
    st.setdefault("writers", {})
    st.setdefault("frozen", {})
    return st


def _save(book_dir: Path, st: dict) -> None:
    p = book_dir / ".book" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)                       # 原子替换，避免半截文件


def update(book_dir: Path, fn: Callable[[dict], None]) -> dict:
    """加锁读改写。fn 内抛 SystemExit 会正常释放锁且不落盘。"""
    with _lock(book_dir):
        st = load_state(book_dir)
        fn(st)
        _warn_schema("state", st)
        _save(book_dir, st)
        return st


def _warn_schema(kind: str, payload: dict) -> list[str]:
    """写盘前按契约自检；schema 缺失或没装 jsonschema 时不假装通过。"""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import schema_check
    except ImportError:
        return []
    problems, status = schema_check.validate(kind, payload)
    if status == "unavailable":
        print("! 未安装 jsonschema，本次未做契约校验（pip install jsonschema）",
              file=sys.stderr)
    elif problems:
        print(f"! {kind} 与契约有 {len(problems)} 处不符：", file=sys.stderr)
        for p in problems[:5]:
            print(f"    - {p}", file=sys.stderr)
    return problems


def load_dag(book_dir: Path, book: dict) -> dict[str, list[str]]:
    """优先读 .book/dag.json；缺失时从章纲 front-matter 现场编译。"""
    p = book_dir / ".book" / "dag.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return {k: list(v.get("requires", [])) for k, v in data.get("nodes", {}).items()}
    plan_dir = _paths(book_dir, book)["plans"]
    dag: dict[str, list[str]] = {}
    for f in sorted(plan_dir.glob("ch*.md")):
        txt = f.read_text(encoding="utf-8")
        meta: dict[str, Any] = {}
        if txt.startswith("---"):
            end = txt.find("\n---", 3)
            if end > 0:
                meta = yaml.safe_load(txt[3:end]) or {}
        no = str(meta.get("chapter") or f.stem.replace("ch", "")).zfill(2)
        dag[f"ch{no}"] = [f"ch{str(x).zfill(2)}" for x in (meta.get("requires") or [])]
    return dag


# ---------------------------------------------------------------- 计算

def compute(st: dict, dag: dict[str, list[str]]) -> list[dict]:
    chapters = st.get("chapters", {})
    rows: list[dict] = []
    for name in sorted(dag):
        cs = chapters.get(name, {})
        status = cs.get("status", "pending")
        reqs = dag[name]
        req_status = {r: chapters.get(r, {}).get("status", "pending") for r in reqs}
        if any(s in ("failed", "blocked") for s in req_status.values()):
            effective = "blocked"
        elif status in ("pending", "ready") and all(s == "done" for s in req_status.values()):
            effective = "ready"
        else:
            effective = status
        rows.append({
            "chapter": name,
            "status": status,
            "effective": effective,
            "attempts": cs.get("attempts", 0),
            "owner": cs.get("owner"),
            "requires": reqs,
            "req_status": req_status,
        })
    return rows


def _next_steps(rows: list[dict]) -> list[str]:
    out: list[str] = []
    ready = [r["chapter"] for r in rows if r["effective"] == "ready"]
    if ready:
        out.append("可开写：" + "、".join(ready))
    writing = [r["chapter"] for r in rows if r["effective"] in ("writing", "checking", "repair")]
    if writing:
        out.append("进行中：" + "、".join(f"{r['chapter']}({r['effective']})" for r in rows
                                          if r["effective"] in ("writing", "checking", "repair")))
    blocked = [r["chapter"] for r in rows if r["effective"] == "blocked"]
    if blocked:
        out.append("被阻塞：" + "、".join(blocked) + "（先处理上游 failed/blocked）")
    done = [r["chapter"] for r in rows if r["effective"] == "done"]
    out.append(f"已完成 {len(done)}/{len(rows)} 章")
    return out


# ---------------------------------------------------------------- 命令

def cmd_init(book_dir: Path, force: bool) -> int:
    book = _book_meta(book_dir)
    dag = load_dag(book_dir, book)
    if not dag:
        sys.exit("没有章纲，先写 04-chapter-plans/ch*.md 并跑 plan.py")

    def fn(st: dict) -> None:
        for name in sorted(dag):
            cs = st["chapters"].setdefault(
                name, {"status": "pending", "attempts": 0, "owner": None, "rev": 0})
            if force and cs.get("status") in (None, "pending"):
                cs["status"] = "pending"
        for name in sorted(dag):
            cs = st["chapters"][name]
            if cs.get("status") == "pending" and all(
                    st["chapters"].get(r, {}).get("status") == "done" for r in dag[name]):
                cs["status"] = "ready"
                cs["rev"] = cs.get("rev", 0) + 1
                cs["updated_at"] = _now()

    update(book_dir, fn)
    print(f"已初始化 {len(dag)} 章状态（dag 来源：.book/dag.json 或章纲）")
    return 0


def cmd_report(book_dir: Path, as_json: bool) -> int:
    book = _book_meta(book_dir)
    dag = load_dag(book_dir, book)
    st = load_state(book_dir)
    rows = compute(st, dag)
    drift = detect_drift(book_dir, st, dag)

    if as_json:
        print(json.dumps({"phase": st.get("phase"), "rows": rows,
                          "next": _next_steps(rows), "drift": drift},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"状态报告 {book_dir}")
    print(f"  phase: {st.get('phase')}   章数: {len(rows)}")
    print()
    print(f"  {'章':<6}{'状态':<10}{'owner':<12}{'attempts':<10}上游")
    for r in rows:
        mark = {"blocked": "✗", "failed": "✗", "done": "✓"}.get(r["effective"], " ")
        owner = r["owner"] or "-"
        req = ",".join(f"{k}:{v}" for k, v in r["req_status"].items()) or "-"
        print(f"  {mark} {r['chapter']:<6} {r['effective']:<10} {owner:<12} "
              f"{r['attempts']:<10} {req}")
    print()
    for line in _next_steps(rows):
        print(f"  → {line}")
    if drift:
        print()
        print("! 账本与磁盘不一致：")
        for d in drift:
            print(f"  - {d}")
    return 0


def detect_drift(book_dir: Path, st: dict, dag: dict) -> list[str]:
    """账本说没写、磁盘上却有正文——这类漂移会让续跑把已完成的章重写一遍。"""
    ch_dir = book_dir / "chapters"
    if not ch_dir.is_dir():
        return []
    out: list[str] = []
    for p in sorted(ch_dir.glob("ch*.md")):
        meta = st.get("chapters", {}).get(p.stem, {})
        status = meta.get("status", "pending")
        body = p.read_text(encoding="utf-8", errors="ignore")
        # 去掉 front-matter 后判断是不是真有内容
        if body.startswith("---"):
            end = body.find("\n---", 3)
            if end > 0:
                body = body[end + 4:]
        if len(body.strip()) > 200 and status in ("pending", "ready", "blocked"):
            out.append(f"{p.stem} 磁盘已有正文，但状态是 {status}（续跑会重写）")
        elif len(body.strip()) <= 200 and status == "done":
            out.append(f"{p.stem} 状态是 done，但正文几乎是空的")
    return out


def cmd_calibrate(book_dir: Path, from_chs: list[str]) -> int:
    """用已完成的章校准文风指纹（SPEC §7.2）：中位数做基准，带宽取离散度的 1.5 倍。"""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import check as ck
    except ImportError:
        sys.exit("校准需要同目录的 check.py")

    ch_dir = book_dir / "chapters"
    paths = [ch_dir / f"{c}.md" for c in from_chs] if from_chs else sorted(ch_dir.glob("ch*.md"))
    paths = [p for p in paths if p.exists()]
    if len(paths) < 2:
        sys.exit("至少需要 2 章才能校准；先写完第一波（或 --from ch01,ch02）")

    series: dict[str, list[float]] = {}
    for p in paths:
        for k, v in ck.chapter_metrics(ck.parse_chapter(p)).items():
            series.setdefault(k, []).append(v)

    def median(xs: list[float]) -> float:
        s = sorted(xs)
        n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

    floor = {"avg_sentence_len": 4.0, "avg_paragraph_len": 12.0,
             "annotation_per_kchar": 0.4, "figures_per_section": 0.25,
             "code_block_lines": 5.0}
    metrics: dict[str, dict[str, float]] = {}
    for k, xs in series.items():
        med = median(xs)
        spread = (sum((x - med) ** 2 for x in xs) / len(xs)) ** 0.5
        metrics[k] = {"mean": round(med, 1),
                      "band": round(max(spread * 1.5, floor.get(k, 0.2)), 1)}

    out = book_dir / ".book" / "style-fingerprint.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "source": "calibrated",
        "calibrated_at": _now(),
        "based_on": [p.stem for p in paths],
        "metrics": metrics,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已校准 {out}（基于 {len(paths)} 章：{'、'.join(p.stem for p in paths)}）")
    for k, v in metrics.items():
        print(f"  {k:22} {v['mean']} ± {v['band']}")
    return 0


def cmd_claim(book_dir: Path, ch: str, owner: str, force: bool) -> int:
    def fn(st: dict) -> None:
        cs = st["chapters"].setdefault(
            ch, {"status": "pending", "attempts": 0, "owner": None, "rev": 0})
        cur = cs.get("owner")
        if cur and cur != owner and cs.get("status") in ("writing", "checking", "repair") and not force:
            sys.exit(f"{ch} 已被 {cur} 占用（status={cs.get('status')}）。\n"
                     f"→ 换一章，或加 --force 抢占（会记入 last_error）。")
        if cur and cur != owner and force:
            cs["last_error"] = f"owner 由 {cur} 被 {owner} 抢占"
        cs["owner"] = owner
        cs["rev"] = cs.get("rev", 0) + 1
        cs["updated_at"] = _now()
        st["writers"].setdefault(owner, {"last_seen": _now(), "chapters": []})
        st["writers"][owner]["last_seen"] = _now()
        if ch not in st["writers"][owner]["chapters"]:
            st["writers"][owner]["chapters"].append(ch)

    update(book_dir, fn)
    print(f"{owner} 已认领 {ch}")
    return 0


def cmd_release(book_dir: Path, ch: str, owner: str) -> int:
    def fn(st: dict) -> None:
        cs = st["chapters"].get(ch)
        if not cs:
            sys.exit(f"{ch} 不存在")
        if owner and cs.get("owner") and cs["owner"] != owner:
            sys.exit(f"{ch} 的 owner 是 {cs['owner']}，不是 {owner}，无权释放")
        cs["owner"] = None
        cs["rev"] = cs.get("rev", 0) + 1
        cs["updated_at"] = _now()

    update(book_dir, fn)
    print(f"已释放 {ch}")
    return 0


def _snapshot(book_dir: Path, ch: str, cs: dict, error: str) -> None:
    """repair 前把当前稿留档，供回滚。"""
    book = _book_meta(book_dir)
    src = _paths(book_dir, book)["chapters"] / f"{ch}.md"
    if not src.exists():
        return
    attempt = cs.get("attempts", 0) + 1
    hist_dir = book_dir / ".book" / "history" / ch
    hist_dir.mkdir(parents=True, exist_ok=True)
    dst = hist_dir / f"attempt-{attempt}.md"
    if dst.exists():                     # 回滚后再 repair，不覆盖旧快照
        dst = hist_dir / f"attempt-{attempt}-{datetime.now():%H%M%S}.md"
    shutil.copy2(src, dst)
    cs.setdefault("history", []).append({
        "attempt": attempt,
        "path": str(dst.relative_to(book_dir)).replace("\\", "/"),
        "at": _now(),
        "error": error or "",
    })


def cmd_set(book_dir: Path, ch: str, status: str, owner: str,
            error: str, expect_rev: int | None, force_book: bool) -> int:
    if status not in STATUSES:
        sys.exit(f"非法状态：{status}（可选：{'/'.join(STATUSES)}）")

    def fn(st: dict) -> None:
        cs = st["chapters"].setdefault(
            ch, {"status": "pending", "attempts": 0, "owner": None, "rev": 0})
        if expect_rev is not None and cs.get("rev", 0) != expect_rev:
            sys.exit(f"{ch} 的 rev 已变为 {cs.get('rev', 0)}（期望 {expect_rev}），"
                     f"说明有别人先改了。重新读一次再试。")
        if cs.get("owner") and owner and cs["owner"] != owner and \
                cs.get("status") in ("writing", "checking", "repair") and not force_book:
            sys.exit(f"{ch} 正被 {cs['owner']} 写（status={cs.get('status')}），拒绝越权修改。")

        if status == "repair":
            _snapshot(book_dir, ch, cs, error)
            cs["attempts"] = cs.get("attempts", 0) + 1
            if cs["attempts"] > REPAIR_MAX:
                cs["status"] = "failed"
                cs["rev"] = cs.get("rev", 0) + 1
                cs["updated_at"] = _now()
                cs["last_error"] = (error + "；" if error else "") + \
                    f"repair 已达 {cs['attempts']} 次，转人工（问题在章纲，不在写手）"
                return

        cs["status"] = status
        cs["rev"] = cs.get("rev", 0) + 1
        cs["updated_at"] = _now()
        if owner:
            cs["owner"] = owner
        if error:
            cs["last_error"] = error

    update(book_dir, fn)
    st = load_state(book_dir)
    cs = st["chapters"].get(ch, {})
    print(f"{ch} → {cs.get('status')}（attempts {cs.get('attempts', 0)}，rev {cs.get('rev', 0)}）")
    return 0


def cmd_rollback(book_dir: Path, ch: str) -> int:
    st = load_state(book_dir)
    cs = st["chapters"].get(ch, {})
    hist = cs.get("history") or []
    if not hist:
        sys.exit(f"{ch} 没有历史快照，无法回滚")
    last = hist[-1]
    src = book_dir / last["path"]
    if not src.exists():
        sys.exit(f"快照文件不存在：{src}")
    book = _book_meta(book_dir)
    dst = _paths(book_dir, book)["chapters"] / f"{ch}.md"
    shutil.copy2(src, dst)

    def fn(s: dict) -> None:
        c = s["chapters"].setdefault(ch, {})
        c["history"] = [h for h in (c.get("history") or []) if h.get("attempt") != last["attempt"]]
        c["attempts"] = max(0, c.get("attempts", 1) - 1)
        c["status"] = "repair"
        c["rev"] = c.get("rev", 0) + 1
        c["updated_at"] = _now()

    update(book_dir, fn)
    print(f"已把 {ch} 回滚到 {last['path']}（status=repair，可继续修）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="章节状态机与多作者协作")
    ap.add_argument("--book", required=True)
    ap.add_argument("--init", action="store_true", help="按 dag 初始化章节状态")
    ap.add_argument("--report", action="store_true", help="输出状态报告与下一步")
    ap.add_argument("--claim", metavar="CH", help="认领一章")
    ap.add_argument("--release", metavar="CH", help="释放一章")
    ap.add_argument("--set", nargs=2, metavar=("CH", "STATUS"), help="设置章节状态")
    ap.add_argument("--rollback", metavar="CH", help="回滚到最近一次 repair 快照")
    ap.add_argument("--owner", default="", help="写手标识")
    ap.add_argument("--error", default="", help="记录错误信息")
    ap.add_argument("--expect-rev", type=int, default=None, help="乐观并发：期望的 rev")
    ap.add_argument("--force", action="store_true", help="抢占已被占用的章")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--calibrate", action="store_true",
                    help="用已完成章校准文风指纹（SPEC §7.2）")
    ap.add_argument("--from", dest="cal_from", default="",
                    help="配合 --calibrate：指定基准章，逗号分隔，缺省用全部已有章")
    args = ap.parse_args()

    root = Path(args.book).resolve()
    if not (root / "book.yaml").exists():
        sys.exit(f"找不到 {root / 'book.yaml'}")

    if args.init:
        return cmd_init(root, args.force)
    if args.calibrate:
        chs = [x.strip() for x in args.cal_from.split(",") if x.strip()]
        return cmd_calibrate(root, chs)
    if args.report:
        return cmd_report(root, args.json)
    if args.claim:
        if not args.owner:
            sys.exit("--claim 需要 --owner")
        return cmd_claim(root, args.claim, args.owner, args.force)
    if args.release:
        return cmd_release(root, args.release, args.owner)
    if args.rollback:
        return cmd_rollback(root, args.rollback)
    if args.set:
        ch, status = args.set
        return cmd_set(root, ch, status, args.owner,
                       args.error, args.expect_rev, args.force)

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
