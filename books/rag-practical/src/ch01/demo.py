"""最小的端到端演示：问题进，答案出。"""

from ch01.answer import answer

ROWS = [
    {"ticket_no": "T-1001", "description": "显示器无法开机，电源灯不亮"},
    {"ticket_no": "T-1002", "description": "A100 显卡保修需要提供购买凭证"},
    {"ticket_no": "T-1003", "description": "打印机卡纸，取出后仍提示缺纸"},
]


def main() -> None:
    for q in ("显示器黑屏", "A100 保修", "键盘失灵"):
        r = answer(q, ROWS)
        print(f"q={q} source={r['source'] or '-'} answer={r['answer'] or '-'}")


if __name__ == "__main__":
    main()
