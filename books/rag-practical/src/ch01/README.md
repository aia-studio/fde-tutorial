# ch01 最小链路

运行：

```bash
cd src
python -m ch01.demo
```

实测输出（2026-10-30，Python 3.13）：

```text
q=显示器黑屏 source=T-1001 answer=显示器无法开机，电源灯不亮
q=A100 保修 source=T-1002 answer=A100 显卡保修需要提供购买凭证
q=键盘失灵 source=- answer=-
```

第三条查不到时返回空，这是预期行为，不是故障。
