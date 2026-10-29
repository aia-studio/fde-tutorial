"""全书共用的路径常量：数据目录与索引文件的位置只在这里定义一次。"""

from pathlib import Path

BOOK_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BOOK_ROOT / "data"
TICKETS_CSV = DATA_DIR / "tickets.csv"
INDEX_DB = DATA_DIR / "index.db"
EVAL_SET = DATA_DIR / "eval" / "questions.jsonl"
