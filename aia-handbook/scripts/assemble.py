#!/usr/bin/env python3
"""assemble.py —— 把散落的章节装配成一本自包含的书。

产出 `final/`：
    生成：README、前言终稿、章节（图路径重写）、附录 A–E、结语、LICENSE
    复制：assets/ → final/assets/（自包含，整包可独立分发）

装配后自动扫描 final/ 内图片相对路径，有不可达或残留 `../` 即报错。

用法:
    python scripts/assemble.py --book <书目录>
    python scripts/assemble.py --book <书目录> --quiet
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
except ImportError:  # pragma: no cover
    sys.exit("需要 pyyaml：python -m pip install pyyaml")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

GEN_FILES = {"README.md", "00-preface.md", "99-afterword.md", "LICENSE"}
IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
# 装配产物里不该出现的占位写法（中英文都算）
PLACEHOLDER_WORDS = ("（待补", "（待定", "待补充", "FIXME", "XXX", "此处省略")
# 评审 C3：FAQ 按骨架段 id 收集，不再写死「常见坑 / 常见问题」两个中文标题。
FAQ_SKELETON_IDS = {"pitfalls", "mistakes", "risks", "boundary", "retro"}


class PromisesOpenError(RuntimeError):
    """承诺账本仍有 open 时拒绝产出 final/（评审 A1）。"""


def _open_promises(repo: check.Repo) -> list[dict]:
    return [p for p in repo.ledger.get("promises", []) if p.get("status") == "open"]


# ---------------------------------------------------------------- 工具

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _strip_fm(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            return text[end + 4:]
    return text


def _rewrite_assets(text: str) -> str:
    """`../assets/` 或更深层 → `assets/`，配合 final/assets/ 自包含。"""
    return re.sub(r"\]\((?:\.\./)+assets/", "](assets/", text)


def _split_h2(md: str) -> dict[str, str]:
    """按 H2 切段，key 为标题，value 为正文。"""
    out: dict[str, str] = {}
    cur = ""
    buf: list[str] = []
    for ln in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            if cur:
                out[cur.strip()] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        elif cur:
            buf.append(ln)
    if cur:
        out[cur.strip()] = "\n".join(buf).strip()
    return out


def _annotation_meanings(repo: check.Repo) -> dict[str, str]:
    """从 genre 的 md 表格里抽 【标注】→ 含义。

    评审 C3：混合 genre 时合并**所有参与类型**的 md，副体裁的标注不再显示「（待补含义）」。
    """
    meanings: dict[str, str] = {}
    files = [check.GENRE_DIR / "_core.md"] + [
        check.GENRE_DIR / f"{g}.md" for g in repo.cfg["genre_list"]]
    for f in files:
        if not f.exists():
            continue
        for ln in _read(f).splitlines():
            m = re.match(r"^\|\s*【(.+?)】\s*\|\s*(.+?)\s*\|\s*$", ln)
            if m:
                meanings[m.group(1)] = m.group(2)
    return meanings


def _path_marks(ch: check.Chapter) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for sec in ch.h3:
        mark = "必读"
        for ln in sec.body:
            m = re.match(r"^>\s*路径[：:]\s*(必读|选读|参考)", ln.strip())
            if m:
                mark = m.group(1)
                break
        out.append((sec.title, mark))
    return out


def _toc_rows(repo: check.Repo) -> list[tuple[str, str, str]]:
    """优先 02-toc.md 的表格，缺失时从章纲兜底。"""
    rows: list[tuple[str, str, str]] = []
    toc = _read(repo.root / "02-toc.md")
    for ln in toc.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.match(r"^\d{2}$", cells[0]):
            rows.append((f"ch{cells[0]}", cells[1], cells[2]))
    if rows:
        return rows
    for name in sorted(repo.plans):
        p = repo.plans[name]
        rows.append((name, str(p.get("title", "")), str(p.get("deliverable", ""))))
    return rows


def _stats(chapters: list[check.Chapter]) -> dict[str, int]:
    return {
        "chapters": len(chapters),
        "words": sum(c.han_count for c in chapters),
        "figures": sum(len(c.images) for c in chapters),
        "code_blocks": sum(len(c.code_blocks) for c in chapters),
        "code_lines": sum(len(b) for c in chapters for b in c.code_blocks),
    }


# ---------------------------------------------------------------- 生成件

def _preface(repo: check.Repo, chapters: list[check.Chapter],
             stats: dict[str, int], paths: dict[str, list[tuple[str, str]]]) -> str:
    book = repo.book
    pos = _split_h2(_read(repo.root / "00-positioning.md"))
    aud = book.get("audience", {})
    meanings = _annotation_meanings(repo)
    used = sorted({a for c in chapters for a in c.annotations})

    def sect(key: str, fallback: str) -> str:
        for k, v in pos.items():
            if key in k:
                return v or fallback
        return fallback

    # 「范围边界」里同时有「讲什么」与「不讲什么」，前言只取后者
    scope = sect("范围边界", "（待补：见 00-positioning.md 的范围边界）")
    marker = re.search(r"\*\*这本书不讲什么[^*]*\*\*", scope)
    if marker:
        scope = scope[marker.end():].lstrip("：: \n")

    quick = [f"Ch{n[-2:]} {next((r[1] for r in _toc_rows(repo) if r[0] == n), '')}"
             for n in sorted(paths) if any(m == "必读" for _, m in paths[n])]

    lines = [
        "# 前言", "",
        "## 这本书给谁看", "",
        sect("目标读者", f"- 画像：{aud.get('who', '')}\n"
                         f"- 前置知识：{'、'.join(aud.get('prerequisite', [])) or '无'}"), "",
        "## 读完你能做什么", "",
        sect("学习目标", "（待补：见 00-positioning.md 的学习目标）"), "",
        "## 这本书不讲什么", "",
        scope, "",
        "## 怎么读", "",
        "### 快速路径", "",
        "必读小节 + 每章小结：" + " → ".join(quick) if quick else "（暂无路径标注）", "",
        "### 完整路径", "",
        "按章顺序通读。", "",
        "### 复习路径", "",
        "必读小节 + 各章自查清单 + 常见坑。", "",
        "## 标注体系", "",
        "| 标注 | 含义 |", "| --- | --- |",
    ]
    if used:
        for a in used:
            lines.append(f"| 【{a}】 | {meanings.get(a, '（待补含义）')} |")
    else:
        lines.append("| — | 本书未使用自定义标注 |")
    stack = book.get("stack", {}) or {}
    entry = _run_entry(repo)
    if entry:
        lines += [
            "", "## 代码怎么跑", "",
            "```bash",
            f"cd {_book_slug(repo)}",
            entry,
            "```", "",
            f"- Mock 模式：{'开启，没有 API Key 也能跑通全书示例' if stack.get('mock') else '关闭，需要真实依赖'}",
        ]
        if (repo.root / "versions.lock").exists():
            lines.append("- 版本基准：见附录 D 与 `versions.lock`")
    else:
        lines += [
            "", "## 代码约定", "",
            "- 本书示例以伪码与结构表为主，不提供可运行工程。",
            f"- 语言与版本：{stack.get('python', '与版本弱相关')}。",
        ]
    lines += [
        "", "## 本书规模", "",
        f"- 章节：{stats['chapters']} 章",
        f"- 正文：约 {stats['words']:,} 字",
        f"- 图：{stats['figures']} 张",
        f"- 代码：{stats['code_blocks']} 段 / {stats['code_lines']} 行", "",
    ]
    return "\n".join(lines)


def _run_entry(repo: check.Repo) -> str:
    """找第一章里真能 `python -m` 跑的模块；没有就返回空串。

    旧模板无条件写 `python -m ch01.demo`，无代码的书（如面试本）会被教着跑不存在的模块。
    """
    src = repo.root / "src"
    if not src.is_dir():
        return ""
    for ch in sorted(p for p in src.iterdir() if p.is_dir() and p.name.startswith("ch")):
        if not re.fullmatch(r"ch\d{2}", ch.name):
            continue
        for py in sorted(ch.glob("*.py")):
            txt = py.read_text(encoding="utf-8", errors="ignore")
            if "__main__" in txt:
                return f"python -m {ch.name}.{py.stem}"
    return ""


def _book_slug(repo: check.Repo) -> str:
    """包目录名。书名里带冒号/斜杠不能直接当路径，用项目目录名最稳。"""
    return repo.root.name


def _readme(repo: check.Repo, stats: dict[str, int]) -> str:
    book = repo.book
    pos = _split_h2(_read(repo.root / "00-positioning.md"))
    one = next((v for k, v in pos.items() if "一句话定位" in k), "") or \
        f"一本关于 {book.get('title', '')} 的技术书。"
    rows = _toc_rows(repo)
    slug = _book_slug(repo)
    entry = _run_entry(repo)
    lines = [
        f"# {book.get('title', '')}", "",
        one.strip(), "",
        "## 怎么读", "",
        "- 快速路径：必读小节 + 每章小结",
        "- 完整路径：顺序读",
        "- 复习路径：自查清单 + 常见坑", "",
        "## 目录", "",
        "| 章 | 标题 | 一句话 |", "| --- | --- | --- |",
    ]
    for name, title, one_liner in rows:
        lines.append(f"| {name[-2:]} | {title} | {one_liner} |")
    if entry:
        lines += [
            "", "## 怎么跑代码", "",
            "```bash",
            f"cd {slug}",
            entry,
            "```", "",
            f"- Mock 模式：{'开启，没有 API Key 也能跑通' if (book.get('stack') or {}).get('mock') else '关闭，需要真实依赖'}",
        ]
        if (repo.root / "versions.lock").exists():
            lines.append("- 版本基准：见 `versions.lock`")
    else:
        lines += ["", "## 关于代码", "",
                  "本书不提供可运行的示例工程，示例是伪码与结构表。" if not (repo.root / "src" / "ch01").is_dir()
                  else "示例代码见 `src/`，按章组织。"]
    lines += ["", f"> 全书 {stats['chapters']} 章，约 {stats['words']:,} 字，"
                  f"{stats['figures']} 张图。", ""]
    return "\n".join(lines)


def _appendix_glossary(repo: check.Repo) -> str:
    terms = [t for t in repo.ledger.get("glossary", []) if isinstance(t, dict)]
    lines = ["# 附录 A 术语表", "",
             "| id | 中文 | English | 定义 | 首现章 |",
             "| --- | --- | --- | --- | --- |"]
    if terms:
        for t in sorted(terms, key=lambda x: str(x.get("id", ""))):
            lines.append(f"| {t.get('id', '')} | {t.get('zh', '')} | {t.get('en', '')} "
                         f"| {t.get('def', '')} | {t.get('first_chapter', '')} |")
    else:
        lines.append("| — | （术语账本为空） | | | |")
    return "\n".join(lines) + "\n"


def _appendix_refs(repo: check.Repo) -> str:
    seen: list[str] = []
    for c in repo.ledger.get("claims", []):
        s = str(c.get("source", "")).strip()
        if s and s not in seen:
            seen.append(s)
    lines = ["# 附录 B 参考文献", ""]
    if seen:
        for i, s in enumerate(seen, 1):
            lines.append(f"{i}. {s}")
    else:
        lines.append("（事实账本为空，暂无参考文献）")
    return "\n".join(lines) + "\n"


def _appendix_paths(repo: check.Repo, paths: dict[str, list[tuple[str, str]]]) -> str:
    lines = ["# 附录 C 阅读路径", "",
             "## 快速路径", "", "只读标为「必读」的小节，再看每章小结。", "",
             "| 章 | 必读小节 |", "| --- | --- |"]
    for name in sorted(paths):
        must = [t for t, m in paths[name] if m == "必读"]
        lines.append(f"| {name[-2:]} | {'；'.join(must) if must else '（未标注）'} |")
    lines += ["", "## 完整路径", "", "按章顺序全部通读。", "",
              "## 复习路径", "", "必读小节 + 各章自查清单 + 常见坑。", "",
              "## 小节标注明细", "",
              "| 章 | 小节 | 路径 |", "| --- | --- | --- |"]
    for name in sorted(paths):
        for title, mark in paths[name]:
            lines.append(f"| {name[-2:]} | {title} | {mark} |")
    return "\n".join(lines) + "\n"


def _appendix_toolbox(repo: check.Repo) -> str:
    """评审 C3：用途字典下沉到 genres/*.yaml 的 tool_purposes，换主题不再改脚本。"""
    stack = repo.book.get("stack", {}) or {}
    purposes = {str(k).lower(): str(v) for k, v in
                (repo.cfg.get("tool_purposes") or {}).items()}
    lines = ["# 附录 D 工具箱", "",
             "| 类别 | 选型 | 用途 |", "| --- | --- | --- |"]
    for k, v in stack.items():
        purpose = purposes.get(str(k).lower())
        lines.append(f"| {k} | {v} | {purpose or '—'} |")
    reqs = sorted((repo.root / "src").rglob("requirements.txt")) if (repo.root / "src").is_dir() else []
    if reqs:
        lines += ["", "## 依赖清单", "",
                  "| 文件 | 内容 |", "| --- | --- |"]
        for r in reqs:
            content = "；".join(x.strip() for x in _read(r).splitlines() if x.strip())
            lines.append(f"| `{r.relative_to(repo.root).as_posix()}` | {content or '（空）'} |")
    return "\n".join(lines) + "\n"


def _faq_titles(repo: check.Repo) -> set[str]:
    """把所有参与 genre 骨架里 FAQ 类段的别名收集成标题集合。"""
    titles: set[str] = set()
    for doc in repo.cfg.get("genre_docs", []):
        for item in doc.get("skeleton", []) or []:
            if item.get("id") in FAQ_SKELETON_IDS:
                titles |= {check._norm(a) for a in (item.get("aliases") or [])}
    return titles


def _appendix_faq(repo: check.Repo, chapters: list[check.Chapter]) -> str:
    lines = ["# 附录 E 常见问题", ""]
    titles = _faq_titles(repo)
    any_pit = False
    for ch in chapters:
        for h2 in ch.h2:
            if check._norm(h2.title) in titles:
                body = "\n".join(h2.body).strip()
                if body:
                    any_pit = True
                    lines += [f"## Ch{ch.name[-2:]} · {h2.title.strip()}", "", body, ""]
    dropped = [p for p in repo.ledger.get("promises", []) if p.get("status") == "dropped"]
    if dropped:
        lines += ["## 书中未展开的承诺", ""]
        for p in dropped:
            lines.append(f"- {p.get('text', '')}（原因：{p.get('reason', '未写')}）")
    if not any_pit and not dropped:
        lines.append("（各章暂无 FAQ 类骨架段，承诺账本也没有 dropped 项）")
    return "\n".join(lines) + "\n"


def _afterword(repo: check.Repo) -> str:
    ladder = repo.ledger.get("ladder", [])
    lines = ["# 结语", ""]
    if ladder:
        last = ladder[-1]
        lines += ["读完这本书，你应该能做到：", ""]
        for x in last.get("after", []) or []:
            lines.append(f"- {x}")
    else:
        lines += ["<!-- TODO: 能力阶梯为空，结语需手工补；内容必须来自 ladder.jsonl 末章 after -->",
                  "（待补：读完这本书你能做到什么）"]
    lines += ["", "这本书到这里结束。剩下的，靠你动手。", ""]
    return "\n".join(lines)


def _license(repo: check.Repo) -> str:
    book = repo.book
    return (f"{book.get('title', '')}\n\n"
            f"Copyright (c) {date.today():%Y} {book.get('author', '')}\n\n"
            f"License: {book.get('license', '')}\n")


# ---------------------------------------------------------------- 装配

STDLIB = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()


def write_versions_lock(repo: check.Repo) -> None:
    """有示例代码却没有 versions.lock 时，按真实 import 生成一份。

    存在的 lock 不覆盖——那是作者的决定。没有 lock 时 C04 会静默跳过，
    「读者按书跑不起来」就没人负责，所以装配阶段补上。
    """
    lock = repo.root / "versions.lock"
    src = repo.root / "src"
    if repo.cfg["code_lang"] != "python":
        print(f"  ! 代码栈={repo.cfg['code_lang']}，versions.lock 生成已跳过"
              "（按 Python import 特化，见 C00 标注）")
        return
    if lock.exists() or not src.is_dir():
        return
    pkgs: set[str] = set()
    for py in src.rglob("*.py"):
        txt = py.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", txt, re.M):
            name = m.group(1)
            if name in STDLIB or name in ("common", "src"):
                continue
            if re.fullmatch(r"ch\d{2}", name):      # 包内互引，不是依赖
                continue
            pkgs.add(name)
    deps: dict[str, str] = {}
    for p in sorted(pkgs):
        try:
            import importlib.metadata as md
            deps[p] = md.version(p)
        except Exception:  # noqa: BLE001
            deps[p] = "未知（生成时未安装）"
    repos = sorted(src.rglob("requirements.txt"))
    for r in repos:
        for ln in _read(r).splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            name = re.split(r"[=<>!~ ]", ln, 1)[0].strip()
            if name and name not in deps:
                deps[name] = ln[len(name):].lstrip("=<>!~ ") or "未标版本"
    lock.write_text(
        yaml.safe_dump({
            "generated_by": "aia-handbook assemble.py",
            "generated_at": date.today().isoformat(),
            "note": "本书示例只依赖标准库；有第三方依赖时会锁主版本，C04 按主版本比对。"
                    if not deps else "生成自本项目 src/ 的实际 import，与实测环境一致。",
            "dependencies": deps,
        }, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"  已生成 versions.lock（{len(deps)} 个第三方依赖）")


def assemble(book_dir: Path) -> tuple[int, list[str]]:
    repo = check.load_repo(book_dir)
    # 评审 A1：open 承诺必须在装配器里真正阻断，不能只靠 check.py 的 X06。
    # 直接跑 assemble.py（不经 verify.py）时也要拦得住。
    opens = _open_promises(repo)
    if opens:
        ids = "、".join(str(p.get("id") or "?") for p in opens[:5])
        raise PromisesOpenError(
            f"promises.jsonl 仍有 {len(opens)} 条 status=open（{ids}）；"
            "结清或标记 dropped 并写 reason 后才能产出 final/")
    book = repo.book
    final = book_dir / book.get("paths", {}).get("final", "final")
    final.mkdir(parents=True, exist_ok=True)

    # 清理已知生成物（不动用户自建文件）
    for name in GEN_FILES:
        (final / name).unlink(missing_ok=True)
    for pat in ("ch*.md", "appendix-*.md"):
        for p in final.glob(pat):
            p.unlink()
    if (final / "assets").exists():
        shutil.rmtree(final / "assets")

    # 章节：去 front-matter + 重写图路径
    chapters: list[check.Chapter] = []
    ch_dir = book_dir / book.get("paths", {}).get("chapters", "chapters")
    for f in sorted(ch_dir.glob("ch*.md")):
        chapters.append(check.parse_chapter(f))
    for f, ch in zip(sorted(ch_dir.glob("ch*.md")), chapters):
        body = _rewrite_assets(_strip_fm(_read(f)))
        (final / f"{ch.name}.md").write_text(body, encoding="utf-8")

    # 资产：自包含复制
    assets = book_dir / book.get("paths", {}).get("assets", "assets")
    if assets.is_dir():
        shutil.copytree(assets, final / "assets", dirs_exist_ok=True)

    stats = _stats(chapters)
    paths = {c.name: _path_marks(c) for c in chapters}
    write_versions_lock(repo)

    (final / "README.md").write_text(_readme(repo, stats), encoding="utf-8")
    (final / "00-preface.md").write_text(_preface(repo, chapters, stats, paths), encoding="utf-8")
    (final / "appendix-a-glossary.md").write_text(_appendix_glossary(repo), encoding="utf-8")
    (final / "appendix-b-references.md").write_text(_appendix_refs(repo), encoding="utf-8")
    (final / "appendix-c-paths.md").write_text(_appendix_paths(repo, paths), encoding="utf-8")
    (final / "appendix-d-toolbox.md").write_text(_appendix_toolbox(repo), encoding="utf-8")
    (final / "appendix-e-faq.md").write_text(_appendix_faq(repo, chapters), encoding="utf-8")
    (final / "99-afterword.md").write_text(_afterword(repo), encoding="utf-8")
    (final / "LICENSE").write_text(_license(repo), encoding="utf-8")

    # 装配后校验：final/ 内图片路径可达、无残留 ../
    problems: list[str] = []
    for md in sorted(final.glob("*.md")):
        txt = _read(md)
        for m in IMG.finditer(txt):
            p = m.group(1)
            if p.startswith(("http://", "https://")):
                continue
            if p.startswith("../"):
                problems.append(f"{md.name}: 仍引用 ../ → {p}")
            elif not (final / p).exists():
                problems.append(f"{md.name}: 图不存在 → {p}")
        if "<!-- TODO:" in txt:
            problems.append(f"{md.name}: 有未完成的 TODO 占位")
        # 「留占位」不止英文 TODO：装配自己生成的中文占位也一样不能放过
        for kw in PLACEHOLDER_WORDS:
            if kw in txt:
                problems.append(f"{md.name}: 残留占位「{kw}」")
                break

    return stats, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="装配 final/（自包含）")
    ap.add_argument("--book", required=True)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = Path(args.book).resolve()
    if not (root / "book.yaml").exists():
        sys.exit(f"找不到 {root / 'book.yaml'}")

    try:
        stats, problems = assemble(root)
    except PromisesOpenError as e:
        print(f"✗ 装配被阻断：{e}", file=sys.stderr)
        print("  → 修复承诺后重跑；verify.py 会在 check 阶段先报 X06。", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"装配完成 {root / 'final'}")
        print(f"  {stats['chapters']} 章 · {stats['words']:,} 字 · "
              f"{stats['figures']} 图 · {stats['code_blocks']} 段代码")
        print(f"  assets 已复制（自包含），图路径已重写为 assets/...")
        print("  产物：README / 00-preface / chNN / appendix-a~e / 99-afterword / LICENSE")

    if problems:
        print()
        print(f"✗ 装配校验 {len(problems)} 处问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print()
    print("✓ final/ 内相对路径全部可达")
    return 0


if __name__ == "__main__":
    sys.exit(main())
