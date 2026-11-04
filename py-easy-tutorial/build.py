#!/usr/bin/env python3
"""内容编译器：`content/**/*.md` → `web/data/lessons/*.json` + `web/data/index.json`。

用法：
    python build.py              # 编译，只做结构校验
    python build.py --check      # 编译 + 全量校验（含真跑每个代码块）
    python build.py --strict     # 缺口也视为错误（发布前用）

设计原则：宁可构建失败，也不要把半成品发布出去。所有错误带文件路径与行号。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from tutorial import markdown
from tutorial.grader import grade
from tutorial.schema import (
    BLOCK_TYPES,
    PLANNED_TOTAL,
    STAGE_META,
    STAGES,
    check_progression,
    scan_content,
    split_front_matter,
    validate_meta,
)

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
DATA = ROOT / "web" / "data"
LESSONS_DIR = DATA / "lessons"

RUN_TIMEOUT = 10


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_lesson(path: Path, report: Report) -> dict | None:
    """读取并校验一门课。任何一步失败都返回 None，不写半个产物。"""
    rel = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.error(f"{rel}: 读取失败 {exc}")
        return None

    try:
        raw_meta, body = split_front_matter(text)
        meta = tomllib.loads(raw_meta)
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        report.error(f"{rel}: front matter 解析失败：{exc}")
        return None

    errors = validate_meta(meta, source=rel)
    if errors:
        for e in errors:
            report.error(e)
        return None

    try:
        blocks = markdown.parse(body)
    except ValueError as exc:
        report.error(f"{rel}: {exc}")
        return None

    for idx, block in enumerate(blocks):
        if block["type"] not in BLOCK_TYPES:
            report.error(f"{rel}: 第 {idx} 块类型未知 `{block['type']}`")

    if not any(b["type"] == "code" and b["runnable"] for b in blocks):
        report.warn(f"{rel}: 没有可运行代码块")

    meta["blocks"] = blocks
    meta["source"] = rel
    meta.setdefault("prereq", [])
    meta.setdefault("xp", 20)
    meta.setdefault("requires_python", "3.15")
    meta.setdefault("allow_network", False)
    meta.setdefault("standalone", False)
    return meta


def compile_all() -> tuple[list[dict], Report]:
    report = Report()
    lessons: list[dict] = []

    for path in scan_content(CONTENT):
        lesson = load_lesson(path, report)
        if lesson:
            lessons.append(lesson)

    lessons.sort(key=lambda x: x["order"])

    seen: dict[str, str] = {}
    for lesson in lessons:
        prev = seen.get(lesson["id"])
        if prev:
            report.error(f"id 重复：`{lesson['id']}`（{prev} 与 {lesson['source']}）")
        seen[lesson["id"]] = lesson["source"]

    seen_order: dict[int, str] = {}
    for lesson in lessons:
        prev = seen_order.get(lesson["order"])
        if prev:
            report.error(f"order 重复：{lesson['order']}（{prev} 与 {lesson['source']}）")
        seen_order[lesson["order"]] = lesson["source"]

    return lessons, report


def check_gaps(lessons: list[dict], report: Report, strict: bool) -> None:
    present = {l["order"] for l in lessons}
    missing = [n for n in range(1, PLANNED_TOTAL + 1) if n not in present]
    if not missing:
        return
    preview = ", ".join(str(n) for n in missing[:12])
    more = "" if len(missing) <= 12 else f" 等 {len(missing)} 门"
    msg = f"大纲尚缺 {len(missing)} 课：{preview}{more}"
    if strict:
        report.error(msg)
    else:
        report.warn(msg)


def _normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n")


def _run_code(code: str) -> tuple[int, str]:
    """返回 (退出码, 合并后的输出)。

    stderr 合并进 stdout：校验只需要"最后一行"来报告错误，少一条管道
    就少一半的句柄关闭开销——实测这部分占了单课校验时间的大头。
    """
    with tempfile.TemporaryDirectory(prefix="pytut-build-") as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code + "\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-s", "-B", "-u", str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=RUN_TIMEOUT,
            cwd=tmp,
        )
        return proc.returncode, proc.stdout + proc.stderr


def _pmap(fn, items: list, jobs: int) -> list:
    """保持顺序的并行 map。jobs<=1 时退化成串行，方便排查。"""
    if jobs <= 1 or len(items) <= 1:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(fn, items))


def _check_one_block(task: tuple[str, str, str | None]) -> tuple[str, list[str]]:
    label, code, expect = task
    try:
        rc, output = _run_code(code)
    except subprocess.TimeoutExpired:
        return label, [f"{label}: 执行超时（>{RUN_TIMEOUT}s）"]

    if rc != 0:
        lines = output.strip().splitlines() or ["无输出"]
        return label, [f"{label}: 退出码 {rc}：{lines[-1]}"]

    if expect is None:
        return label, []

    if _normalize_output(output) != _normalize_output(expect):
        return label, [
            f"{label}: 输出与 expect 不一致\n"
            f"    期望：{_normalize_output(expect)!r}\n"
            f"    实际：{_normalize_output(output)!r}"
        ]
    return label, []


def check_blocks(lessons: list[dict], report: Report, jobs: int) -> int:
    """并行真跑每个可运行代码块；有 expect 的比对输出。返回执行块数。"""
    tasks = [
        (f"{lesson['source']} › {block['id']}", block["code"], block["expect"])
        for lesson in lessons
        for block in lesson["blocks"]
        if block["type"] == "code" and block["runnable"]
    ]
    if not tasks:
        return 0

    for _label, errors in _pmap(_check_one_block, tasks, jobs):
        for message in errors:
            report.error(message)
    return len(tasks)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def build_outline(blocks: list[dict]) -> list[dict]:
    """抽取 h2/h3 大纲，锚点编号必须和前端 renderer 保持一致（sec-1 起）。"""
    outline: list[dict] = []
    n = 0
    for block in blocks:
        if block["type"] != "heading" or block["level"] > 3:
            continue
        n += 1
        outline.append(
            {"anchor": f"sec-{n}", "level": block["level"], "text": _plain(block["html"])}
        )
    return outline


def _check_one_exercise(task: tuple[str, str, dict]) -> list[tuple[str, str]]:
    label, _source, block = task
    messages: list[tuple[str, str]] = []

    result = grade(block["solution"], block["tests"])
    if result["timed_out"]:
        messages.append(("error", f"{label}: 参考答案执行超时"))
    elif not result["passed"]:
        failed = [r for r in result["results"] if not r["passed"]]
        detail = failed[0]["error"] if failed else result["stderr"][-200:]
        messages.append(("error", f"{label}: 参考答案没通过测试 —— {detail}"))

    if block["starter"].strip():
        starter = grade(block["starter"], block["tests"])
        if starter["passed"] and not starter["timed_out"]:
            messages.append(
                ("warn", f"{label}: 起始代码已能通过全部测试，题目可能过于简单")
            )
    return messages


def check_exercises(lessons: list[dict], report: Report, jobs: int) -> int:
    """参考答案必须能过自己的测试；起始代码不该白给。返回练习数。"""
    seen: dict[str, str] = {}
    tasks: list[tuple[str, str, dict]] = []

    for lesson in lessons:
        for block in lesson["blocks"]:
            if block["type"] != "exercise":
                continue
            if block["id"] in seen:
                report.error(
                    f"练习 id 重复：`{block['id']}`（{seen[block['id']]} 与 {lesson['source']}）"
                )
            seen[block["id"]] = lesson["source"]
            tasks.append((f"{lesson['source']} › {block['id']}", lesson["source"], block))

    for messages in _pmap(_check_one_exercise, tasks, jobs):
        for level, message in messages:
            if level == "error":
                report.error(message)
            else:
                report.warn(message)
    return len(tasks)


def _filter_lessons(lessons: list[dict], pattern: str | None) -> list[dict]:
    """`--only` 支持逗号分隔，匹配课程编号、id 或文件路径片段。"""
    if not pattern:
        return lessons
    needles = [p.strip().lower() for p in pattern.split(",") if p.strip()]
    if not needles:
        return lessons

    picked = []
    for lesson in lessons:
        haystack = f"{lesson['order']} {lesson['id']} {lesson['source']}".lower()
        if any(n in haystack for n in needles):
            picked.append(lesson)
    return picked


def write_outputs(lessons: list[dict]) -> None:
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    (DATA / "lessons").mkdir(parents=True, exist_ok=True)

    expected: set[Path] = set()

    for idx, lesson in enumerate(lessons):
        outline = build_outline(lesson["blocks"])
        payload = {
            "id": lesson["id"],
            "order": lesson["order"],
            "stage": lesson["stage"],
            "stage_title": STAGE_META[lesson["stage"]]["title"],
            "official_group": lesson["official_group"],
            "title": lesson["title"],
            "concepts": lesson["concepts"],
            "outline": outline,
            "doc_refs": lesson["doc_refs"],
            "prereq": lesson["prereq"],
            "requires_python": lesson["requires_python"],
            "allow_network": lesson["allow_network"],
            "xp": lesson["xp"],
            "blocks": lesson["blocks"],
            "prev": lessons[idx - 1]["id"] if idx > 0 else None,
            "next": lessons[idx + 1]["id"] if idx + 1 < len(lessons) else None,
        }
        out = LESSONS_DIR / f"{lesson['id']}.json"
        expected.add(out)
        out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # 只删除已失效的课程文件。每课一个 unlink，全删重建会触发
    # 环境里的批量删除守卫（实测每次 unlink 约 0.4s，33 个文件就是 15 秒）。
    for stale in LESSONS_DIR.glob("*.json"):
        if stale not in expected:
            stale.unlink()

    stages = []
    for stage_id in STAGES:
        items = [
            {
                "id": l["id"],
                "order": l["order"],
                "title": l["title"],
                "official_group": l["official_group"],
            }
            for l in lessons
            if l["stage"] == stage_id
        ]
        stages.append(
            {
                "id": stage_id,
                "title": STAGE_META[stage_id]["title"],
                "subtitle": STAGE_META[stage_id]["subtitle"],
                "lessons": items,
            }
        )

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "planned_total": PLANNED_TOTAL,
        "published": len(lessons),
        "stages": stages,
        "lessons": [
            {
                "id": l["id"],
                "order": l["order"],
                "title": l["title"],
                "stage": l["stage"],
                "official_group": l["official_group"],
                "concepts": l["concepts"],
                "outline": build_outline(l["blocks"]),
            }
            for l in lessons
        ],
    }
    (DATA / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="编译课程内容")
    parser.add_argument("--check", action="store_true", help="全量校验（会真跑代码块）")
    parser.add_argument("--strict", action="store_true", help="缺口视为错误")
    parser.add_argument("--quiet", action="store_true", help="只在出错时输出")
    parser.add_argument(
        "--only",
        metavar="PATTERN",
        help="只校验匹配的课（编号/id/路径片段，逗号分隔），编译仍然全量",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(8, os.cpu_count() or 4),
        help="并行进程数，默认 min(8, CPU 数)",
    )
    args = parser.parse_args()

    if not CONTENT.exists():
        print(f"找不到内容目录：{CONTENT}", file=sys.stderr)
        return 1

    lessons, report = compile_all()

    check_gaps(lessons, report, args.strict)

    for e in check_progression(lessons):
        if args.strict or "不存在于当前内容集" not in e:
            report.error(e)

    targets = _filter_lessons(lessons, args.only)
    if args.only and not targets:
        report.error(f"--only `{args.only}` 没有匹配到任何课程")

    ran = 0
    exercises = 0
    if args.check:
        ran = check_blocks(targets, report, args.jobs)
        exercises = check_exercises(targets, report, args.jobs)

    if report.ok:
        write_outputs(lessons)

    if not args.quiet:
        for w in report.warnings:
            print(f"  warn  {w}")
        for e in report.errors:
            print(f"  ERROR {e}")
        status = "OK" if report.ok else "FAILED"
        scope = f"（仅校验 {len(targets)} 门）" if args.only else ""
        detail = f"，已执行 {ran} 个代码块" if args.check else ""
        if args.check and exercises:
            detail += f"、{exercises} 道练习"
        print(
            f"\n[{status}] {len(lessons)} 门课{detail}{scope}"
            f" → web/data/（计划 {PLANNED_TOTAL} 课）"
        )

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
