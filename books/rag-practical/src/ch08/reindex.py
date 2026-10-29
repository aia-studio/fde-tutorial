"""Ch08 索引重建：先算变更集，再决定全量还是增量，切换要原子。

重建的风险不在算得慢，在于重建期间线上查的是半成品。
这节的做法是先在一份副本上建，校验通过再换文件名，换名是一次原子操作。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

from common.paths import DATA_DIR, INDEX_DB

OPS_DIR = DATA_DIR / "ops"
CHANGES = OPS_DIR / "corpus_change.jsonl"
STAGING = OPS_DIR / "index.staging.db"
CURRENT = OPS_DIR / "index.current.db"


def snapshot(db_path: str | Path = INDEX_DB) -> dict[str, str]:
    """工单号 → 该工单全部块文本的指纹。块没变就不必重新嵌入。"""
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT ticket_no, text FROM chunks ORDER BY ticket_no, seq").fetchall()
    conn.close()
    acc: dict[str, list[str]] = {}
    for ticket_no, text in rows:
        acc.setdefault(ticket_no, []).append(text)
    return {t: hashlib.sha1("".join(v).encode("utf-8")).hexdigest()[:12]
            for t, v in acc.items()}


def load_changes(path: Path = CHANGES) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def apply(old: dict[str, str], changes: list[dict]) -> dict[str, str]:
    """按变更单改动快照；新工单先给一个占位指纹，真实重建后才会有真值。"""
    new = dict(old)
    for c in changes:
        op, ticket = c["op"], c["ticket_no"]
        if op == "add":
            new[ticket] = f"new-{ticket}"
        elif op == "update":
            new[ticket] = f"upd-{hashlib.sha1(c.get('note', '').encode()).hexdigest()[:8]}"
        elif op == "remove":
            new.pop(ticket, None)
    return new


def diff(old: dict[str, str], new: dict[str, str]) -> dict[str, list[str]]:
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(t for t in set(old) & set(new) if old[t] != new[t])
    return {"added": added, "changed": changed, "removed": removed}


def chunk_estimate(db_path: str | Path, tickets: list[str]) -> int:
    """按这些工单现有块数的平均值估重建块数，用来对比全量与增量的代价。"""
    if not tickets:
        return 0
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        f"SELECT COUNT(*) FROM chunks WHERE ticket_no IN ({','.join('?' * len(tickets))})",
        tickets).fetchall()
    total = conn.execute("SELECT COUNT(*), COUNT(DISTINCT ticket_no) FROM chunks").fetchone()
    conn.close()
    hit = rows[0][0] or len(tickets)
    avg = total[0] / max(total[1], 1)
    return max(hit, round(avg * len(tickets)))


def validate(db_path: str | Path, min_chunks: int, dim: int) -> list[str]:
    """切换前的四项检查：块数、空文本、维度、样例查询有没有结果。"""
    problems: list[str] = []
    conn = sqlite3.connect(str(db_path))
    chunks, tickets = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT ticket_no) FROM chunks").fetchone()
    empty = conn.execute("SELECT COUNT(*) FROM chunks WHERE length(trim(text)) = 0").fetchone()[0]
    dims = [r[0] for r in conn.execute("SELECT DISTINCT dim FROM chunks").fetchall()]
    sample = conn.execute(
        "SELECT COUNT(*) FROM chunks WHERE text LIKE '%保修%'").fetchone()[0]
    conn.close()
    if chunks < min_chunks:
        problems.append(f"块数 {chunks} 少于基线 {min_chunks}")
    if empty:
        problems.append(f"有 {empty} 块正文为空")
    if dims != [dim]:
        problems.append(f"向量维度不唯一：{dims}")
    if not sample:
        problems.append("样例查询没有命中，索引可能没写完")
    return problems


def swap(staging: str | Path, target: str | Path) -> float:
    """把暂存库换到线上名。同一分区上 rename 是原子的，读到的要么旧要么新。"""
    t0 = time.perf_counter()
    os.replace(str(staging), str(target))
    return (time.perf_counter() - t0) * 1000


def main() -> None:
    if not CURRENT.exists():
        shutil.copyfile(INDEX_DB, CURRENT)
    old = snapshot(CURRENT)
    conn = sqlite3.connect(str(CURRENT))
    dim = conn.execute("SELECT value FROM meta WHERE key='dim'").fetchone()
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    conn.close()
    dim = int(dim[0]) if dim else 256

    changes = load_changes()
    new = apply(old, changes)
    d = diff(old, new)
    print(f"工单快照：{len(old)} 条，变更后 {len(new)} 条")
    print(f"变更集：新增 {len(d['added'])}　修改 {len(d['changed'])}　下线 {len(d['removed'])}")
    for op, key in (("新增", "added"), ("修改", "changed"), ("下线", "removed")):
        for t in d[key]:
            print(f"  {op} {t}")

    touched = d["added"] + d["changed"]
    inc = chunk_estimate(CURRENT, touched)
    print()
    print(f"全量：{len(new)} 条工单、{total} 块，全部重新嵌入")
    print(f"增量：{len(touched)} 条工单、约 {inc} 块，其余复用旧向量")

    shutil.copyfile(CURRENT, STAGING)
    problems = validate(STAGING, total, dim)
    print()
    if problems:
        print("暂存库校验失败，不切换：")
        for p in problems:
            print(f"  ✗ {p}")
        STAGING.unlink(missing_ok=True)
        return
    print(f"暂存库 {STAGING.name}：块数、空文本、维度、样例查询四项通过")
    cost = swap(STAGING, CURRENT)
    print(f"切换：{CURRENT.name} 已换名，用时 {cost:.2f} ms，暂存库残留 {STAGING.exists()}")


if __name__ == "__main__":
    main()
