#!/usr/bin/env python3
"""schema_check.py —— 把 schemas/*.json 接进流水线。

背景：`state.json` / `dag.json` / `contracts/*.json` 三份契约一直存在，
但没有任何脚本校验过。契约无人执行，等于没有契约。

用法（也被 state.py / plan.py / check.py 内部调用）：
    python scripts/schema_check.py --kind contract --file .book/contracts/ch01.json
    python scripts/schema_check.py --kind state --file .book/state.json

设计：jsonschema 缺失时降级为一条 info，不阻断——校验缺席要明说，不能假装通过。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_DIR = HERE.parent / "schemas"
GENRE_DIR = HERE.parent / "genres"

KIND_FILE = {
    "book": "book.schema.json",
    "state": "state.schema.json",
    "dag": "dag.schema.json",
    "contract": "contract.schema.json",
}

_CACHE: dict[str, dict] = {}


def available_genres() -> set[str]:
    """评审 C4：可用 genre 从 genres/*.yaml 自动发现，不再在 schema 里硬编码四种。

    排除 `_core.yaml`（宪法核心层）与 `presets.yaml`（预设组合，不是体裁）。
    """
    if not GENRE_DIR.is_dir():
        return set()
    return {p.stem for p in GENRE_DIR.glob("*.yaml")
            if p.stem not in {"_core", "presets"}}


def load_schema(kind: str) -> dict | None:
    if kind in _CACHE:
        return _CACHE[kind]
    path = SCHEMA_DIR / KIND_FILE.get(kind, "")
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    _CACHE[kind] = data
    return data


def validate(kind: str, payload: dict) -> tuple[list[str], str]:
    """返回 (问题列表, 状态)。状态为 ok / unavailable / no-schema。

    genre 的可用值不写死在 JSON Schema 里（静态文件无法自动发现目录），
    这里做一次动态补充校验；校验缺席时显式返回 unavailable。
    """
    problems: list[str] = []
    if kind == "book":
        genres = payload.get("genre") or []
        if isinstance(genres, str):
            genres = [genres]
        known = available_genres()
        if known:
            unknown = [g for g in genres if g not in known]
            if unknown:
                problems.append(f"genre: 找不到 {'、'.join(unknown)} 对应的 "
                                f"genres/<name>.yaml（可用：{'、'.join(sorted(known))}）")
    schema = load_schema(kind)
    if schema is None:
        return problems, "no-schema"
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        return problems, "unavailable"
    v = Draft7Validator(schema)
    for err in sorted(v.iter_errors(payload), key=lambda e: list(e.path)):
        where = "/".join(str(x) for x in err.path) or "<root>"
        problems.append(f"{where}: {err.message}")
    return problems, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="按 schemas/*.json 校验一个 JSON 文件")
    ap.add_argument("--kind", required=True, choices=sorted(KIND_FILE))
    ap.add_argument("--file", required=True)
    args = ap.parse_args()

    p = Path(args.file)
    if not p.exists():
        sys.exit(f"找不到 {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        # book.yaml 是 YAML，不是 JSON；此前 --kind book --file book.yaml 会直接崩
        try:
            import yaml
        except ImportError:
            sys.exit("需要 pyyaml：python -m pip install pyyaml")
        payload = yaml.safe_load(text) or {}
    else:
        payload = json.loads(text)
    problems, status = validate(args.kind, payload)

    if status == "unavailable":
        print("! 未安装 jsonschema，仅做了 genre 自动发现校验（pip install jsonschema）")
    if status == "no-schema":
        print(f"! 没有 {args.kind} 的 schema，跳过")
    if problems:
        print(f"✗ {args.kind} 校验失败 {len(problems)} 处：")
        for x in problems:
            print(f"  - {x}")
        return 1
    if status != "ok":
        return 0
    print(f"✓ {args.kind} 符合契约")
    return 0


if __name__ == "__main__":
    sys.exit(main())
