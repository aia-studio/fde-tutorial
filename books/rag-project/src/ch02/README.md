# ch02 数据接入与清洗

四个脚本按顺序跑，覆盖盘点、接入、映射、验收四步。只依赖 Python 标准库。

```bash
cd books/rag-project
python src/ch02/source.py
python src/ch02/db.py
python src/ch02/mapping.py
python src/ch02/check.py
```

`db.py` 会在系统临时目录造一份 sqlite 离线快照，模拟客户导出。接生产时只改一个环境变量：

```bash
TICKET_DSN=/data/replica/tickets.sqlite python src/ch02/check.py
```

## 实测输出

### source.py

```
数据源盘点
数据源    类型        责任方        接入方式  敏感字段              结论
工单主表  PostgreSQL  客服系统厂商  只读从库  客户手机号、客户地址  可接
工单回复  PostgreSQL  客服系统厂商  只读从库  坐席工号              可接
产品手册  共享网盘    产品部        人工导出  无                    可接
历史邮件  对象存储    客服主管      未授权    客户邮箱              暂缓

可接 3 个，暂缓 1 个
  暂缓 历史邮件：无书面授权，需 客服主管 出具书面授权

敏感字段清单
  工单主表: 客户手机号、客户地址
  工单回复: 坐席工号
  历史邮件: 客户邮箱
```

### db.py

```
TICKET_DSN = C:\Users\Hex\AppData\Local\Temp\huayang_tickets_demo.sqlite
   HY-1001 | 设备无法开机 | 宁波华远机械 | 已解决
   HY-1002 | 主轴异响 | 苏州恒达精工 | 已解决
   HY-1003 | 报错 E-204 | 无锡新材 | 已解决
写操作被拒绝：attempt to write a readonly database
总数校验：12 条
```

### mapping.py

```
字段映射表
源字段      目标字段        规则
ticket_no   doc_id          去空格并转大写，作为唯一键
title       title           去 HTML 标签，压缩空白
body        content         去 HTML 标签，手机号脱敏
customer    customer_alias  截取城市加客户简称，去掉全称
created_at  created_at      统一为 ISO 8601，保留到秒
status      status          收敛到已解决 / 处理中 / 已关闭

清洗前： {'ticket_no': ' hy-1001 ', 'title': '设备<em>无法</em>开机', 'body': '<p>通电后指示灯不亮。客户电话 13800001111。</p>', 'customer': '宁波华远机械有限公司', 'created_at': '2026/03/02 09:14', 'status': '已解决'}
清洗后： {'doc_id': 'HY-1001', 'title': '设备无法开机', 'content': '通电后指示灯不亮。客户电话 138****1111。', 'customer_alias': '宁波-华远', 'created_at': '2026-03-02 09:14', 'status': '已解决'}

覆盖检查：6 个源字段全部有映射，未映射 0 个
```

### check.py

```
数据质量验收：抽样 10 条，固定取单号最小的十条
  HY-1001  汉字  20  宁波-华远     一致
  HY-1002  汉字  19  苏州-恒达     一致
  HY-1003  汉字  15  无锡-新材     一致
  HY-1004  汉字  18  宁波-华远     一致
  HY-1005  汉字  19  常州-瑞信     一致
  HY-1006  汉字  17  苏州-恒达     一致
  HY-1007  汉字  17  杭州-立成     一致
  HY-1008  汉字  15  无锡-新材     一致
  HY-1009  汉字  14  常州-瑞信     一致
  HY-1010  汉字  16  杭州-立成     一致

差异合计 0 处，结论：通过
全量 12 条：空正文 0 条，重复单号 0 条
```

`check.py` 的比对不复用 `mapping.py` 的结果：它把源正文去掉标签后的汉字序列与清洗后的汉字序列逐字比对，再单独查标签残留、手机号残留、时间格式。复用同一个函数比对等于自己验自己。

## 文件职责

| 文件 | 职责 | 关键点 |
| --- | --- | --- |
| `source.py` | 数据源盘点 | 先列敏感字段与授权状态，再谈对接 |
| `db.py` | 只读从库接入 | URI `mode=ro` 加 `pragma query_only`，双保险 |
| `mapping.py` | 字段映射与清洗 | 映射表是数据，不是注释；未登记字段直接抛错 |
| `check.py` | 数据质量验收 | 抽样十条零差异，差异要能逐条说清 |
