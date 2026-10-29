# 附录 D 工具箱

| 类别 | 选型 | 用途 |
| --- | --- | --- |
| python | 3.12 | 运行全书示例 |
| llm | OpenAI 兼容接口 + Ollama 本地兜底 | 生成答案；Mock 模式可离线替代 |
| mock | True | 没有 API Key 时仍能跑通示例 |
| vector_store | SQLite + numpy 暴力检索（先跑通再选型） | 存向量与元数据，做暴力检索 |
| framework | FastAPI + Pydantic | 对外提供 HTTP 接口 |
