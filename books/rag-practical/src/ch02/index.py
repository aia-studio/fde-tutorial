"""Ch02 索引：SQLite 存块、元数据与向量，按工单增量更新。"""

from __future__ import annotations

import sqlite3
from array import array

from ch02.chunk import build_chunks, load_rows
from ch02.embed import DEFAULT_DIM, embed_one
from common.paths import INDEX_DB, TICKETS_CSV

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   TEXT PRIMARY KEY,
    ticket_no  TEXT NOT NULL,
    product    TEXT,
    category   TEXT,
    created_at TEXT,
    seq        INTEGER,
    text       TEXT NOT NULL,
    dim        INTEGER NOT NULL,
    vector     BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_ticket ON chunks(ticket_no);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('dim', ?)", (str(DEFAULT_DIM),))
    return conn


def _pack(vec: list[float]) -> bytes:
    return array("f", vec).tobytes()


def _insert(conn: sqlite3.Connection, chunk: dict) -> None:
    vec = embed_one(chunk["text"])
    conn.execute(
        "INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?,?)",
        (chunk["chunk_id"], chunk["ticket_no"], chunk["product"], chunk["category"],
         chunk["created_at"], chunk["seq"], chunk["text"], len(vec), _pack(vec)),
    )


def build(csv_path: str = str(TICKETS_CSV), db_path: str = str(INDEX_DB)) -> dict:
    """全量重建索引：先删库，再按工单逐条写入。"""
    from pathlib import Path

    Path(db_path).unlink(missing_ok=True)
    rows = load_rows(csv_path)
    chunks = build_chunks(rows)
    conn = connect(db_path)
    with conn:
        for chunk in chunks:
            _insert(conn, chunk)
    conn.close()
    return {"tickets": len(rows), "chunks": len(chunks)}


def replace_ticket(ticket_no: str, description: str, resolution: str,
                   db_path: str = str(INDEX_DB)) -> dict:
    """改一条工单：先删它全部的块，再按新内容重建，别的工单不动。"""
    conn = connect(db_path)
    old = conn.execute("SELECT product, category, created_at FROM chunks WHERE ticket_no=?",
                       (ticket_no,)).fetchone()
    if old is None:
        conn.close()
        return {"error": f"索引里没有 {ticket_no}"}
    row = {"ticket_no": ticket_no, "product": old[0], "category": old[1],
           "created_at": old[2], "description": description, "resolution": resolution}
    new_chunks = build_chunks([row])
    with conn:
        conn.execute("DELETE FROM chunks WHERE ticket_no=?", (ticket_no,))
        for chunk in new_chunks:
            _insert(conn, chunk)
    conn.close()
    return {"ticket_no": ticket_no, "chunks": len(new_chunks)}


def stats(db_path: str = str(INDEX_DB)) -> dict:
    conn = connect(db_path)
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    tickets = conn.execute("SELECT COUNT(DISTINCT ticket_no) FROM chunks").fetchone()[0]
    dim = conn.execute("SELECT value FROM meta WHERE key='dim'").fetchone()
    conn.close()
    return {"chunks": chunks, "tickets": tickets, "dim": int(dim[0]) if dim else 0}


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "build"
    if cmd == "build":
        print("重建索引：", build())
        print("索引状态：", stats())
    elif cmd == "stat":
        print("索引状态：", stats())
    elif cmd == "update":
        if len(args) < 4:
            raise SystemExit("用法：python -m ch02.index update <工单号> <现象> <处理>")
        print("更新前：", stats())
        print("更新结果：", replace_ticket(args[1], args[2], args[3]))
        print("更新后：", stats())
    else:
        raise SystemExit(f"未知子命令 {cmd}，可用 build / stat / update")


if __name__ == "__main__":
    main()
