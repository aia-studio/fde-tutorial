#!/usr/bin/env python3
"""init_book.py —— 生成书项目骨架。

做三件事：
1. 从 templates/book/book.yaml 渲染出 book.yaml（保留注释）
2. 建目录结构
3. 初始化四本账（glossary / claims / promises / ladder）与 state.json

用法:
    python scripts/init_book.py --dest ../my-book --title "AI 应用评测入门" \
        --genre practical --spine capstone --spine-name 客服工单助手 \
        --chapters 10 --words 4500,6000
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：python -m pip install pyyaml")

HERE = Path(__file__).resolve().parent.parent
TEMPLATE = HERE / "templates" / "book" / "book.yaml"
SCHEMA = HERE / "schemas" / "book.schema.json"

DIRS = [
    "04-chapter-plans", "chapters", "src", "src/common", "src/data",
    "figures", "assets", "dep-brief", "final", ".book", ".book/contracts",
]

MERMAID = HERE / "mermaid.config.json"
PRESETS_FILE = HERE / "genres" / "presets.yaml"

POSITIONING = """# 定位与方向

> 阶段 0 产物 · 本书一切内容的最终裁判标准

## 一句话定位

（这本书给谁看，用一句话说清）

## 目标读者

- **画像**：
- **前置知识（最低门槛）**：
- **典型场景**：
- **反面读者（不在服务范围内）**：

## 学习目标（读完能做到什么）

用可验收的动词开头：能搭出 / 能判断 / 能排查 / 能交付。
「理解」「掌握」不合格——它们无法验收。

1.
2.
3.

## 范围边界

**这本书讲什么：**

**这本书不讲什么（至少 5 条）：**
-
-

## 与同类的差异

（一句话。答「更系统」「更实战」不算答案。）

## 技术栈与版本

| 类别 | 选型 | 说明 |
| --- | --- | --- |
"""

STUBS = {
    "01-outline.md": """# 篇级大纲

> 阶段 1 产物 · 3–9 篇，每篇一句话说清「这一篇解决什么」

## 第 1 篇

解决：

包含章节：
""",
    "02-toc.md": """# 章级目录

> 阶段 1 产物 · 每章一行，五个字段缺一不可

| 章 | 标题 | 一句话目标 | 字数 | 难度 | 交付物 |
| --- | --- | --- | --- | --- | --- |
| 01 | | | | 2 | |
""",
}

GITIGNORE = """__pycache__/
*.pyc
.env
.book/*.tmp
src/**/.venv/
"""

# 评审 A5：03-constitution.md 引用的 progress.md 此前无模板、无工具。
PROGRESS = """# 进度与解冻记录

> 阶段推进与宪法冻结/解冻的流水账。`state.py --freeze / --unfreeze / --phase`
> 会写进 .book/state.json；解冻记录同时自动追加到本文件。

| 时间 | 事件 | 原因 / 影响 |
| --- | --- | --- |
"""


def set_line(text: str, key: str, value: str) -> str:
    """替换首个 `key: ...` 行，保留缩进与其余内容。"""
    pat = re.compile(rf"^(\s*){re.escape(key)}:.*$", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return text + f"\n{key}: {value}\n"
    return text[:m.start()] + f"{m.group(1)}{key}: {value}" + text[m.end():]


def drop_line(text: str, key: str) -> str:
    return re.sub(rf"^\s*{re.escape(key)}:.*\n?", "", text, count=1, flags=re.MULTILINE)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成书项目骨架")
    ap.add_argument("--dest", required=True, help="目标目录（不存在则创建）")
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", default="待填")
    ap.add_argument("--license", default="CC BY-NC-SA 4.0")
    ap.add_argument("--genre", default="practical", help="单值或用逗号分隔的列表")
    ap.add_argument("--lang", default="zh-CN", choices=["zh-CN", "zh-TW"],
                    help="评审 C1：统计口径中文特化，暂不开放 en")
    ap.add_argument("--preset", default="",
                    help="混合 genre 预设：project-practical / principle-practical / interview-principle")
    ap.add_argument("--spine", default="running-example",
                    choices=["capstone", "running-example", "none"])
    ap.add_argument("--spine-name", default="")
    ap.add_argument("--chapters", type=int, default=10)
    ap.add_argument("--words", default="4500,6000", help="每章字数范围，如 4500,6000")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="目标非空时仍继续")
    args = ap.parse_args()

    dest = Path(args.dest).resolve()
    if dest.exists() and any(dest.iterdir()) and not args.force:
        sys.exit(f"{dest} 非空。确认要覆盖请加 --force")
    dest.mkdir(parents=True, exist_ok=True)

    # 1) 目录 + 渲染配置
    for d in DIRS:
        (dest / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(MERMAID, dest / "mermaid.config.json")

    # 2) book.yaml
    text = TEMPLATE.read_text(encoding="utf-8")
    if args.preset:
        presets = (yaml.safe_load(PRESETS_FILE.read_text(encoding="utf-8")) or {}).get("presets", {})
        if args.preset not in presets:
            sys.exit(f"未知 preset：{args.preset}（可选：{'、'.join(presets)}）")
        genres = list(presets[args.preset]["genre"])
    else:
        genres = [g.strip() for g in args.genre.split(",") if g.strip()]
    # 评审 C4：可用 genre 从目录自动发现，不再只认四种硬编码值
    valid = {p.stem for p in (HERE / "genres").glob("*.yaml")
             if p.stem not in {"_core", "presets"}}
    unknown = [g for g in genres if g not in valid]
    if unknown:
        sys.exit(f"找不到 genre：{'、'.join(unknown)}（可用：{'、'.join(sorted(valid))}；"
                 f"新增体裁见 genres/README.md）")
    genre_val = genres[0] if len(genres) == 1 else "[" + ", ".join(genres) + "]"
    if "project" in genres and args.spine != "capstone":
        print("! genre 含 project，spine 已强制为 capstone", file=sys.stderr)
        args.spine = "capstone"

    text = set_line(text, "title", args.title)
    text = set_line(text, "author", args.author)
    text = set_line(text, "license", args.license)
    text = set_line(text, "updated", f'"{date.today():%Y-%m}"')
    text = set_line(text, "genre", genre_val)
    text = set_line(text, "lang", args.lang)
    text = set_line(text, "spine", args.spine)
    text = set_line(text, "chapters", str(args.chapters))
    text = set_line(text, "words_per_chapter", f"[{args.words}]")
    text = set_line(text, "concurrency", str(args.concurrency))
    if args.spine == "capstone":
        if not args.spine_name:
            sys.exit("spine=capstone 必须给 --spine-name")
        text = set_line(text, "spine_name", args.spine_name)
    else:
        text = drop_line(text, "spine_name")
    (dest / "book.yaml").write_text(text, encoding="utf-8")

    # 3) schema 校验（有 jsonschema 就校，没有就给提示）
    book = yaml.safe_load(text)
    try:
        import jsonschema
        jsonschema.validate(book, json.loads(SCHEMA.read_text(encoding="utf-8")))
        print("book.yaml 通过 schema 校验")
    except ImportError:
        print("（未安装 jsonschema，跳过结构校验）")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"book.yaml 不符合 schema：{e}")

    # 4) 文档骨架
    (dest / "00-positioning.md").write_text(POSITIONING, encoding="utf-8")
    for name, body in STUBS.items():
        (dest / name).write_text(body, encoding="utf-8")
    (dest / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (dest / ".gitignore").write_text(GITIGNORE, encoding="utf-8")

    # 5) 四本账 + 状态
    (dest / ".book" / "glossary.json").write_text(
        json.dumps({"version": 1, "terms": []}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    for f in ["claims.jsonl", "promises.jsonl", "ladder.jsonl"]:
        (dest / ".book" / f).write_text("", encoding="utf-8")

    state = {
        "version": 2,
        "created": date.today().isoformat(),
        "phase": "0-intake",
        "frozen": {"positioning": False, "toc": False, "constitution": False},
        "frozen_meta": {},
        "freeze_log": [],
        "phase_log": [],
        "chapters": {},
    }
    (dest / ".book" / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6) 文风指纹初值：直接复制主 genre 的 fingerprint，标 source，第一波后校准覆盖
    genre_cfg = yaml.safe_load(
        (HERE / "genres" / f"{genres[0]}.yaml").read_text(encoding="utf-8")) or {}
    (dest / ".book" / "style-fingerprint.json").write_text(
        json.dumps({"source": "genre-default", "calibrated_at": None,
                    "metrics": genre_cfg.get("fingerprint", {})},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    (dest / "src" / "common" / "README.md").write_text(
        "# 公共模块\n\n只放纯功能，不放章节业务语义。\n"
        "任何修改都要全量重验（所有章重跑闸门）。\n", encoding="utf-8")
    (dest / "src" / "data" / "README.md").write_text(
        "# 示例数据\n\n只放生成脚本，不放数据本体。\n"
        "每个脚本固定 SEED，并在开头 random.seed(SEED)。\n", encoding="utf-8")

    print(f"\n已生成 {dest}")
    print("下一步：填 00-positioning.md → 写 02-toc.md 与 04-chapter-plans/ → "
          "python scripts/plan.py --book .")
    return 0


if __name__ == "__main__":
    sys.exit(main())
