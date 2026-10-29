"""进度存储：一份 JSON，原子写入，写之前先备份上一版。

单用户本地应用，不做增量合并——客户端提交完整文档，服务端只负责校验与落盘。
这样客户端逻辑简单，也不会出现"两次写入互相覆盖"的中间态。
"""

from __future__ import annotations

import json
import os
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
MAX_BYTES = 1024 * 1024
MAX_XP = 1_000_000


def _default() -> dict:
    return {
        "schema": SCHEMA_VERSION,
        "updated_at": None,
        "xp": 0,
        "streak": {"current": 0, "best": 0, "last_day": None},
        "lessons": {},
        "exercises": {},
        "quizzes": {},
        "weak": {},
    }


def _as_int(value, *, minimum: int = 0, maximum: int = MAX_XP) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("必须是整数")
    if not minimum <= value <= maximum:
        raise ValueError(f"必须在 {minimum}..{maximum} 之间")
    return value


def validate(payload: object) -> dict:
    """把客户端提交的文档收敛成可信结构；字段不认识就丢掉，避免无限膨胀。"""
    if not isinstance(payload, dict):
        raise ValueError("进度必须是 JSON 对象")

    data = _default()

    if "schema" in payload and payload["schema"] != SCHEMA_VERSION:
        raise ValueError(f"schema 版本不支持：{payload['schema']}")
    data["schema"] = SCHEMA_VERSION

    if "xp" in payload:
        data["xp"] = _as_int(payload["xp"])

    streak = payload.get("streak")
    if isinstance(streak, dict):
        data["streak"] = {
            "current": _as_int(streak.get("current", 0), maximum=100_000),
            "best": _as_int(streak.get("best", 0), maximum=100_000),
            "last_day": streak.get("last_day")
            if isinstance(streak.get("last_day"), str)
            else None,
        }

    for key in ("lessons", "exercises", "quizzes"):
        value = payload.get(key)
        if not isinstance(value, dict):
            continue
        clean = {}
        for name, entry in list(value.items())[:2000]:
            if not isinstance(name, str) or not isinstance(entry, dict):
                continue
            clean[name] = {
                k: v
                for k, v in entry.items()
                if isinstance(k, str) and isinstance(v, (str, int, bool, list))
            }
        data[key] = clean

    weak = payload.get("weak")
    if isinstance(weak, dict):
        data["weak"] = {
            str(k): _as_int(v, maximum=10_000)
            for k, v in list(weak.items())[:2000]
            if isinstance(v, int) and not isinstance(v, bool)
        }

    data["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return data


class ProgressStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.backup = self.path.with_suffix(".json.bak")
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        with self._lock:
            if not self.path.exists():
                return _default()
            try:
                raw = self.path.read_text(encoding="utf-8")
                payload = json.loads(raw)
            except (OSError, json.JSONDecodeError):
                # 文件损坏时退回默认值，但不要覆盖它——留给用户自己查看
                return _default()
            try:
                return validate(payload)
            except ValueError:
                return _default()

    def save(self, payload: object) -> dict:
        data = validate(payload)
        body = json.dumps(data, ensure_ascii=False, indent=2)
        if len(body.encode("utf-8")) > MAX_BYTES:
            raise ValueError("进度数据过大")

        with self._lock:
            if self.path.exists():
                try:
                    shutil.copyfile(self.path, self.backup)
                except OSError:
                    pass

            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(body, encoding="utf-8", newline="\n")
            os.replace(tmp, self.path)

        return data
