"""课程元数据与结构校验。

front matter 用 TOML（标准库 tomllib 直接解析，不手写 YAML）。
"""

from __future__ import annotations

import re
from pathlib import Path

STAGES: tuple[str, ...] = ("s0", "s1", "s2", "s3", "s4", "s5")

STAGE_META: dict[str, dict[str, str]] = {
    "s0": {"title": "起步", "subtitle": "能跑、能查、能算、能存"},
    "s1": {"title": "组织", "subtitle": "函数、模块、文件、异常、测试"},
    "s2": {"title": "抽象", "subtitle": "类、协议、装饰器、生成器、注解"},
    "s3": {"title": "工程", "subtitle": "日志、打包、类型检查、并发"},
    "s4": {"title": "深入", "subtitle": "对象模型、描述符、元类、GC、字节码"},
    "s5": {"title": "参考", "subtitle": "术语表、PEP、FAQ、Zen、路线图"},
}

OFFICIAL_GROUPS: tuple[str, ...] = (
    "beginner",
    "moderate",
    "advanced",
    "general",
    "resources",
)

OFFICIAL_GROUP_LABELS: dict[str, str] = {
    "beginner": "Beginner",
    "moderate": "Moderate",
    "advanced": "Advanced",
    "general": "General",
    "resources": "Python 3.x Resources",
}

#: 大纲里规划的总课数。`build.py --strict` 用它判断是否还有缺口。
PLANNED_TOTAL = 103

REQUIRED_META = ("id", "order", "stage", "official_group", "title", "concepts", "doc_refs")

_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: 允许出现的块类型，`build.py` 会拒绝未知类型，避免渲染器悄悄吞掉内容。
BLOCK_TYPES = frozenset(
    {
        "heading",
        "p",
        "list",
        "code",
        "output",
        "callout",
        "quiz",
        "exercise",
        "step",
        "glossary",
        "table",
        "hr",
    }
)

CALLOUT_KINDS = frozenset({"note", "tip", "warn", "danger", "why"})


def split_front_matter(text: str) -> tuple[str, str]:
    """把 `+++ ... +++` 切成 (front matter 文本, 正文)。

    正文缺失或分隔符不完整时抛 ValueError —— 宁可构建失败，也不要静默丢内容。
    """
    if not text.startswith("+++"):
        raise ValueError("文件必须以 `+++` 开头（TOML front matter）")
    parts = text.split("+++", 2)
    if len(parts) < 3:
        raise ValueError("front matter 未闭合，缺少第二个 `+++`")
    return parts[1], parts[2].lstrip("\n")


def validate_meta(meta: dict, *, source: str) -> list[str]:
    """校验单课元数据，返回错误列表（空列表表示通过）。"""
    errors: list[str] = []

    for key in REQUIRED_META:
        if key not in meta:
            errors.append(f"{source}: 缺少必填字段 `{key}`")

    lesson_id = meta.get("id")
    if isinstance(lesson_id, str):
        if not _ID_RE.match(lesson_id):
            errors.append(f"{source}: id `{lesson_id}` 只允许小写字母、数字和连字符")
    elif lesson_id is not None:
        errors.append(f"{source}: id 必须是字符串")

    order = meta.get("order")
    if not isinstance(order, int) or isinstance(order, bool):
        errors.append(f"{source}: order 必须是整数")
    elif not 1 <= order <= PLANNED_TOTAL:
        errors.append(f"{source}: order={order} 超出 1..{PLANNED_TOTAL}")

    stage = meta.get("stage")
    if stage not in STAGES:
        errors.append(f"{source}: stage `{stage}` 不在 {STAGES} 里")

    group = meta.get("official_group")
    if group not in OFFICIAL_GROUPS:
        errors.append(f"{source}: official_group `{group}` 不在 {OFFICIAL_GROUPS} 里")

    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{source}: title 不能为空")

    concepts = meta.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        errors.append(f"{source}: concepts 必须是非空数组")
    elif not all(isinstance(c, str) and c.strip() for c in concepts):
        errors.append(f"{source}: concepts 里每一项都必须是非空字符串")

    refs = meta.get("doc_refs")
    if not isinstance(refs, list) or not refs:
        errors.append(f"{source}: doc_refs 必须是非空数组")
    else:
        for i, ref in enumerate(refs):
            if not isinstance(ref, dict):
                errors.append(f"{source}: doc_refs[{i}] 必须是表")
                continue
            for key in ("title", "url"):
                if not isinstance(ref.get(key), str) or not ref[key].strip():
                    errors.append(f"{source}: doc_refs[{i}].{key} 不能为空")
            url = ref.get("url", "")
            if isinstance(url, str) and url and not url.startswith("https://"):
                errors.append(f"{source}: doc_refs[{i}].url 必须是 https:// 开头")

    prereq = meta.get("prereq", [])
    if not isinstance(prereq, list) or not all(isinstance(p, int) for p in prereq):
        errors.append(f"{source}: prereq 必须是整数数组（课程编号）")

    return errors


def check_progression(lessons: list[dict]) -> list[str]:
    """难度曲线校验：前置必须严格早于本课，跨阶段只能指向更早阶段。

    这是把「渐进式」变成可执行约束的地方，不靠人工 review。
    """
    errors: list[str] = []
    by_order = {l["order"]: l for l in lessons}

    for lesson in lessons:
        stage_idx = STAGES.index(lesson["stage"])
        for p in lesson.get("prereq", []):
            if p == lesson["order"]:
                errors.append(f"第 {lesson['order']} 课：不能把自己列为前置")
                continue
            target = by_order.get(p)
            if target is None:
                errors.append(f"第 {lesson['order']} 课：前置 {p} 不存在于当前内容集")
                continue
            if p > lesson["order"]:
                errors.append(
                    f"第 {lesson['order']} 课：前置 {p} 编号更大，违反单调性"
                )
            elif STAGES.index(target["stage"]) > stage_idx:
                errors.append(
                    f"第 {lesson['order']} 课：前置 {p} 属于更晚的阶段 {target['stage']}"
                )

    # 孤岛课：除第 1 课外，必须至少有一个前置，或显式 standalone
    for lesson in lessons:
        if lesson["order"] == 1:
            continue
        if not lesson.get("prereq") and not lesson.get("standalone", False):
            errors.append(
                f"第 {lesson['order']} 课：没有任何前置，也没有 standalone 标记"
            )

    return errors


def scan_content(content_dir: Path) -> list[Path]:
    return sorted(p for p in content_dir.rglob("*.md") if p.is_file())
