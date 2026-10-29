"""只读从库接入：一份代码，靠环境变量换库。

演示用 sqlite 造一份离线快照，生产把 TICKET_DSN 指向只读从库即可。

运行：python src/ch02/db.py
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

DDL = """
create table tickets (
    ticket_no  text primary key,
    title      text not null,
    body       text not null,
    customer   text not null,
    created_at text not null,
    status     text not null
)
"""

DEMO_ROWS: list[tuple[str, str, str, str, str, str]] = [
    ("HY-1001", "设备无法开机", "<p>通电后指示灯不亮，已排除电源线松动。客户电话 13800001111。</p>", "宁波华远机械", "2026-03-02 09:14:00", "已解决"),
    ("HY-1002", "主轴异响", "运行半小时后出现周期性异响，怀疑轴承缺油。", "苏州恒达精工", "2026-03-02 10:02:00", "已解决"),
    ("HY-1003", "报错 E-204", "面板显示 E-204，手册第 3 章写的是过热保护。", "无锡新材", "2026-03-03 08:41:00", "已解决"),
    ("HY-1004", "换刀卡顿", "换刀动作在第二把刀时停顿两秒，之后恢复。", "宁波华远机械", "2026-03-03 13:20:00", "处理中"),
    ("HY-1005", "精度漂移", "连续加工八小时后尺寸偏大，重新对刀后正常。", "常州瑞信", "2026-03-04 09:05:00", "已解决"),
    ("HY-1006", "远程连不上", "客户内网限制 443 端口，远程诊断工具连不上。", "苏州恒达精工", "2026-03-04 14:33:00", "处理中"),
    ("HY-1007", "冷却液报警", "液位正常但持续报警，怀疑浮子开关卡住。", "杭州立成", "2026-03-05 09:47:00", "已解决"),
    ("HY-1008", "系统升级失败", "升级包校验不通过，回滚后恢复正常。", "无锡新材", "2026-03-05 16:12:00", "已解决"),
    ("HY-1009", "夹具夹不紧", "气路压力不足，调压后夹紧力恢复。", "常州瑞信", "2026-03-06 08:58:00", "已解决"),
    ("HY-1010", "触摸屏失灵", "右下角区域点击无响应，重启后仍存在。", "杭州立成", "2026-03-06 11:26:00", "处理中"),
    ("HY-1011", "刀具寿命提示", "刀具寿命提前报警，实际加工件数未到设定值。", "宁波华远机械", "2026-03-07 10:03:00", "已解决"),
    ("HY-1012", "数据导出为空", "导出报表只有表头，明细为空，客户电话 13900002222。", "苏州恒达精工", "2026-03-07 15:39:00", "已解决"),
]


def build_demo(path: Path) -> Path:
    """造一份离线快照，模拟客户从库的一份导出。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.execute(DDL)
        conn.executemany("insert into tickets values (?,?,?,?,?,?)", DEMO_ROWS)
    return path


def resolve_dsn(default: str) -> str:
    """线上只改环境变量，不改代码。"""
    return os.environ.get("TICKET_DSN", default)


def connect_readonly(dsn: str) -> sqlite3.Connection:
    """以 URI 只读模式打开，再叠一层 query_only。"""
    uri = f"file:{Path(dsn).as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("pragma query_only = on")
    return conn


def fetch(conn: sqlite3.Connection, limit: int = 3) -> list[tuple]:
    sql = "select ticket_no, title, customer, status from tickets order by ticket_no limit ?"
    return conn.execute(sql, (limit,)).fetchall()


def main() -> None:
    demo = Path(tempfile.gettempdir()) / "huayang_tickets_demo.sqlite"
    build_demo(demo)
    dsn = resolve_dsn(str(demo))
    print(f"TICKET_DSN = {dsn}")

    conn = connect_readonly(dsn)
    rows = fetch(conn, 3)
    for row in rows:
        print("  ", " | ".join(row))

    try:
        conn.execute("delete from tickets where ticket_no = 'HY-1001'")
    except sqlite3.OperationalError as exc:
        print(f"写操作被拒绝：{exc}")
    finally:
        print(f"总数校验：{conn.execute('select count(*) from tickets').fetchone()[0]} 条")
        conn.close()


if __name__ == "__main__":
    main()
