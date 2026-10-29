# 附录 A 术语表

| id | 中文 | English | 定义 | 首现章 |
| --- | --- | --- | --- | --- |
| C001 | 检索增强生成 | Retrieval-Augmented Generation | 先检索资料，再让模型基于资料回答 | ch01 |
| C002 | 切分 | Chunking | 把长文档切成可检索的小块 | ch02 |
| C003 | 嵌入 | Embedding | 把文本压成固定维度的语义向量 | ch02 |
| C004 | 召回 | Recall | 正确内容是否出现在候选集里 | ch03 |
| C005 | 引用 | Citation | 答案里指向原文片段的标注 | ch04 |
| C006 | 拒答 | Abstention | 证据不足时明确说答不了 | ch04 |
| C007 | 混合检索 | Hybrid Retrieval | 同时用向量与关键词两路检索 | ch05 |
| C008 | 重排 | Rerank | 对候选集再排一次序 | ch05 |
| C009 | 评测集 | Evaluation Set | 固定的一组问题与期望答案 | ch06 |
| C010 | Top-K | Top-K | 按相似度取前 K 个候选 | ch03 |
| C011 | 元数据过滤 | Metadata Filter | 按字段先筛掉不该出现的文档 | ch03 |
| C012 | 幻觉 | Hallucination | 模型生成没有依据的内容 | ch04 |
| C013 | 会话状态 | Conversation State | 多轮对话里保留的少量实体与上一轮结果，不含全部原文 | ch07 |
| C014 | 指代消解 | Coreference Resolution | 把「它」「那换屏呢」还原成带具体对象的完整问句 | ch07 |
| C015 | 灰度发布 | Canary Release | 新版本先接一小部分会话，拿指标对比过再全量 | ch08 |
